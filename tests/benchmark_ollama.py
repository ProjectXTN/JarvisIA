"""Teste manual reproduzível: python -X utf8 -m tests.benchmark_ollama.

Use --num-gpu 0 para validar em CPU sem disputar a GPU com jogos.
Não altera a configuração do Jarvis. Tempos só são comparáveis sem outros usos da GPU.
"""
import argparse
import base64
import io
import json
import time
from pathlib import Path
import requests
from PIL import Image, ImageDraw
from core.settings import OLLAMA_HOST, OLLAMA_NUM_CTX
from brain.memory.memory import system_prompt


def run(model, num_gpu=None, note=''):
    options = {'temperature': 0.2, 'num_ctx': OLLAMA_NUM_CTX, 'num_predict': 192}
    if num_gpu is not None:
        options.update(num_gpu=num_gpu, draft_num_predict=0)
    records = []
    def ask(name, messages):
        started = time.perf_counter()
        try:
            response = requests.post(OLLAMA_HOST + '/api/chat', json={
                'model': model, 'messages': [{'role': 'system', 'content': system_prompt}] + messages,
                'think': False, 'stream': False, 'keep_alive': '30m', 'options': options}, timeout=(5,300))
            response.raise_for_status()
            data = response.json()
            record = {'case':name, 'seconds': round(time.perf_counter()-started,2),
                      'answer':data['message']['content'], 'done_reason':data.get('done_reason'),
                      'load_seconds': round(data.get('load_duration',0)/1e9,2),
                      'tokens_per_second': round(data.get('eval_count',0)/max(data.get('eval_duration',1)/1e9,0.001),2)}
        except Exception as error:
            record = {'case':name, 'seconds':round(time.perf_counter()-started,2),'error':str(error)}
        records.append(record)
        print(model,json.dumps(record,ensure_ascii=False),flush=True)
        return record.get('answer','')
    ask('portugues', [{'role':'user','content':'Em duas frases, explique por que o céu é azul.'}])
    ask('calculo', [{'role':'user','content':'Uma peça usa 35 g de filamento a R$ 109/kg e uma argola de R$ 0,447. Qual o custo total? Responda em uma frase.'}])
    ask('historico', [{'role':'user','content':'Minha peça se chama Aurora e tem 76 mm.'},
                     {'role':'assistant','content':'Certo, a peça Aurora tem 76 mm.'},
                     {'role':'user','content':'Qual é o nome e a medida da peça que acabei de mencionar?'}])
    ask('codigo', [{'role':'user','content':'Escreva só uma função Python chamada soma_pares(numeros) que soma os números pares da lista.'}])
    picture=Image.new('RGB',(224,224),'white')
    ImageDraw.Draw(picture).rectangle((40,40,184,184),fill='red')
    buffer=io.BytesIO();picture.save(buffer,format='PNG')
    ask('visao', [{'role':'user','content':'Qual a forma e a cor no centro desta imagem? Responda em uma frase.',
                    'images':[base64.b64encode(buffer.getvalue()).decode()]}])
    return {'model':model,'options':options,'note':note, 'results':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--models',nargs='+',default=['qwen3.8:27b','gemma4:26b'])
    parser.add_argument('--num-gpu',type=int)
    parser.add_argument('--output',default='logs/fase2_modelos.json')
    parser.add_argument('--note',default='',help='ex.: "jogo aberto durante o teste"')
    args=parser.parse_args()
    results=[]
    for model in args.models:
        results.append(run(model,args.num_gpu,args.note))
        Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
