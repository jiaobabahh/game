"""Refresh the browser's copies of the original engines without editing the engines."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
target = root / 'docs' / 'engine'
target.mkdir(parents=True, exist_ok=True)
for name in ['__init__', 'prop', 'sets_engine', 'rels', 'graphs', 'autodissect', 'cases', 'runner']:
    shutil.copyfile(root / 'src' / 'dmverify' / f'{name}.py', target / f'{name}.py')
