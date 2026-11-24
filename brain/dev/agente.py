"""O programador do Jarvis (Fase 8, itens 63, 65, 66, 67 e 68).

Um laço com o modelo de código (DEV_MODEL, padrão qwen3.8:27b) e ferramentas
que só mexem na pasta do projeto: criar/ler/listar arquivos, instalar pacotes
e rodar o app (essas duas só com a permissão que o Pedro deu por voz). O modelo
escreve, roda, lê o erro e corrige; depois de 5 execuções com erro, tem que
parar e explicar onde travou. O código nunca é falado: no fim o Jarvis diz só
o que fez, onde salvou e como rodar.
"""
import json
import threading
import time

import requests

from brain.dev import executor
from brain.dev.projeto import OutsideProject
from core.settings import DEV_MAX_STEPS, DEV_MODEL, DEV_NUM_CTX, OLLAMA_HOST

MAX_FAILED_RUNS = 5

SYSTEM = (
    "Você é um programador sênior trabalhando para Pedro, no Windows. Construa o app pedido "
    "COMPLETO e funcionando, em vários arquivos se fizer sentido, usando as ferramentas: "
    "criar_arquivo, ler_arquivo, listar_arquivos, instalar_pacotes, rodar_app e terminar. "
    "Regras: prefira Python (arquivo principal main.py) a menos que Pedro peça web/JavaScript; "
    "escreva requirements.txt quando usar pacotes; código limpo, comentado em português, sem "
    "partes faltando nem 'TODO'. Depois de escrever, instale os pacotes e rode o app para testar; "
    "se der erro, leia a mensagem, corrija os arquivos e rode de novo. Apps com janela ou "
    "servidor que continuam abertos no fim do teste contam como funcionando. Se depois de "
    f"{MAX_FAILED_RUNS} execuções com erro não conseguir, pare e explique onde travou. "
    "Termine SEMPRE chamando terminar, com um resumo curto em português (2 frases, sem código) "
    "e como rodar. Nunca escreva fora da pasta do projeto."
)


def _tool(name, description, properties=None, required=()):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {}, "required": list(required)}}}


TOOLS = [
    _tool("criar_arquivo", "Cria ou substitui um arquivo do projeto (caminho relativo).",
          {"caminho": {"type": "string"}, "conteudo": {"type": "string"}}, ["caminho", "conteudo"]),
    _tool("ler_arquivo", "Lê um arquivo do projeto.", {"caminho": {"type": "string"}}, ["caminho"]),
    _tool("listar_arquivos", "Lista os arquivos do projeto."),
    _tool("instalar_pacotes", "Instala pacotes no ambiente do projeto.",
          {"pacotes": {"type": "array", "items": {"type": "string"}},
           "gerenciador": {"type": "string", "enum": ["pip", "npm"]}}, ["pacotes"]),
    _tool("rodar_app", "Roda um arquivo .py ou .js do projeto e devolve a saída.",
          {"arquivo": {"type": "string"}, "argumentos": {"type": "array", "items": {"type": "string"}}},
          ["arquivo"]),
    _tool("terminar", "Encerra o trabalho.",
          {"resumo": {"type": "string", "description": "2 frases, sem código"},
           "como_rodar": {"type": "string"},
           "arquivo_principal": {"type": "string"},
           "funcionou": {"type": "boolean"}}, ["resumo", "funcionou"]),
]


def chat(messages):
    response = requests.post(f"{OLLAMA_HOST}/api/chat", json={
        "model": DEV_MODEL, "messages": messages, "tools": TOOLS, "stream": False, "think": False,
        "keep_alive": "10m", "options": {"num_ctx": DEV_NUM_CTX, "num_predict": 8192, "temperature": 0.2},
    }, timeout=(5, 900))
    response.raise_for_status()
    return response.json()["message"]


