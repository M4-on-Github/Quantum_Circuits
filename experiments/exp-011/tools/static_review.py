"""Static (parse-only) review of the ported kit src/dqi/pro_q2_897. Nothing in the kit is imported or run.

Usage: python -I -B static_review.py <src/dqi> <out.json>

For every .py file: ast.parse under this interpreter, top-level imports (absolute and relative), calls
to a watch-list of names (open, exec, eval, compile, __import__, importlib.*, subprocess.*, os.*,
pickle.*, socket.*, urllib.*, shutil.*), whether those calls sit under `if __name__ == '__main__'`,
and module-level statements other than imports, defs, classes, assignments and asserts.
"""
import ast
import json
import sys
from pathlib import Path

WATCH = {'open', 'exec', 'eval', 'compile', '__import__', 'FunctionType', 'write_text', 'write_bytes', 'unlink',
         'rmtree', 'system', 'popen', 'Popen', 'run', 'call', 'load', 'loads', 'urlopen', 'connect',
         'exec_module', 'spec_from_file_location', 'setattr', 'globals'}


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
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


def review(path: Path, kit: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    guarded = main_guard_lines(tree)
    imports, calls, toplevel = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append('.' * node.level + (node.module or ''))
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            if name.split('.')[-1] in WATCH or name.split('.')[0] in {'subprocess', 'os', 'pickle', 'socket',
                                                                     'urllib', 'shutil', 'importlib'}:
                calls.append(dict(line=node.lineno, call=name, under_main=node.lineno in guarded))
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.Assign,
                                 ast.AnnAssign, ast.Assert, ast.Expr, ast.AugAssign)):
            toplevel.append(dict(line=node.lineno, kind=type(node).__name__))
    return dict(file=path.relative_to(kit).as_posix(), imports=sorted(set(imports)), watched_calls=calls,
                other_toplevel=toplevel)


def main():
    kit = Path(sys.argv[1]) / 'pro_q2_897'
    files = sorted(p for p in kit.rglob('*.py'))
    out = [review(p, kit) for p in files]
    ext = sorted({i.split('.')[0] for r in out for i in r['imports'] if not i.startswith('.')})
    summary = dict(n_py=len(files), python=sys.version.split()[0], all_parse=True, top_level_import_names=ext,
                   watched_calls_outside_main=[dict(file=r['file'], **c) for r in out for c in r['watched_calls']
                                               if not c['under_main']],
                   files=out)
    Path(sys.argv[2]).write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print('py files', len(files), 'all parse; import names:', ext)
    for c in summary['watched_calls_outside_main']:
        print('  ', c['file'], c['line'], c['call'])


if __name__ == '__main__':
    main()
