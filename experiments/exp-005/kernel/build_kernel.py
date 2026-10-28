"""Writes exp005_account.py = exp005_template.py with src/kmx_tag_count.py and src/kmx_segment_sim.py inlined."""
from pathlib import Path

here = Path(__file__).resolve().parent
srcdir = here.parents[2] / 'src'
tpl = (here / 'exp005_template.py').read_text(encoding='utf-8')
for key, fn in (('__COUNTER_SRC__', 'kmx_tag_count.py'), ('__SEGSIM_SRC__', 'kmx_segment_sim.py')):
    assert tpl.count(key) == 1, key
    tpl = tpl.replace(key, repr((srcdir / fn).read_text(encoding='utf-8')))
(here / 'exp005_account.py').write_text(tpl, encoding='utf-8')
print('wrote', here / 'exp005_account.py')
