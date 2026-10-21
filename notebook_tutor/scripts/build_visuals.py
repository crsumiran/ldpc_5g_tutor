"""Render the public visual explanations before any learner TODO is filled."""

import contextlib
import io
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import matplotlib

matplotlib.use('Agg')

from qwen_numpy import checks, reference, tutorial
assets = root / 'assignments' / 'qwen36_27b' / 'assets'
assets.mkdir(parents=True, exist_ok=True)
for name in checks.TUTORIAL_TASKS:
    path = assets / f'{name}.png'
    with contextlib.redirect_stdout(io.StringIO()):
        tutorial.show_small(name, reference, save_path=path)
    print(path.relative_to(root))
