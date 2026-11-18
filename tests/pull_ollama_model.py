"""Baixa modelos pelo servidor configurado, registrando progresso sem timeout total."""
import argparse
import requests
from core.settings import OLLAMA_HOST

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('model')
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    last = None
    with requests.post(OLLAMA_HOST + '/api/pull', json={'model': args.model, 'stream': True}, stream=True, timeout=(5,300)) as response:
        response.raise_for_status()
        import json
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get('error'):
                raise RuntimeError(data['error'])
            percent = int(100 * data.get('completed',0) / data['total']) if data.get('total') else None
            state = (data.get('status'), percent)
            if state != last:
                print(data.get('status'), f'{percent}%' if percent is not None else '', flush=True)
                last = state

    if args.benchmark:
        from tests.benchmark_ollama import run
        from pathlib import Path
        result = run(args.model)
        Path('logs/fase2_gemma.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