class Session:
    """Um trabalho num projeto. allow_run: Pedro deixou instalar pacotes e rodar."""

    def __init__(self, project, request, allow_run=True, llm=chat, log=print):
        self.project, self.request, self.allow_run = project, request, allow_run
        self.llm, self.log = llm, log
        self.failed_runs = 0
        self.last_run = None
        self.result = None

    def _context(self):
        files = self.project.files()
        text = f"Projeto: {self.project.path}\nPedido de Pedro: {self.request}\n"
        if files and files != ["README.md"]:
            text += "Este projeto já existe; altere em cima do que existe. Arquivos:\n" + "\n".join(files)
            text += "\n\nREADME atual:\n" + self.project.read("README.md")[:3000]
        if not self.allow_run:
            text += "\nPedro NÃO autorizou instalar pacotes nem rodar o app: só escreva os arquivos."
        return text

    def call(self, name, args):
        try:
            if name == "criar_arquivo":
                rel = self.project.write(args.get("caminho"), args.get("conteudo", ""))
                self.log(f"[DEV] Arquivo: {rel}")
                return f"Salvo: {rel}"
            if name == "ler_arquivo":
                return self.project.read(args.get("caminho"))
            if name == "listar_arquivos":
                return "\n".join(self.project.files()) or "(vazio)"
            if name in ("instalar_pacotes", "rodar_app") and not self.allow_run:
                return "Pedro não autorizou instalar nem rodar. Só escreva os arquivos e termine."
            if name == "instalar_pacotes":
                packages = args.get("pacotes") or []
                if isinstance(packages, str):
                    packages = packages.replace(",", " ").split()
                ok, out = executor.install(self.project, packages, args.get("gerenciador") or "pip")
                self.log(f"[DEV] Instalar {packages}: {'ok' if ok else 'falhou'}")
                return ("Instalado.\n" if ok else "Falhou:\n") + out
            if name == "rodar_app":
                status, out = executor.run(self.project, args.get("arquivo"), args.get("argumentos") or [])
                self.last_run = status
                self.log(f"[DEV] Rodar {args.get('arquivo')}: {status}")
                if status == "erro":
                    self.failed_runs += 1
                    left = MAX_FAILED_RUNS - self.failed_runs
                    hint = (f"\n(Tentativas com erro: {self.failed_runs}/{MAX_FAILED_RUNS}.)" if left > 0 else
                            "\nLimite de tentativas atingido: chame terminar com funcionou=false e explique onde travou.")
                    return f"ERRO:\n{out}{hint}"
                return f"Situação: {status}\n{out}"
        except (OutsideProject, FileNotFoundError, ValueError, RuntimeError) as error:
            return f"Erro: {error}"
        return f"Ferramenta desconhecida: {name}"

    @staticmethod
    def _compact(message):
        """Tira o conteúdo dos arquivos já salvos do histórico (economiza contexto)."""
        for call in message.get("tool_calls") or []:
            fn = call.get("function", {})
            args = fn.get("arguments")
            if fn.get("name") == "criar_arquivo" and isinstance(args, dict) and len(args.get("conteudo", "")) > 400:
                lines = args["conteudo"].count("\n") + 1
                fn["arguments"] = dict(args, conteudo=f"<{lines} linhas salvas; use ler_arquivo para ver>")
        return message

    def work(self):
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": self._context()}]
        for step in range(DEV_MAX_STEPS):
            message = self.llm(messages)
            calls = message.get("tool_calls") or []
            if not calls:
                messages.append({"role": "assistant", "content": message.get("content", "")})
                messages.append({"role": "user", "content": "Continue usando as ferramentas e termine com terminar."})
                continue
            results = []
            for call in calls:
                fn = call.get("function", {})
                name, args = fn.get("name"), fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                if name == "terminar":
                    ok = bool(args.get("funcionou")) and (self.last_run in ("ok", "abriu") or not self.allow_run)
                    self.result = {"ok": ok, "resumo": str(args.get("resumo") or "").strip(),
                                   "como_rodar": str(args.get("como_rodar") or "").strip(),
                                   "principal": str(args.get("arquivo_principal") or "main.py").strip(),
                                   "passos": step + 1}
                    return self.result
                results.append({"role": "tool", "tool_name": name, "content": self.call(name, args)[:6000]})
            messages.append(self._compact(dict(message, role="assistant")))
            messages.extend(results)
            if self.failed_runs > MAX_FAILED_RUNS:
                break
        self.result = {"ok": False, "resumo": "Não terminei: passei do limite de tentativas.",
                       "como_rodar": "", "principal": "main.py", "passos": DEV_MAX_STEPS}
        return self.result


# ------------------------------------------------- execução em segundo plano
_busy = threading.Lock()


def run_in_background(project, request, allow_run, build, say, on_done=None):
    """Roda a sessão sem travar a voz e avisa no fim. False se já há uma em andamento."""
    if not _busy.acquire(blocking=False):
        return False

    def job():
        started = time.monotonic()
        try:
            session = Session(project, request, allow_run)
            result = session.work()
            built = ""
            if result["ok"] and build:
                ok, out = executor.build(project, result["principal"])
                built = " Gerei o executável na pasta dist." if ok else " O executável não saiu; deixei o erro no log."
                if not ok:
                    print(f"[DEV] Build falhou:\n{out}")
            project.add_history(request, result["resumo"], result["ok"], result["principal"])
            minutes = (time.monotonic() - started) / 60
            print(f"[DEV] {project.name}: {'ok' if result['ok'] else 'travou'} em {minutes:.1f} min, "
                  f"{result['passos']} passos.")
            if result["ok"]:
                executor.open_folder(project)
                message = (f"Terminei o app {project.spoken}. {result['resumo']}{built} "
                           f"{('Para rodar: ' + result['como_rodar']) if result['como_rodar'] else ''}")
            else:
                message = f"Não consegui deixar o app {project.spoken} funcionando. {result['resumo']}"
            say(message.strip())
        except Exception as error:
            print(f"[DEV] Erro no modo programador: {error}")
            say(f"Tive um problema programando o app {project.spoken}: o modelo de código não respondeu.")
        finally:
            _busy.release()
            if on_done:
                on_done()

    threading.Thread(target=job, name=f"dev-{project.name}", daemon=True).start()
    return True


def busy():
    return _busy.locked()
