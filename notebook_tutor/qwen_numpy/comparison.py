"""Compare NumPy logits to a saved original-model reference fixture."""

import json
from pathlib import Path
import numpy as np


def compare(logits, fixture_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding='utf-8'))
    ref = np.asarray(fixture['logits'], dtype=np.float32)
    got = np.asarray(logits, dtype=np.float32)
    if got.shape != ref.shape or not np.isfinite(got).all():
        raise ValueError('Logit shape mismatch or nonfinite NumPy logits')
    top_numpy, top_original = int(np.argmax(got)), int(np.argmax(ref))
    result = {
        'numpy_top_token': top_numpy,
        'original_top_token': top_original,
        'same_next_token': top_numpy == top_original,
        'max_absolute_logit_error': float(np.max(np.abs(got - ref))),
        'mean_absolute_logit_error': float(np.mean(np.abs(got - ref))),
        'top10_overlap': len(set(np.argsort(got)[-10:]) & set(np.argsort(ref)[-10:])),
    }
    return result
