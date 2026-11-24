"""Planejamento antes de programar (Fase 8+), como um engenheiro sênior faria.

1. Entende o pedido e, só se for essencial, faz até 3 perguntas.
2. Compara 2 ou 3 abordagens (tecnologia, estrutura) e recomenda uma.
3. Quebra o trabalho em 3 a 6 etapas, cada uma com um teste de "pronto".
O plano vira PLANO.md dentro da pasta do app, com as etapas marcadas.
"""
import json

import requests

from core.settings import DEV_MODEL, DEV_NUM_CTX, OLLAMA_HOST

PLAN_SYSTEM = (
    "Você é um engenheiro de software sênior planejando um app para Pedro, no Windows, antes "
    "de escrever código. Pense como em um bom projeto: entenda o pedido, veja as melhores "
    "maneiras de fazer, escolha a mais simples que atende bem e divida em etapas testáveis. "
    "Responda SÓ JSON neste formato:\n"
    '{"entendimento": "1 a 2 frases do que será feito", '
    '"perguntas": ["só dúvidas que mudam o resultado, com sugestão de resposta entre parênteses; '
    'no máximo 3; lista vazia se o pedido já basta"], '
    '"opcoes": [{"abordagem": "ex.: Python + Tkinter", "pros": "...", "contras": "..."}], '
    '"recomendacao": "qual abordagem e por quê, 1 frase", '
    '"etapas": [{"titulo": "curto", "descricao": "o que fazer", "teste": "como saber que ficou pronta"}], '
    '"pacotes": ["pacotes pip ou npm"], '
    '"arquivo_principal": "main.py"}\n'
    "Regras: 2 ou 3 opções; 3 a 6 etapas, a primeira deixa algo rodando e as seguintes "
    "acrescentam; prefira Python (Tkinter, CustomTkinter, Pygame, Flask) a menos que Pedro peça "
    "web ou outra linguagem; nada de pacotes desnecessários. Tudo em português."
)


def chat_json(system, user, model=DEV_MODEL):
    response = requests.post(f"{OLLAMA_HOST}/api/chat", json={
        "model": model, "stream": False, "think": False, "format": "json", "keep_alive": "10m",
        "options": {"num_ctx": DEV_NUM_CTX, "num_predict": 2048, "temperature": 0.3},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }, timeout=(5, 600))
    response.raise_for_status()
    try:
        return json.loads(response.json()["message"]["content"])
    except (ValueError, KeyError):
        return {}


def make_plan(request, project, answers=None, changes=None, llm=chat_json):
    """Plano em dict (normalizado). answers: [(pergunta, resposta)]; changes: pedido de ajuste."""
    user = f"Pedido de Pedro: {request}\n"
    files = project.files()
    if files and files not in (["README.md"], ["PLANO.md", "README.md"]):
        user += ("\nO app já existe; planeje a mudança em cima dele. Arquivos:\n" + "\n".join(files[:80]))
        try:
            user += "\n\nREADME:\n" + project.read("README.md")[:2500]
        except (FileNotFoundError, OSError):
            pass
    if answers:
        user += "\n\nRespostas do Pedro às suas perguntas (não pergunte de novo):\n" + "\n".join(
            f"- {q} -> {a or 'sem resposta: escolha o padrão mais razoável e diga qual'}" for q, a in answers)
    if changes:
        user += f"\n\nPedro pediu estas mudanças no plano anterior: {changes}\nNão faça novas perguntas."
    plan = llm(PLAN_SYSTEM, user) or {}
    return normalize(plan, no_questions=bool(answers or changes))


def normalize(plan, no_questions=False):
    def text(value, limit=400):
        return str(value or "").strip()[:limit]

    steps = []
    for item in (plan.get("etapas") or [])[:6]:
        if isinstance(item, dict) and text(item.get("titulo")):
            steps.append({"titulo": text(item.get("titulo"), 80), "descricao": text(item.get("descricao"), 600),
                          "teste": text(item.get("teste"), 300)})
    if not steps:
        steps = [{"titulo": "Versão completa", "descricao": "Construir o app pedido inteiro.",
                  "teste": "O app abre e faz o que foi pedido."}]
    options = [o for o in (plan.get("opcoes") or [])[:3] if isinstance(o, dict) and o.get("abordagem")]
    return {
        "entendimento": text(plan.get("entendimento")),
        "perguntas": [] if no_questions else [text(q, 250) for q in (plan.get("perguntas") or [])[:3] if text(q)],
        "opcoes": [{k: text(o.get(k), 200) for k in ("abordagem", "pros", "contras")} for o in options],
        "recomendacao": text(plan.get("recomendacao")),
        "etapas": steps,
        "pacotes": [text(p, 60) for p in (plan.get("pacotes") or [])[:15] if text(p)],
        "arquivo_principal": text(plan.get("arquivo_principal"), 80) or "main.py",
    }


def to_markdown(plan, request, done=0):
    lines = [f"# Plano\n\n**Pedido:** {request}\n", f"**Entendimento:** {plan['entendimento']}\n"]
    if plan["opcoes"]:
        lines.append("## Caminhos considerados\n")
        lines += [f"- **{o['abordagem']}** — prós: {o['pros']}; contras: {o['contras']}" for o in plan["opcoes"]]
        lines.append("")
    if plan["recomendacao"]:
        lines.append(f"**Escolha:** {plan['recomendacao']}\n")
    lines.append("## Etapas\n")
    for i, step in enumerate(plan["etapas"], 1):
        mark = "x" if i <= done else " "
        lines.append(f"- [{mark}] {i}. **{step['titulo']}** — {step['descricao']} _(pronto quando: {step['teste']})_")
    if plan["pacotes"]:
        lines.append(f"\n**Pacotes:** {', '.join(plan['pacotes'])}")
    return "\n".join(lines) + "\n"


def spoken_summary(plan):
    """Resumo curto para falar (o plano inteiro vai para a janela de texto)."""
    choice = plan["recomendacao"] or (plan["opcoes"][0]["abordagem"] if plan["opcoes"] else "")
    titles = ", ".join(s["titulo"] for s in plan["etapas"])
    return f"Plano pronto, em {len(plan['etapas'])} etapas: {titles}. {choice}".strip()
