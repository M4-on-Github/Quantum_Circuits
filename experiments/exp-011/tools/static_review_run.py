"""Static (parse-only) review of every file the exp-011 Kaggle kernel will run. Nothing reviewed is imported or run.

Usage: python -I -B static_review_run.py <repo root> <out.json>

Scope:
- the ported kit src/dqi/pro_q2_897/**.py (59 files; the kernel runs the subset decode.py imports, recorded at
  run time by generate.py as kit_modules_imported);
- our launcher src/dqi/generate.py and the kernel script template experiments/exp-011/kernel/exp011_template.py;
- the kit's non-.py files (how each one is read).

Per file, five categories, from the AST:
  imports       every import (absolute, relative, inside functions too)
  file_writes   open(..., mode with w/a/x/+), write_text, write_bytes, to_file, mkdir, unlink, rename, replace,
                rmtree, copy*, remove, makedirs, lzma/gzip/zipfile opens in write mode
  network       imports of / calls into socket, ssl, http, urllib, requests, ftplib, smtplib, asyncio, websocket,
                xmlrpc, telnetlib, pip
  subprocess    subprocess, os.system/popen/exec*/spawn*/fork, multiprocessing, pty, concurrent.futures
  dynamic       exec, eval, compile, __import__, importlib.*, runpy, zipimport, marshal, pickle, shelve, ctypes,
                types.FunctionType / CodeType, .__code__ / .__globals__ access, globals()/vars() writes,
                setattr on modules, sys.path and sys.modules mutation
Each hit carries its line, the enclosing function (or <module>), whether it is lexically inside
`if __name__ == '__main__'`, and, for hits inside a function, whether every call site of that function name
in the same file is under the main guard (main_only). Module-level code other than imports, defs, classes,
assignments and asserts is listed too, because it runs at import.
For the kit, bare-name imports are resolved against the kit's own files: any name that is neither stdlib,
kickmix/numpy/circ, nor a kit file/package would have to come from somewhere else and is listed.
"""
import ast
import json
import sys
from pathlib import Path

NET_MODS = {'socket', 'ssl', 'http', 'urllib', 'urllib3', 'requests', 'ftplib', 'smtplib', 'asyncio', 'websocket',
            'websockets', 'xmlrpc', 'telnetlib', 'pip', 'httpx', 'aiohttp', 'paramiko'}
SUB_MODS = {'subprocess', 'multiprocessing', 'pty', 'concurrent'}
DYN_MODS = {'importlib', 'runpy', 'zipimport', 'marshal', 'pickle', 'shelve', 'ctypes', 'cffi', 'dill', 'code',
            'codeop'}
WRITE_ATTRS = {'write_text', 'write_bytes', 'to_file', 'mkdir', 'unlink', 'rename', 'replace', 'rmtree', 'copy',
               'copy2', 'copyfile', 'copytree', 'remove', 'makedirs', 'removedirs', 'rmdir', 'move', 'touch',
               'symlink_to', 'hardlink_to', 'chmod', 'truncate'}
OS_SUB = {'system', 'popen', 'execv', 'execve', 'execl', 'execlp', 'execvp', 'execvpe', 'spawnv', 'spawnl',
          'spawnve', 'fork', 'forkpty', 'posix_spawn', 'startfile', 'kill'}
DYN_CALLS = {'exec', 'eval', 'compile', '__import__', 'FunctionType', 'CodeType', 'globals', 'vars', 'setattr',
             'delattr', 'exec_module', 'spec_from_file_location', 'module_from_spec', 'import_module', 'reload',
             'load', 'loads'}
SAFE_TOP = {'kickmix', 'numpy', 'circ', 'psutil'}


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    elif isinstance(node, ast.Call):
        parts.append(dotted(node.func) + '()')
    elif isinstance(node, ast.Subscript):
        parts.append(dotted(node.value) + '[]')
    return '.'.join(reversed(parts))


