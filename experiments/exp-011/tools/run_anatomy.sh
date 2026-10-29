#!/bin/bash
# exp-011 local anatomy of our build's .kmx text (exported by the kernel). Our own scripts only, python -I -B.
set -e
cd /c/Users/moemy/Documents/Kaggle/Quantum_Circuits
PY=.venv/Scripts/python.exe
XZ=experiments/exp-011/kaggle_output/exp011/dqi.kmx.xz
A=experiments/exp-011/out/anatomy
t() { local s=$(date +%s); "$@"; echo "[time] $(( $(date +%s) - s )) s: $*"; }
t $PY -I -B experiments/exp-005/analysis/kmx_skeleton.py $XZ $A/skeleton.npz
t $PY -I -B experiments/exp-005/analysis/fingerprint_search.py $A/skeleton.npz $A/fingerprint_search.json
t $PY -I -B experiments/exp-005/analysis/kernel_semantics.py $A/skeleton.npz $XZ $A/semantics_restart.json $A/semantics_restart_gates.npz restart > $A/semantics_restart.log
t $PY -I -B -c "import lzma,shutil,hashlib,sys; h=hashlib.sha256(); f=lzma.open(sys.argv[1],'rb'); o=open(sys.argv[2],'wb')
while True:
    b=f.read(1<<22)
    if not b: break
    h.update(b); o.write(b)
o.close(); print('kmx sha256', h.hexdigest())" $XZ $A/dqi.kmx
t $PY -I -B src/kmx_tag_count.py $A/dqi.kmx $A/tag_count.json
rm -f $A/dqi.kmx
t $PY -I -B experiments/exp-011/tools/anatomy_compare.py . $A/compare.json
echo ANATOMY_DONE
