"""Optional CPU Transformers oracle. Run in a separate process with ample RAM.

The result is an author-provided reference fixture for the same token IDs. It
never runs inside the learner's public check process.
"""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', required=True, type=Path)
    parser.add_argument('--input', required=True, type=Path,
                        help='JSON file with input_ids array')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--layers-output', type=Path,
                        help='Optional NPZ of last-token decoder output after each layer')
    parser.add_argument('--max-new-tokens', type=int, default=1)
    args = parser.parse_args()
    import torch
    from transformers import AutoModelForImageTextToText

    ids = json.loads(args.input.read_text())['input_ids']
    if not isinstance(ids, list) or not ids or len(ids) > 128:
        raise ValueError('Expected 1 to 128 token IDs')
    if not 1 <= args.max_new_tokens <= 16:
        raise ValueError('Expected 1 to 16 new tokens')
    model = AutoModelForImageTextToText.from_pretrained(
        str(args.weights), local_files_only=True, dtype=torch.bfloat16,
        device_map='cpu', low_cpu_mem_usage=True).eval()
    layer_vectors = {}
    hooks = []
    if args.layers_output:
        for index, layer in enumerate(model.model.language_model.layers):
            def capture(_module, _inputs, output, index=index):
                layer_vectors[f'layer_{index}'] = output[0, -1].float().cpu().numpy()
            hooks.append(layer.register_forward_hook(capture))
    with torch.inference_mode():
        output = model(input_ids=torch.tensor([ids], dtype=torch.long),
                       logits_to_keep=1, use_cache=False)
        for hook in hooks:
            hook.remove()
        logits = output.logits[0, -1].float().cpu().numpy().tolist()
        generated = []
        prefix = list(ids)
        for step in range(args.max_new_tokens):
            if step:
                output = model(input_ids=torch.tensor([prefix], dtype=torch.long),
                               logits_to_keep=1, use_cache=False)
            token = int(output.logits[0, -1].float().argmax())
            generated.append(token)
            prefix.append(token)
            if token in (248046, 248044):
                break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def digest(name):
        return hashlib.sha256((args.weights / name).read_bytes()).hexdigest()
    args.output.write_text(json.dumps({'input_ids': ids, 'logits': logits,
                                      'generated_ids': generated,
                                      'model': 'Qwen/Qwen3.6-27B',
                                      'config_sha256': digest('config.json'),
                                      'index_sha256': digest('model.safetensors.index.json'),
                                      'torch_version': torch.__version__,
                                      'reference': 'transformers CPU BF16'}))
    print(f'Wrote {len(logits)} reference logits to {args.output}')
    if args.layers_output:
        import numpy as np
        args.layers_output.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.layers_output, input_ids=np.asarray(ids, np.int64),
                            config_sha256=np.asarray(digest('config.json')),
                            index_sha256=np.asarray(digest('model.safetensors.index.json')),
                            **layer_vectors)
        print(f'Wrote {len(layer_vectors)} decoder layer vectors to {args.layers_output}')


if __name__ == '__main__':
    main()
