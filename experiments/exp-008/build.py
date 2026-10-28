"""exp-008: build our invsqrt circuit from a config with src/invsqrt.

Usage: python -I -B experiments/exp-008/build.py <config.json> <out.kmb> [work_dir]
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

if __name__ == '__main__':
    from invsqrt import generate
    cfg, out = sys.argv[1], sys.argv[2]
    work = sys.argv[3] if len(sys.argv) > 3 else str(REPO / 'experiments' / 'exp-008' / 'out' / 'work')
    generate.main([cfg, work, out])
