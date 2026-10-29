"""Assemble an experiment's results.json from official verifier outputs, driven by a JSON config.

Usage (repo root):
    .venv/Scripts/python.exe -I -B src/tools/make_results.py <config.json> [--commit HASH] [--out PATH] [--check]

  --commit   value of "commit" (default: the config's "commit", else "pending")
  --out      write here instead of the config's "output" (default: results.json next to the config)
  --check    write nothing; compare with the existing output (or --out) as JSON (values and key order) and as
             bytes (working tree, CRLF-normalised, and the git HEAD blob); exit 1 if the JSON differs

Every number is copied from a file (verifier JSON, kernel run records, analysis JSON). The only derived
values are means/ranges over runs, improvement_factor = baseline cost / cost, score_delta_factor =
improvement_factor ** (1/3), and whatever the config's "$expr" fields compute explicitly.

Config keys (paths are relative to the repo root unless absolute):
  exp, task                 required. task in invsqrt | dqi | dfthcsos | all
  commit, output, indent    optional (indent default 1; output is written as UTF-8 with LF line ends)
  verifier                  optional; default from the task of the runs
  runs                      list of verifier runs, each
                              {"label": str, "salt": str|null, "seed": int (optional), "task": (default: config task),
                               "output": <ref to the verifier JSON>, "meta": <ref or object with cmd/cwd/wall_s/memory>}
                            "output" files may be pure JSON or text with the JSON starting at the first "{"
                            (the stdout capture of a verifier). [] for diagnostic experiments without a verifier.
  circuit_path              required (string or null): where the verified circuit is
  circuit_sha256            optional value/directive; default the verifier-reported hash (circuit_sha256, or
                            submission_sha256 for dfthcsos), which must agree across runs
  baseline                  {"exp", "cost", ...}; for runs spanning several tasks, {task: {"exp", "cost"}}
  metrics_fields            extra or overriding metrics (values or directives)
  metrics_keys              optional exact list (and order) of metrics keys; omitting a key the protocol requires
                            prints a warning
  run_fields                extra per-run fields; "$expr" sees the run as `run`
  run_meta_keys             meta keys copied into each run (default wall_s and the memory peaks present)
  fields                    extra top-level fields, evaluated in order (values or directives)
  key_order                 optional exact top-level key order (every key must be listed)

Directives (a JSON object whose first key starts with "$"; everything else is a literal):
  {"$ref": "path#ptr", "pick": [keys], "first": N, "default": X}   value from a file; ptr is a.b[0].c or
        list[key=value] (empty ptr = whole file); "default" is used only when the file does not exist
  {"$map": "path#ptr", "key": "label", "value": "wall_s"}  list of dicts -> {item[key]: item[value]};
        dict of dicts -> {k: v[value]}
  {"$expr": "python expression"}   restricted eval (no imports, no dunder access). Names: metrics, runs (label ->
        run summary), run (in run_fields), baseline, passed, cost, fields (fields so far), ref("path#ptr"),
        math, and abs/min/max/all/any/sum/len/round/sorted/list/dict/float/int/str/bool/range/zip/enumerate
  {"$when": "path", "value": <template>, "else": X}   evaluate value only if path exists
  {"$sha256": "path"}   SHA-256 of a local file
  {"$literal": X}       X unevaluated

Output layout (experiment-protocol results.json schema): exp, commit, task, verifier, verifier_cmd, passed,
circuit_path, circuit_sha256, metrics, baseline, improvement_factor, score_delta_factor, runtime_s, salts_or_seeds,
then verify_runs (one summary per run), then the config's fields in order; key_order overrides all of this.

Behaviour chosen where the per-experiment copies (exp-001..exp-011/make_results.py) diverged; the latest wins:
  - Verifier output read as JSON from the first "{" of the stdout capture (exp-005, exp-011); pure JSON files
    (exp-002, exp-008, exp-009) and run records embedded in runs.json (exp-003, exp-011) also work via refs.
  - Means are sum/len (exp-011), not statistics.mean (exp-003); identical for 2 runs, may differ by 1 ulp for 3+.
  - Per-run summary names follow exp-011: toffoli_mean (verifier toffoli_count), toffoli_static
    (max_toffoli_count), shots (verified_shots). exp-008/009 used max_toffoli and verified_shots in metrics.
  - dfthcsos ham_error_mHa is {error_1, error_2} in mHa (exp-002, exp-006, exp-007); exp-001 used a max scalar.
  - verifier_cmd: interpreter dropped, an absolute verifier script path reduced to its basename, cwd appended when
    the meta has one (exp-011 with exp-008/009's cwd note); a list when there are several runs (exp-011), a string for one.
  - salts_or_seeds: the salt, or "(default, no salt)" (exp-011); "seed N" when a seed is given.
  - commit from --commit, default "pending" (exp-008..011). exp-002 kept an older commit from the existing file and
    exp-001/003/007 called git rev-parse; neither is done here.
  - JSON written with indent 1 and a trailing newline (exp-004, exp-009, exp-011), always with LF line ends. The
    copies used write_text without newline=, so on Windows their working-tree files have CRLF; git stores LF.
  - dqi metrics: t_gates is null unless the config supplies it (the dqi verifier reports no T count; exp-003 wrote
    0, exp-011 took kickmix's num_t_like). Multi-run lists (_per_salt, _range, failures list) only when >1 run.
  - invsqrt over several salts: worst_error_over_tolerance/worst_x of the worst run, rotation_eps the minimum.
    dfthcsos: Q must agree, toffoli and cost are means, the other figures come from the first run.
  - Runs spanning several tasks (exp-001): metrics, circuit_sha256 and improvement_factor become {task: ...} and
    score_delta_factor is the product of the per-task factors to the 1/3.
  - Analysis-specific numbers (exp-003 Toffoli accounting, exp-005 kernel semantics, exp-010 ledgers) stay in the
    experiment's own analysis scripts; their JSON outputs enter results.json through "$ref" fields.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VERIFIER = {'invsqrt': 'verify_submission_invsqrt.py', 'dqi': 'verify_submission_dqi.py',
            'dfthcsos': 'dfthcsos/verify.py'}
SCHEMA_KEYS = ['exp', 'commit', 'task', 'verifier', 'verifier_cmd', 'passed', 'circuit_path', 'circuit_sha256',
               'metrics', 'baseline', 'improvement_factor', 'score_delta_factor', 'runtime_s', 'salts_or_seeds']
REQUIRED_METRICS = {'invsqrt': ['Q', 'toffoli', 't_gates', 'cost'],
                    'dqi': ['Q', 'toffoli', 't_gates', 'cost', 'failures', 'shots', 'eps_plus', 'R'],
                    'dfthcsos': ['Q', 'toffoli', 't_gates', 'cost', 'lambda_eff', 'Lambda', 'E_gap', 'ham_error_mHa',
                                 'max_width', 'n_circuits']}
DEFAULT_META_KEYS = ['wall_s', 'proc_hwm_peak_bytes', 'tree_rss_peak_bytes', 'peak_rss_bytes_max_process', 'peak']
CHUNK = 1 << 22


# ---------------------------------------------------------------- files and refs
def rpath(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else REPO / p


_cache: dict = {}


def load_doc(path: str):
    p = rpath(path)
    key = str(p)
    if key not in _cache:
        text = p.read_text(encoding='utf-8')
        try:
            _cache[key] = json.loads(text)
        except json.JSONDecodeError:
            if '{' not in text:
                raise ValueError(f'{path}: no JSON object found')
            _cache[key] = json.loads(text[text.index('{'):])
    return _cache[key]


_SEG = re.compile(r'([^.\[\]]+)|\[(\d+)\]|\[([^=\]]+)=([^\]]*)\]')


def walk(doc, ptr: str, where: str):
    pos = 0
    ptr = ptr.strip()
    while pos < len(ptr):
        if ptr[pos] == '.':
            pos += 1
            continue
        m = _SEG.match(ptr, pos)
        if not m:
            raise ValueError(f'{where}: bad pointer at {ptr[pos:]!r}')
        pos = m.end()
        if m.group(1) is not None:
            doc = doc[m.group(1)]
        elif m.group(2) is not None:
            doc = doc[int(m.group(2))]
        else:
            k, v = m.group(3), m.group(4)
            hits = [x for x in doc if isinstance(x, dict) and str(x.get(k)) == v]
            if len(hits) != 1:
                raise ValueError(f'{where}: [{k}={v}] matched {len(hits)} items')
            doc = hits[0]
    return doc


def ref(spec: str):
    path, _, ptr = spec.partition('#')
    return walk(load_doc(path), ptr, spec)


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(rpath(p), 'rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- restricted expressions
_FUNCS = {f.__name__: f for f in (abs, min, max, all, any, sum, len, round, sorted, list, dict, float, int, str,
                                  bool, range, zip, enumerate)}
_ALLOWED_ATTRS = {'values', 'keys', 'items', 'get', 'isfinite', 'isclose', 'sqrt', 'log', 'exp', 'prod', 'fsum'}


def safe_eval(expr: str, names: dict):
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Lambda, ast.NamedExpr, ast.Await, ast.Yield)):
            raise ValueError(f'$expr: {type(node).__name__} not allowed: {expr}')
        if isinstance(node, ast.Attribute) and node.attr not in _ALLOWED_ATTRS:
            raise ValueError(f'$expr: attribute .{node.attr} not allowed: {expr}')
        if isinstance(node, ast.Name) and node.id.startswith('_'):
            raise ValueError(f'$expr: name {node.id} not allowed: {expr}')
    env = {'__builtins__': {}, **_FUNCS, 'math': math, 'ref': ref, **names}
    return eval(compile(tree, '<$expr>', 'eval'), env)  # noqa: S307 - AST-checked, no builtins


def evaluate(t, ctx: dict):
    """Evaluate a config template: directives are replaced by their values, everything else is literal."""
    if isinstance(t, list):
        return [evaluate(x, ctx) for x in t]
    if not isinstance(t, dict):
        return t
    first = next(iter(t), '')
    if not first.startswith('$'):
        return {k: evaluate(v, ctx) for k, v in t.items()}
    if first == '$literal':
        return t['$literal']
    if first == '$ref':
        path = t['$ref'].partition('#')[0]
        if 'default' in t and not rpath(path).exists():
            return t['default']
        v = ref(t['$ref'])
        if 'pick' in t:
            v = {k: v[k] for k in t['pick']}
        if 'first' in t:
            v = dict(list(v.items())[:t['first']]) if isinstance(v, dict) else v[:t['first']]
        return v
    if first == '$map':
        src = ref(t['$map'])
        val = t.get('value')
        if isinstance(src, list):
            return {x[t['key']]: (x[val] if val else x) for x in src}
        return {k: (v[val] if val else v) for k, v in src.items()}
    if first == '$expr':
        return safe_eval(t['$expr'], ctx)
    if first == '$when':
        return evaluate(t['value'], ctx) if rpath(t['$when']).exists() else t.get('else')
    if first == '$sha256':
        return sha256_file(t['$sha256'])
    raise ValueError(f'unknown directive {first}')


# ---------------------------------------------------------------- per-task extraction
def run_summary(task: str, v: dict) -> dict:
    if task == 'dqi':
        return {'status': v['status'], 'Q': v['num_qubits'], 'toffoli_mean': v['toffoli_count'],
                'toffoli_static': v['max_toffoli_count'], 'failures': v['value_errors'] + v['phase_errors'],
                'value_errors': v['value_errors'], 'phase_errors': v['phase_errors'], 'shots': v['verified_shots'],
                'eps_plus': v['effective_error_rate'], 'R': v['repetition_factor'], 'cost': v['score'],
                'num_ops': v.get('num_ops'), 'reaction_depth': v.get('reaction_depth'),
                'circuit_sha256': v.get('circuit_sha256')}
    if task == 'invsqrt':
        return {'status': v['status'], 'Q': v['num_qubits'], 'toffoli_mean': v['toffoli_count'],
                'toffoli_static': v.get('max_toffoli_count'), 't_gates': v.get('t_count'),
                'rotation_count': v.get('rotation_count'), 'rotation_eps': v.get('rotation_eps'),
                'toffoli_equivalent': v.get('toffoli_equivalent'), 'cost': v['score'],
                'worst_error_over_tolerance': v.get('worst_error_over_tolerance'), 'worst_x': v.get('worst_x'),
                'shots': v.get('verified_shots'), 'circuit_sha256': v.get('circuit_sha256')}
    if task == 'dfthcsos':
        m, r = v.get('metrics', {}), v.get('resources', {})
        err = {k: 1e3 * m[k] for k in ('error_1', 'error_2') if k in m}
        return {'status': v['status'], 'Q': v['num_qubits'], 'toffoli': v['toffoli_count'], 'cost': v['score'],
                'lambda_eff': v.get('lambda_eff'), 'Lambda': m.get('Lambda'), 'E_gap': m.get('E_gap'),
                'ham_error_mHa': err, 'max_width': r.get('angles_qubits'), 'n_circuits': v.get('num_circuits'),
                'brot': v.get('brot'), 'J': v.get('batch_size'), 'angles_toffoli': r.get('angles_toffoli'),
                'angles_toffoli_per_pass': r.get('angles_toffoli_per_pass'),
                'heuristic_toffoli': r.get('heuristic_toffoli'), 'shots': v.get('verified_shots'),
                'submission_sha256': v.get('submission_sha256')}
    raise ValueError(f'unknown task {task}')


def same(xs, what):
    if any(x != xs[0] for x in xs):
        raise ValueError(f'{what} differs between runs: {xs}')
    return xs[0]


def mean(xs):
    return sum(xs) / len(xs)


def aggregate(task: str, rs: list) -> dict:
    n = len(rs)
    col = lambda k: [r[k] for r in rs]  # noqa: E731
    costs = col('cost')
    if not all(isinstance(c, (int, float)) and math.isfinite(c) for c in costs):
        raise ValueError(f'non-finite cost: {costs}')
    multi = {'cost_per_salt': costs, 'cost_range': [min(costs), max(costs)]} if n > 1 else {}
    if task == 'dqi':
        eps, R = col('eps_plus'), col('R')
        out = {'Q': same(col('Q'), 'Q'), 'toffoli': mean(col('toffoli_mean'))}
        if n > 1:
            out['toffoli_per_salt'] = col('toffoli_mean')
        out |= {'toffoli_static': same(col('toffoli_static'), 'toffoli_static'), 't_gates': None,
                'num_ops': same(col('num_ops'), 'num_ops'), 'cost': mean(costs), **multi,
                'failures': col('failures') if n > 1 else rs[0]['failures'], 'shots': same(col('shots'), 'shots'),
                'eps_plus': mean(eps), 'R': mean(R)}
        if n > 1:
            out |= {'eps_plus_range': [min(eps), max(eps)], 'eps_plus_per_salt': eps, 'R_per_salt': R}
        return out
    if task == 'invsqrt':
        worst = max(rs, key=lambda r: r['worst_error_over_tolerance'] or 0)
        out = {'Q': same(col('Q'), 'Q'), 'toffoli': mean(col('toffoli_mean'))}
        if n > 1:
            out['toffoli_per_salt'] = col('toffoli_mean')
        out |= {'toffoli_static': same(col('toffoli_static'), 'toffoli_static'), 't_gates': same(col('t_gates'), 't'),
                'rotation_count': same(col('rotation_count'), 'rotation_count'),
                'rotation_eps': min(col('rotation_eps')) if n > 1 else rs[0]['rotation_eps'],
                'toffoli_equivalent': mean(col('toffoli_equivalent')) if n > 1 else rs[0]['toffoli_equivalent'],
                'cost': mean(costs), **multi,
                'worst_error_over_tolerance': worst['worst_error_over_tolerance'], 'worst_x': worst['worst_x'],
                'shots': same(col('shots'), 'shots')}
        return out
    # dfthcsos: Q and the mean T/cost; the remaining figures are taken from the first run.
    rest = {k: v for k, v in rs[0].items() if k not in ('status', 'submission_sha256', 'cost', 'toffoli', 'Q')}
    return {'Q': same(col('Q'), 'Q'), 'toffoli': mean(col('toffoli')), 't_gates': None, 'cost': mean(costs),
            **multi, **rest}


def cmd_string(meta: dict):
    cmd = meta.get('cmd')
    if cmd is None:
        return None
    if isinstance(cmd, str):
        s = cmd
    else:
        parts = list(cmd[1:])
        for i, c in enumerate(parts):
            if c.endswith('.py'):  # the verifier script: basename if absolute, else as given (cwd-relative)
                parts[i] = Path(c).name if c.startswith('/') or Path(c).is_absolute() else c
                break
        s = ' '.join(parts)
    return s + (f"  (cwd {meta['cwd']})" if meta.get('cwd') else '')


# ---------------------------------------------------------------- assembly
CONFIG_KEYS = {'exp', 'task', 'commit', 'output', 'indent', 'verifier', 'runs', 'circuit_path', 'circuit_sha256',
               'baseline', 'metrics_fields', 'metrics_keys', 'run_fields', 'run_meta_keys', 'fields', 'key_order'}
RUN_KEYS = {'label', 'salt', 'seed', 'task', 'output', 'meta'}


def assemble(cfg: dict, commit: str) -> dict:
    unknown = [k for k in cfg if k not in CONFIG_KEYS and not k.startswith('_')]
    unknown += [f'runs[].{k}' for r in cfg.get('runs', []) for k in r if k not in RUN_KEYS]
    if unknown:
        raise ValueError(f'unknown config keys (prefix "_" for comments): {unknown}')
    if cfg['task'] not in ('invsqrt', 'dqi', 'dfthcsos', 'all'):
        raise ValueError(f"task {cfg['task']!r}")
    if 'circuit_path' not in cfg:
        raise ValueError('circuit_path is required (null if there is no circuit)')
    task = cfg['task']
    meta_keys = cfg.get('run_meta_keys', DEFAULT_META_KEYS)
    runs, run_tasks, metas, pure = {}, {}, {}, {}
    for spec in cfg.get('runs', []):
        lab = spec['label']
        rt = spec.get('task', task)
        if rt not in VERIFIER:
            raise ValueError(f'run {lab}: task {rt!r} needs to be invsqrt, dqi or dfthcsos')
        out = evaluate({'$ref': spec['output']} if isinstance(spec['output'], str) else spec['output'], {})
        meta = spec.get('meta', {})
        meta = evaluate({'$ref': meta} if isinstance(meta, str) else meta, {})
        rec = {'salt': spec.get('salt')}
        if 'seed' in spec:
            rec['seed'] = spec['seed']
        pure[lab] = run_summary(rt, out)
        rec |= pure[lab]
        rec |= {k: meta[k] for k in meta_keys if k in meta}
        runs[lab], run_tasks[lab], metas[lab] = rec, rt, meta
    for lab, rec in runs.items():
        for k, t in cfg.get('run_fields', {}).items():
            rec[k] = evaluate(t, {'run': rec, 'runs': runs})
    tasks = list(dict.fromkeys(run_tasks.values()))
    multi_task = len(tasks) > 1
    by_task = {t: [pure[l] for l in runs if run_tasks[l] == t] for t in tasks}
    metrics = {t: aggregate(t, rs) for t, rs in by_task.items()}
    passed = all(r['status'] == 'PASS' for r in runs.values()) if runs else None
    baseline = evaluate(cfg.get('baseline'), {})

    def hashes(t):
        key = 'submission_sha256' if t == 'dfthcsos' else 'circuit_sha256'
        return same([r[key] for r in by_task[t]], key)

    if multi_task:
        cost = {t: m['cost'] for t, m in metrics.items()}
        imp = {t: baseline[t]['cost'] / cost[t] for t in tasks if baseline and t in baseline}
        sdf = math.prod(imp.values()) ** (1 / 3) if imp else None
        circ = {t: hashes(t) for t in tasks}
    elif tasks:
        metrics = metrics[tasks[0]]
        cost = metrics['cost']
        imp = baseline['cost'] / cost if baseline and baseline.get('cost') else None
        sdf = imp ** (1 / 3) if imp else None
        circ = hashes(tasks[0])
    else:
        metrics, cost, imp, sdf, circ = {}, None, None, None, None
    ctx = {'runs': runs, 'baseline': baseline, 'passed': passed, 'cost': cost}
    if not multi_task:
        mf = {k: evaluate(t, ctx | {'metrics': metrics}) for k, t in cfg.get('metrics_fields', {}).items()}
        metrics = metrics | mf
        if 'metrics_keys' in cfg:
            missing = [k for k in cfg['metrics_keys'] if k not in metrics]
            if missing:
                raise ValueError(f'metrics_keys not available: {missing}')
            metrics = {k: metrics[k] for k in cfg['metrics_keys']}
        for t in tasks:
            lost = [k for k in REQUIRED_METRICS[t] if k not in metrics]
            if lost:
                print(f'warning: metrics omit protocol keys {lost}', file=sys.stderr)
    cmds = [cmd_string(metas[l]) for l in runs]
    salts = [f"seed {r['seed']}" if 'seed' in r else (r['salt'] if r['salt'] is not None else '(default, no salt)')
             for r in runs.values()]
    walls = {l: r.get('wall_s') for l, r in runs.items()}
    res = {
        'exp': cfg['exp'], 'commit': commit, 'task': task,
        'verifier': cfg.get('verifier', (VERIFIER[tasks[0]] if len(tasks) == 1 else
                                         [VERIFIER[t] for t in tasks]) if tasks else None),
        'verifier_cmd': (cmds[0] if len(cmds) == 1 else cmds) if cmds else None,
        'passed': passed,
        'circuit_path': cfg['circuit_path'],
        'circuit_sha256': circ,
        'metrics': metrics,
        'baseline': baseline,
        'improvement_factor': imp,
        'score_delta_factor': sdf,
        'runtime_s': (next(iter(walls.values())) if len(walls) == 1 else walls) if walls else None,
        'salts_or_seeds': salts,
    }
    if 'circuit_sha256' in cfg:
        res['circuit_sha256'] = evaluate(cfg['circuit_sha256'], ctx | {'metrics': metrics})
    if runs:
        res['verify_runs'] = runs
    for k, t in cfg.get('fields', {}).items():
        res[k] = evaluate(t, ctx | {'metrics': metrics, 'fields': res})
    if 'key_order' in cfg:
        order = cfg['key_order']
        if sorted(order) != sorted(res):
            raise ValueError(f'key_order mismatch: missing {sorted(set(res) - set(order))}, '
                             f'unknown {sorted(set(order) - set(res))}')
        res = {k: res[k] for k in order}
    return res


def diff(a, b, path=''):
    """List of paths where two JSON values differ (values or key order)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        if list(a) != list(b) and set(a) == set(b):
            out.append(f'{path or "<root>"}: key order differs')
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f'{path}.{k}: only in {"new" if k in a else "existing"}')
            else:
                out += diff(a[k], b[k], f'{path}.{k}')
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f'{path}[{i}]')]
    return [] if a == b and type(a) is type(b) else [f'{path}: new {a!r} != existing {b!r}']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                 epilog='See the module docstring for the config keys and directives.')
    ap.add_argument('config', help='results config JSON (usually experiments/exp-NNN/results_config.json)')
    ap.add_argument('--commit', help='commit hash recorded as "commit" (default: config "commit", else "pending")')
    ap.add_argument('--out', help='output path (default: config "output", else results.json next to the config)')
    ap.add_argument('--check', action='store_true', help='compare with the existing output, write nothing')
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    cfg_path = rpath(a.config)
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    res = assemble(cfg, a.commit or cfg.get('commit', 'pending'))
    out = rpath(a.out) if a.out else (rpath(cfg['output']) if 'output' in cfg else cfg_path.parent / 'results.json')
    text = json.dumps(res, indent=cfg.get('indent', 1)) + '\n'
    if a.check:
        old_bytes = out.read_bytes()
        old = json.loads(old_bytes)
        d = diff(res, old)
        lf = old_bytes.replace(b'\r\n', b'\n')
        try:
            relp = out.resolve().relative_to(REPO.resolve()).as_posix()
            blob = subprocess.run(['git', '-C', str(REPO), 'show', f'HEAD:{relp}'], capture_output=True,
                                  check=True).stdout
            git_equal = text.encode('utf-8') == blob
        except (ValueError, subprocess.CalledProcessError):
            git_equal = None  # outside the repo or not tracked
        print(json.dumps({'compared_with': str(out), 'json_equal': not d, 'differences': d,
                          'bytes_equal': text.encode('utf-8') == old_bytes,
                          'bytes_equal_after_crlf_to_lf': text.encode('utf-8') == lf,
                          'bytes_equal_git_head': git_equal}, indent=1))
        return 0 if not d else 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    m = res.get('metrics') or {}
    print(json.dumps({'wrote': str(out), 'passed': res['passed'], 'improvement_factor': res['improvement_factor'],
                      'score_delta_factor': res['score_delta_factor'],
                      'metrics': {k: m.get(k) for k in ('Q', 'toffoli', 'cost', 'eps_plus', 'R') if k in m}
                      if 'Q' in m else m}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
