"""Read individual Hugging Face safetensors directly from a mounted Drive folder.

No checkpoint tensor is copied into this repository. A tensor is mapped from its
shard only when requested. BF16 values are expanded into float32 in bounded
row chunks for matrix multiplies.
"""

import json
import struct
from pathlib import Path

import numpy as np


_DTYPES = {"BF16": np.dtype('<u2'), "F32": np.dtype('<f4'), "F16": np.dtype('<f2')}


class WeightStore:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.index = json.loads((self.root / 'model.safetensors.index.json').read_text())['weight_map']
        self._headers = {}

    def _tensor_info(self, name):
        shard = self.index[name]
        if Path(shard).name != shard:
            raise ValueError('Unsafe shard name in index')
        path = self.root / shard
        if shard not in self._headers:
            with path.open('rb') as f:
                size = struct.unpack('<Q', f.read(8))[0]
                if size > 16_000_000:
                    raise ValueError('Safetensors header is too large')
                self._headers[shard] = (8 + size, json.loads(f.read(size)))
        offset, header = self._headers[shard]
        spec = header[name]
        dtype = _DTYPES.get(spec['dtype'])
        if dtype is None:
            raise ValueError(f"Unsupported tensor dtype: {spec['dtype']}")
        begin, end = spec['data_offsets']
        shape = tuple(spec['shape'])
        if end - begin != int(np.prod(shape)) * dtype.itemsize:
            raise ValueError(f'Invalid safetensors span for {name}')
        return path, offset + begin, shape, dtype, spec['dtype']

    def raw(self, name):
        path, offset, shape, dtype, _ = self._tensor_info(name)
        return np.memmap(path, dtype=dtype, mode='r', offset=offset, shape=shape)

    def array(self, name):
        raw = self.raw(name)
        kind = self._tensor_info(name)[4]
        if kind == 'BF16':
            return (np.asarray(raw, np.uint16).astype(np.uint32) << 16).view(np.float32)
        return np.asarray(raw, dtype=np.float32)

    def rows(self, name, row_ids):
        raw = self.raw(name)[np.asarray(row_ids, dtype=np.int64)]
        if self._tensor_info(name)[4] == 'BF16':
            return (np.asarray(raw, np.uint16).astype(np.uint32) << 16).view(np.float32)
        return np.asarray(raw, dtype=np.float32)

    def matmul(self, x, name, block_rows=512, linear=None):
        """Compute x @ weight.T while expanding at most block_rows BF16 rows."""
        raw = self.raw(name)
        out = np.empty((*x.shape[:-1], raw.shape[0]), np.float32)
        kind = self._tensor_info(name)[4]
        for start in range(0, raw.shape[0], block_rows):
            piece = raw[start:start + block_rows]
            if kind == 'BF16':
                w = (np.asarray(piece, np.uint16).astype(np.uint32) << 16).view(np.float32)
            else:
                w = np.asarray(piece, np.float32)
            out[..., start:start + len(piece)] = (
                linear(x, w) if linear is not None else np.matmul(x, w.T))
        return out
