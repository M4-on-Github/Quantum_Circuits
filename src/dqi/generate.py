"""Build the dqi circuit from the ported pro_q2_897 kit (see NOTICE, LICENSE).

Usage:
    python -I -B src/dqi/generate.py OUT.kmb             full build: OUT.kmb + OUT.build.json
    python -I -B src/dqi/generate.py --import-only OUT.json
                                                         manifest check + import of the kit, no decode()

Our re-implementation of the upstream pro_q2_897/build_897.py (which is not run). It does the same:
kickmix is the kit's builder module 'circ'; the entry point is pro_q2_897/final_decoder/decode.py,
loaded by file location as module 'decoder_under_test'; the registers S0..S69 (12 qubits each) and
E0..E4094 (12 classical bits each) are allocated in that order, decode(b, S, E) is called, and the
REGISTER / APPEND_TO_REGISTER metadata is prepended to the finished circuit. Added: a SHA-256 check of
every kit file against MANIFEST.json before anything is imported, and in the JSON record the kickmix
version, the kit files actually imported, and the stdlib / third-party modules imported during the build
(to show that no bare-name kit import resolved outside the kit).
"""
import hashlib
import importlib.metadata
import importlib.util
import json
import sys
import sysconfig
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE / 'pro_q2_897'
EXPECTED_SHA256 = 'b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6'


def check_manifest() -> int:
    manifest = json.loads((HERE / 'MANIFEST.json').read_text(encoding='utf-8'))
    bad = []
    for rel, want in manifest['files'].items():
        got = hashlib.sha256((KIT / rel).read_bytes()).hexdigest()
        if got != want:
            bad.append(rel)
    if bad:
        raise SystemExit(f'kit files differ from MANIFEST.json: {bad}')
    return len(manifest['files'])


def load_decoder():
    import kickmix as km
    sys.modules['circ'] = km
    spec = importlib.util.spec_from_file_location('decoder_under_test', KIT / 'final_decoder' / 'decode.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['decoder_under_test'] = module
    spec.loader.exec_module(module)
    return km, module


def module_origins(before: set[str]) -> dict:
    """Modules imported since `before`, outside the kit: stdlib and third-party top-level names."""
    stdlib = Path(sysconfig.get_paths()['stdlib']).resolve()
    std, third = set(), {}
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, '__file__', None)
        if name in before or not f:
            continue
        p = Path(f).resolve()
        if p.is_relative_to(KIT):
            continue
        top = name.split('.')[0]
        if p.is_relative_to(stdlib) and 'site-packages' not in p.parts:
            std.add(top)
        else:
            third.setdefault(top, str(p.parent))
    return dict(stdlib_top_level=sorted(std), third_party_top_level=dict(sorted(third.items())))


def kit_modules() -> list[str]:
    out = set()
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, '__file__', None)
        if f:
            try:
                out.add(Path(f).resolve().relative_to(KIT).as_posix())
            except ValueError:
                pass
    return sorted(out)


def build(target: Path) -> dict:
    start = time.time()
    before = set(sys.modules)
    n_files = check_manifest()
    km, module = load_decoder()
    b = km.CircuitBuilder()
    S = [b.alloc_qubits(12) for _ in range(70)]
    E = [b.alloc_bits(12) for _ in range(4095)]
    module.decode(b, S, E)
    metadata = []
    for i in range(70):
        metadata.append(f'REGISTER r{i} "S{i}"')
        metadata.extend(f'APPEND_TO_REGISTER q{12 * i + k} r{i}' for k in range(12))
    for j in range(4095):
        metadata.append(f'REGISTER r{70 + j} "E{j}"')
        metadata.extend(f'APPEND_TO_REGISTER b{12 * j + k} r{70 + j}' for k in range(12))
    c = km.Circuit('\n'.join(metadata)) + b.finish_circuit()
    c.to_file(str(target), format='kmb')
    with open(target, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    return dict(sha256=digest, matches_upstream_stated=(digest == EXPECTED_SHA256), Q=c.num_qubits,
                T_static=c.operation_statistics().num_toffoli_like, num_ops=len(c), num_bits=c.num_bits,
                seconds=round(time.time() - start, 1), kit_files_checked=n_files,
                kickmix_version=importlib.metadata.version('kickmix'), kit_modules_imported=kit_modules(),
                **module_origins(before))


def main(argv: list[str]) -> None:
    if argv and argv[0] == '--import-only':
        start = time.time()
        before = set(sys.modules)
        n_files = check_manifest()
        load_decoder()
        record = dict(kit_files_checked=n_files, kit_modules_imported=kit_modules(), **module_origins(before),
                      kickmix_version=importlib.metadata.version('kickmix'), seconds=round(time.time() - start, 1))
        Path(argv[1]).write_text(json.dumps(record, indent=1) + '\n', encoding='utf-8')
    else:
        target = Path(argv[0])
        record = build(target)
        target.with_suffix('.build.json').write_text(json.dumps(record, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in record.items() if k != 'kit_modules_imported'}), flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
