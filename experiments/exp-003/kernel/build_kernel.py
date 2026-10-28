"""Writes exp003_account.py = exp003_template.py with src/kmx_tag_count.py inlined."""
from pathlib import Path

here = Path(__file__).resolve().parent
src = (here.parents[2] / 'src' / 'kmx_tag_count.py').read_text(encoding='utf-8')
tpl = (here / 'exp003_template.py').read_text(encoding='utf-8')
assert tpl.count('__COUNTER_SRC__') == 1
(here / 'exp003_account.py').write_text(tpl.replace('__COUNTER_SRC__', repr(src)), encoding='utf-8')
print('wrote', here / 'exp003_account.py')