def main_guard_lines(tree):
    lines = set()
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and \
                getattr(node.test.left, 'id', None) == '__name__':
            for sub in ast.walk(node):
                if hasattr(sub, 'lineno'):
                    lines.add(sub.lineno)
    return lines


def parents_map(tree):
    par = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            par[ch] = node
    return par


def enclosing_func(node, par):
    while node in par:
        node = par[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return getattr(node, 'name', '<lambda>')
    return '<module>'


def open_mode(call):
    mode = None
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        mode = call.args[1].value
    for kw in call.keywords:
        if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
            mode = kw.value.value
    return mode


def review(path: Path, rel: str):
    text = path.read_text(encoding='utf-8')
    tree = ast.parse(text, filename=str(path))
    guard = main_guard_lines(tree)
    par = parents_map(tree)
    cats = {k: [] for k in ('imports', 'file_writes', 'network', 'subprocess', 'dynamic')}
    calls_by_name = {}

    def hit(cat, node, what):
        cats[cat].append(dict(line=node.lineno, what=what, func=enclosing_func(node, par),
                              under_main_guard=node.lineno in guard))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                ['.' * node.level + (node.module or '')]
            for n in names:
                cats['imports'].append(dict(line=node.lineno, name=n, func=enclosing_func(node, par)))
                top = n.lstrip('.').split('.')[0]
                if top in NET_MODS:
                    hit('network', node, f'import {n}')
                if top in SUB_MODS:
                    hit('subprocess', node, f'import {n}')
                if top in DYN_MODS or n == 'types' or (isinstance(node, ast.ImportFrom) and node.module == 'types'):
                    hit('dynamic', node, f'import {n}' + ('' if isinstance(node, ast.Import) else
                                                          ' : ' + ','.join(a.name for a in node.names)))
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            last, first = name.split('.')[-1], name.split('.')[0]
            calls_by_name.setdefault(last, []).append(node.lineno)
            if last == 'open' or name in ('lzma.open', 'gzip.open', 'bz2.open', 'zipfile.ZipFile'):
                mode = open_mode(node)
                if mode is not None and any(c in str(mode) for c in 'wax+'):
                    hit('file_writes', node, f'{name}(mode={mode!r})')
                elif mode is None and len(node.args) >= 2:
                    hit('file_writes', node, f'{name}(mode=<non-constant>)')
            if last in WRITE_ATTRS:
                hit('file_writes', node, name)
            if first in NET_MODS:
                hit('network', node, name)
            if first in SUB_MODS or (first == 'os' and last in OS_SUB) or last in ('Popen', 'check_call',
                                                                               'check_output'):
                hit('subprocess', node, name)
            if first == 'subprocess' or (first == 'sys' and last == 'executable'):
                pass
            if last in DYN_CALLS and not (last in ('load', 'loads') and first == 'json'):
                hit('dynamic', node, name)
            elif last in ('load', 'loads') and first == 'json':
                hit('dynamic', node, name + ' (data only: JSON)')
            if first == 'sys' and name.startswith('sys.path') and last in ('insert', 'append', 'extend', 'remove'):
                hit('dynamic', node, name)
        elif isinstance(node, ast.Attribute) and node.attr in ('__code__', '__globals__', '__closure__',
                                                                '__builtins__', '__dict__'):
            hit('dynamic', node, f'.{node.attr}')
        elif isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                d = dotted(t)
                if d.startswith('sys.path') or d.startswith('sys.modules') or d.startswith('globals()') or \
                        d.startswith('builtins'):
                    hit('dynamic', node, f'assign {d}')
    for cat in cats:
        if cat == 'imports':
            continue
        for h in cats[cat]:
            f = h['func']
            if f not in ('<module>', '<lambda>'):
                sites = calls_by_name.get(f, [])
                h['func_call_sites'] = sites
                h['func_main_only'] = bool(sites) and all(s in guard for s in sites)
    toplevel = [dict(line=n.lineno, kind=type(n).__name__) for n in tree.body
                if not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Assign,
                                      ast.AnnAssign, ast.Assert, ast.Expr, ast.AugAssign))]
    return dict(file=rel, lines=text.count('\n') + 1, **cats, module_level_other=toplevel)


