"""Ferramentas que o modelo pode chamar (Fase 4).

Cada ferramenta tem nome, descrição (é o que o modelo lê para decidir),
parâmetros (JSON Schema) e a função que executa. Dois tipos:

- informação (for_model=True): devolve um texto que volta para o modelo
  formular a resposta falada (busca, notícias, clima, memória...);
- ação (for_model=False): faz algo e confirma em voz alta por conta própria
  (abrir programa, música, imagem...).

Os comandos antigos são reaproveitados; os imports ficam dentro das funções
para não criar ciclos de importação.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Tool:
    name: str
    description: str
    run: callable
    properties: dict = field(default_factory=dict)
    required: list = field(default_factory=list)
    for_model: bool = False

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": self.required,
                },
            },
        }


def _text(kind="string", description="", enum=None):
    prop = {"type": kind, "description": description}
    if enum:
        prop["enum"] = enum
    return prop


# ------------------------------------------------------------- informação
def buscar_na_internet(consulta):
    from brain.websearch.websearch import search_web

    text, sources = search_web(consulta)
    return f"Resultados da busca por '{consulta}':\n{text}\n\nFontes: {sources}"


def buscar_noticias(assunto):
    from brain.websearch.news import fetch_news

    items = fetch_news(assunto)
    if not items:
        return f"Nenhuma notícia encontrada sobre '{assunto}'."
    return "\n\n".join(
        f"Título: {i['title']}\nResumo: {i['description']}\n"
        f"Data: {i['date'] or 'não informada'}\nFonte: {i['url']}"
        for i in items
    )


def previsao_do_tempo(cidade="", periodo="agora"):
    from brain.weatherAPI.weatherAPI import HOME_LOCATION, get_weather, resolve_location

    location = resolve_location(cidade) if cidade else HOME_LOCATION
    if location is None:
        return f"A cidade '{cidade}' não foi encontrada."
    forecast = periodo != "agora"
    return get_weather(location, forecast=forecast, next_week=periodo == "proxima_semana")


def data_e_hora():
    from brain.pipeline.super_jarvis import _WEEKDAYS

    now = datetime.now()
    day = _WEEKDAYS["pt"][now.weekday()]
    return f"Agora: {day}, {now.strftime('%d/%m/%Y, %H:%M')} (horário local de Pedro)."


def status_do_computador():
    from commands.commands_systeme import system_usage

    return system_usage()


def consultar_memoria(assunto):
    from brain.learning.consult_memory import consultar_memoria as consult

    result = consult(assunto.lower().strip())
    if not result:
        return f"Não há nada guardado sobre '{assunto}'."
    info, source, date = result
    return f"Guardado sobre '{assunto}': {info} (fonte: {source}, em {date})."


def listar_memorias():
    from brain.learning.list_memory import listar_memoria

    titles = listar_memoria()
    return "Assuntos guardados: " + (", ".join(titles) if titles else "nenhum ainda.")


def consultar_emocoes(emocao, periodo=""):
    from brain.learning.consult_emotions import query_emotions
    from brain.learning.interpret_date import interpret_date_range
    from brain.learning.normalize_emotions import normalize_emotion

    emotion = normalize_emotion(emocao)
    start, end = interpret_date_range(periodo or "")
    rows = query_emotions(emotion, start, end)
    if not rows:
        return f"Nenhuma lembrança com a emoção '{emotion}' nesse período."
    return "Lembranças: " + "; ".join(f"{r[0]} (em {r[2]})" for r in rows)


# ------------------------------------------------------------------ ação
def _say(text):
    from brain.audio import say

    say(text)


PROGRAMS = ["steam", "discord", "navegador", "vscode"]


def abrir_programa(programa):
    programa = programa.lower().strip()
    if programa in ("steam", "discord"):
        from commands.comandos_software import open_software

        open_software(programa)
    elif programa == "navegador":
        from brain.system import open_browser

        _say("Abrindo o navegador.")
        open_browser()
    elif programa == "vscode":
        from brain.system import open_vscode

        _say("Abrindo o VS Code.")
        open_vscode()
    else:
        _say(f"Ainda não sei abrir o {programa}.")
    return f"abrir_programa({programa})"


def abrir_site(endereco):
    """Abre um site no navegador padrão. Só http/https."""
    import webbrowser
    from urllib.parse import urlparse

    url = endereco.strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or "." not in parsed.netloc:
        _say("Não entendi o endereço do site.")
        return f"abrir_site({endereco}): endereço inválido"
    host = parsed.netloc.removeprefix("www.")
    is_search = "search" in parsed.path or "results" in parsed.path or "q=" in parsed.query
    _say(f"Abrindo a busca em {host}." if is_search else f"Abrindo {host}.")
    from brain.system import open_in_chrome

    open_in_chrome(url)
    return f"abrir_site({url})"


def pesquisar_no_google(consulta):
    """Abre a página de resultados do Google no Chrome, para Pedro ver."""
    from brain.system import search_google

    _say(f"Abrindo a pesquisa no Google sobre {consulta}.")
    search_google(consulta)
    return f"pesquisar_no_google({consulta})"


def tocar_no_youtube(busca):
    """Acha o primeiro vídeo da busca e abre a página dele (o vídeo começa a tocar)."""
    import re
    import webbrowser
    from urllib.parse import quote_plus

    import requests

    search_url = "https://www.youtube.com/results?search_query=" + quote_plus(busca)
    video_id = None
    try:
        page = requests.get(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0",
                     "Accept-Language": "pt-BR,pt;q=0.9"},
            # Sem estes cookies, na Europa o YouTube responde com a página de consentimento
            cookies={"CONSENT": "YES+cb", "SOCS": "CAI"},
            timeout=6,
        ).text
        match = re.search(r'"videoId":"([\w-]{11})"', page)
        video_id = match.group(1) if match else None
    except Exception as error:
        print(f"[YOUTUBE] Busca falhou: {error}")
    from brain.media_window import open_media

    # Sempre na mesma janela: o vídeo novo substitui o anterior
    if video_id:
        _say(f"Tocando {busca} no YouTube.")
        open_media(f"https://www.youtube.com/watch?v={video_id}")
        return f"tocar_no_youtube({busca}): {video_id}"
    _say("Não achei o vídeo direto; abri a busca no YouTube.")
    open_media(search_url)
    return f"tocar_no_youtube({busca}): só a busca"


def abrir_pasta(nome):
    from brain.system import open_folder

    _say(open_folder(nome))
    return f"abrir_pasta({nome})"


def musica(acao, busca=""):
    from commands import commands_music as m

    actions = {
        "pausar": m.pause_music, "proxima": m.next_music,
        "anterior": m.previous_music, "biblioteca": m.play_music,
    }
    if acao == "tocar" and busca:
        m.search_and_play_apple_music(busca)
    elif acao in actions:
        actions[acao](None)
    else:
        m.play_music(None)
    return f"musica({acao}, {busca})"


def criar_imagem(descricao):
    from commands.commands_dispatch_image import dispatch_image_command

    dispatch_image_command(f"crie uma imagem de {descricao}")
    return f"criar_imagem({descricao})"


def descrever_imagem(arquivo, pergunta=""):
    from jarvis_vision import describe_image

    folder = os.path.expanduser("~/Pictures")
    for ext in ("", ".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(folder, arquivo + ext)
        if os.path.isfile(path):
            _say("Analisando a imagem.")
            description = describe_image(path, pergunta)
            _say(description or "Não consegui analisar a imagem.")
            return f"descrever_imagem({arquivo})"
    _say(f"Não encontrei a imagem {arquivo} na sua pasta Imagens.")
    return f"descrever_imagem({arquivo}): não encontrada"


def memorizar(assunto, informacao):
    from brain.learning.insert_memory import insert_memory

    ok = insert_memory(assunto.lower().strip(), informacao, "Pedro",
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    _say(f"Guardei isso sobre {assunto}." if ok else "Não consegui guardar isso.")
    return f"memorizar({assunto})"


def esquecer(assunto):
    from brain.learning.clean_memory import apagar_memoria

    ok = apagar_memoria(assunto.lower().strip())
    _say(f"Esqueci o que sabia sobre {assunto}." if ok else f"Não encontrei nada sobre {assunto}.")
    return f"esquecer({assunto})"


def aprender_da_internet(assunto):
    from commands.commands_memorie import learn_from_web

    learn_from_web(f"aprenda sobre {assunto}")
    return f"aprender_da_internet({assunto})"


def registrar_emocao(evento, emocao, data=""):
    from brain.learning.insert_emotion import register_emotion
    from brain.learning.normalize_emotions import normalize_emotion

    emotion = normalize_emotion(emocao)
    ok = register_emotion(evento, emotion, data or datetime.now().strftime("%Y-%m-%d"), None)
    _say(f"Lembrança registrada com a emoção {emotion}." if ok else "Não consegui registrar essa lembrança.")
    return f"registrar_emocao({evento}, {emotion})"


def registrar_meu_dia():
    from commands.commands_reflection import iniciar_reflexao

    iniciar_reflexao("")
    return "registrar_meu_dia()"


def traduzir_legenda(arquivo, idioma):
    from commands.commands_traduction import execute_subtitle_translation

    execute_subtitle_translation(f"traduzir arquivo {arquivo} para {idioma}")
    return f"traduzir_legenda({arquivo}, {idioma})"


def avatar(acao):
    from brain import avatar as av

    if acao == "esconder":
        av.hide()
        _say("Avatar oculto.")
    else:
        _say("Avatar na tela." if av.show() else "Não consegui abrir o avatar.")
    return f"avatar({acao})"


TOOLS = [
    # informação
    Tool("buscar_na_internet",
         "Pesquisa na internet para VOCÊ ler e responder em voz. Use para fatos atuais ou "
         "que podem ter mudado: versões e lançamentos, preços, eventos, pessoas e cargos "
         "atuais, guias de jogos. Escreva a consulta completa, com o assunto da conversa. "
         "Se Pedro quiser VER a pesquisa (abrir o Chrome/navegador e pesquisar, mostrar "
         "na tela), use pesquisar_no_google.",
         buscar_na_internet, {"consulta": _text(description="O que pesquisar")}, ["consulta"], True),
    Tool("buscar_noticias", "Manchetes recentes sobre um assunto (notícias, boatos, acontecimentos do dia).",
         buscar_noticias, {"assunto": _text(description="Assunto das notícias")}, ["assunto"], True),
    Tool("previsao_do_tempo", "Clima e previsão do tempo. Sem cidade, usa a cidade de Pedro.",
         previsao_do_tempo,
         {"cidade": _text(description="Cidade; vazio para a cidade de Pedro"),
          "periodo": _text(description="Quando", enum=["agora", "amanha", "proximos_dias", "proxima_semana"])},
         [], True),
    Tool("data_e_hora", "Data e hora atuais de Pedro.", data_e_hora, for_model=True),
    Tool("status_do_computador", "Uso de CPU, memória RAM e disco do computador.",
         status_do_computador, for_model=True),
    Tool("consultar_memoria", "O que Jarvis guardou sobre um assunto ('o que você sabe sobre X').",
         consultar_memoria, {"assunto": _text()}, ["assunto"], True),
    Tool("listar_memorias", "Lista os assuntos que Jarvis já guardou.", listar_memorias, for_model=True),
    Tool("consultar_emocoes", "Lembranças de Pedro ligadas a uma emoção ('o que me deixou feliz esta semana').",
         consultar_emocoes,
         {"emocao": _text(description="Ex.: feliz, triste, estressado"),
          "periodo": _text(description="Ex.: hoje, esta semana, este mês")},
         ["emocao"], True),
    # ação
    Tool("abrir_programa", "Abre um programa no computador.", abrir_programa,
         {"programa": _text(enum=PROGRAMS)}, ["programa"]),
    Tool("abrir_site",
         "Abre um site no navegador. Use o endereço completo, por exemplo "
         "https://www.youtube.com. Para pesquisar dentro de um site, monte a URL de busca "
         "dele, por exemplo https://www.youtube.com/results?search_query=queen.",
         abrir_site, {"endereco": _text(description="URL do site")}, ["endereco"]),
    Tool("pesquisar_no_google",
         "Abre no Chrome a página de resultados do Google, para Pedro ver. Use quando ele "
         "pedir para abrir o Chrome/navegador e pesquisar, ou para mostrar a pesquisa na "
         "tela. Já abre o Chrome sozinha: não chame abrir_programa antes.",
         pesquisar_no_google, {"consulta": _text(description="O que pesquisar no Google")}, ["consulta"]),
    Tool("tocar_no_youtube",
         "Toca um vídeo ou música no YouTube: procura e abre direto o primeiro vídeo "
         "encontrado. Use quando Pedro quer assistir ou ouvir algo no YouTube.",
         tocar_no_youtube, {"busca": _text(description="Vídeo, música ou artista")}, ["busca"]),
    Tool("abrir_pasta", "Abre uma pasta do computador pelo nome (ex.: Downloads, Documentos).",
         abrir_pasta, {"nome": _text()}, ["nome"]),
    Tool("musica", "Controla a música no Apple Music: tocar uma busca, pausar, próxima, anterior ou abrir a biblioteca.",
         musica,
         {"acao": _text(enum=["tocar", "pausar", "proxima", "anterior", "biblioteca"]),
          "busca": _text(description="Música, artista ou álbum, quando a ação é tocar")},
         ["acao"]),
    Tool("criar_imagem", "Gera uma imagem a partir de uma descrição.", criar_imagem,
         {"descricao": _text()}, ["descricao"]),
    Tool("descrever_imagem", "Analisa uma imagem da pasta Imagens de Pedro pelo nome do arquivo.",
         descrever_imagem,
         {"arquivo": _text(description="Nome do arquivo, sem a pasta"), "pergunta": _text()}, ["arquivo"]),
    Tool("memorizar", "Guarda uma informação que Pedro pediu para lembrar ('aprenda que X é Y').",
         memorizar, {"assunto": _text(), "informacao": _text()}, ["assunto", "informacao"]),
    Tool("esquecer", "Apaga o que Jarvis guardou sobre um assunto.", esquecer,
         {"assunto": _text()}, ["assunto"]),
    Tool("aprender_da_internet", "Pesquisa um assunto e guarda o resumo, quando Pedro pede para aprender ou estudar algo.",
         aprender_da_internet, {"assunto": _text()}, ["assunto"]),
    Tool("registrar_emocao", "Registra um acontecimento e a emoção que causou em Pedro.",
         registrar_emocao,
         {"evento": _text(), "emocao": _text(), "data": _text(description="AAAA-MM-DD; vazio para hoje")},
         ["evento", "emocao"]),
    Tool("registrar_meu_dia", "Conversa guiada para registrar como foi o dia de Pedro.", registrar_meu_dia),
    Tool("traduzir_legenda", "Traduz um arquivo de legenda (.srt/.ass) da pasta Documentos.",
         traduzir_legenda, {"arquivo": _text(), "idioma": _text()}, ["arquivo", "idioma"]),
    Tool("avatar", "Mostra ou esconde a janela do avatar do Jarvis.", avatar,
         {"acao": _text(enum=["mostrar", "esconder"])}, ["acao"]),
]

BY_NAME = {tool.name: tool for tool in TOOLS}


def schemas():
    return [tool.schema() for tool in TOOLS]


def run_tool(name, arguments):
    """Executa uma ferramenta. Devolve (texto, para_o_modelo). Erros viram texto."""
    tool = BY_NAME.get(name)
    if tool is None:
        return f"Ferramenta desconhecida: {name}.", True
    if isinstance(arguments, str):
        import json

        try:
            arguments = json.loads(arguments or "{}")
        except ValueError:
            arguments = {}
    arguments = {k: v for k, v in (arguments or {}).items() if k in tool.properties}
    print(f"[FERRAMENTA] {name}({', '.join(f'{k}={v!r}' for k, v in arguments.items())})")
    try:
        result = tool.run(**arguments)
    except Exception as error:
        print(f"[FERRAMENTA] {name} falhou: {error}")
        return f"A ferramenta {name} falhou: {error}", True
    return (str(result) if result is not None else ""), tool.for_model