def main():
    repo = Path(sys.argv[1]).resolve()
    kit = repo / 'src' / 'dqi' / 'pro_q2_897'
    kit_files = sorted(kit.rglob('*.py'))
    ours = [repo / 'src' / 'dqi' / 'generate.py', repo / 'experiments' / 'exp-011' / 'kernel' / 'exp011_template.py']
    out_kit = [review(p, 'pro_q2_897/' + p.relative_to(kit).as_posix()) for p in kit_files]
    out_ours = [review(p, p.relative_to(repo).as_posix()) for p in ours]
    # bare-name resolution inside the kit
    kit_names = {p.stem for p in kit_files} | {p.name for p in kit.rglob('*') if p.is_dir()}
    stdlib = set(sys.stdlib_module_names)
    unresolved = {}
    for r in out_kit:
        for imp in r['imports']:
            n = imp['name']
            if n.startswith('.'):
                continue
            top = n.split('.')[0]
            if top in stdlib or top in SAFE_TOP or top in kit_names:
                continue
            unresolved.setdefault(top, []).append(f"{r['file']}:{imp['line']}")
    shadow = sorted(n for n in kit_names if n in stdlib)
    non_py = []
    for p in sorted(kit.rglob('*')):
        if p.is_file() and p.suffix != '.py':
            relp = p.relative_to(kit).as_posix()
            readers = [f"{r['file']}:{h['line']}" for r in out_kit for h in r['dynamic']
                       if h['what'].startswith('json.loads')]
            non_py.append(dict(file='pro_q2_897/' + relp, bytes=p.stat().st_size,
                               referenced_by=sorted({r['file'] for r in out_kit
                                                     if p.name in (kit / r['file'][len('pro_q2_897/'):]).read_text(
                                                         encoding='utf-8')})))

    def summarize(rs, cat):
        return [dict(file=r['file'], **h) for r in rs for h in r[cat]]

    summary = dict(
        python=sys.version.split()[0], n_kit_py=len(out_kit), all_parse=True,
        kit_import_tops=sorted({i['name'].split('.')[0] for r in out_kit for i in r['imports']
                                if not i['name'].startswith('.')}),
        kit_imports_unresolved=unresolved, kit_names_shadowing_stdlib=shadow,
        kit_network=summarize(out_kit, 'network'), kit_subprocess=summarize(out_kit, 'subprocess'),
        kit_file_writes=summarize(out_kit, 'file_writes'),
        kit_dynamic_non_json=[h for h in summarize(out_kit, 'dynamic') if 'JSON' not in h['what']],
        kit_json_reads=[h for h in summarize(out_kit, 'dynamic') if 'JSON' in h['what']],
        kit_module_level_other=[dict(file=r['file'], **t) for r in out_kit for t in r['module_level_other']],
        kit_non_py_files=non_py,
        ours=out_ours, kit=out_kit)
    Path(sys.argv[2]).write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print('kit py', len(out_kit), '| import tops', summary['kit_import_tops'])
    print('unresolved bare names', unresolved, '| kit names shadowing stdlib', shadow)
    for cat in ('kit_network', 'kit_subprocess', 'kit_file_writes'):
        print(cat, len(summary[cat]))
        for h in summary[cat]:
            print('   ', h['file'], h['line'], h['what'], h['func'], 'guard' if h['under_main_guard'] else '',
                  'main_only' if h.get('func_main_only') else '')
    from collections import Counter
    print('kit dynamic (non-JSON) by kind', Counter(h['what'] for h in summary['kit_dynamic_non_json']))
    print('kit json reads', len(summary['kit_json_reads']))
    for r in out_ours:
        print('OURS', r['file'], {c: len(r[c]) for c in ('file_writes', 'network', 'subprocess', 'dynamic')})


if __name__ == '__main__':
    main()
