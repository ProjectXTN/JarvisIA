"""Pastas de projeto do modo programador (Fase 8, itens 62 e 69).

Cada app fica em APPS_DIR/<nome> (padrão C:\\Projetos\\jarvis_apps), com:
  - README.md: o pedido do Pedro, como rodar e o histórico de mudanças;
  - .jarvis/historico.json: cada pedido e o resumo do que foi feito.
Todo caminho passa por resolve(): nada sai da pasta do projeto.
"""
import json
import os
import re
import unicodedata
from datetime import datetime

from core.settings import APPS_DIR

MAX_FILE = 200_000
SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git", "build", "dist", ".jarvis"}


class OutsideProject(PermissionError):
    pass


def slug(name):
    name = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return name[:40] or "app"


class Project:
    def __init__(self, name, base=None):
        self.name = slug(name)
        self.base = os.path.abspath(base or APPS_DIR)
        self.path = os.path.join(self.base, self.name)

    # ------------------------------------------------------------ caminhos
    def resolve(self, relative):
        relative = str(relative or "").replace("\\", "/").strip()
        if not relative or relative.startswith("/") or re.match(r"^[a-zA-Z]:", relative):
            raise OutsideProject(f"Use um caminho relativo dentro do projeto: {relative!r}")
        full = os.path.abspath(os.path.join(self.path, relative))
        if os.path.commonpath([full, self.path]) != self.path or full == self.path:
            raise OutsideProject(f"Caminho fora do projeto: {relative!r}")
        if ".jarvis" in os.path.relpath(full, self.path).split(os.sep):
            raise OutsideProject("A pasta .jarvis é do Jarvis.")
        return full

    @property
    def spoken(self):
        """Nome para falar ("lista_de_tarefas" -> "lista de tarefas")."""
        return self.name.replace("_", " ")

    def exists(self):
        return os.path.isdir(self.path)

    def create(self, request):
        os.makedirs(os.path.join(self.path, ".jarvis"), exist_ok=True)
        if not os.path.exists(os.path.join(self.path, "README.md")):
            self.write("README.md", f"# {self.name}\n\n## Pedido do Pedro\n\n{request}\n")
        return self.path

    # ------------------------------------------------------------ arquivos
    def write(self, relative, content):
        content = str(content or "")
        if len(content) > MAX_FILE:
            raise ValueError("Arquivo grande demais.")
        full = self.resolve(relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return os.path.relpath(full, self.path)

    def read(self, relative, limit=60_000):
        full = self.resolve(relative)
        if not os.path.isfile(full):
            raise FileNotFoundError(relative)
        with open(full, encoding="utf-8", errors="replace") as f:
            return f.read(limit)

    def files(self, limit=300):
        found = []
        for root, dirs, names in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in names:
                found.append(os.path.relpath(os.path.join(root, name), self.path).replace("\\", "/"))
                if len(found) >= limit:
                    return sorted(found)
        return sorted(found)

    # ------------------------------------------------------------ histórico
    def _history_path(self):
        return os.path.join(self.path, ".jarvis", "historico.json")

    def history(self):
        try:
            with open(self._history_path(), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return []

    def main_file(self):
        """Arquivo principal: o que o modelo indicou, senão main.py/app.py/index.js."""
        for item in reversed(self.history()):
            if item.get("principal") and os.path.isfile(os.path.join(self.path, item["principal"])):
                return item["principal"]
        for name in ("main.py", "app.py", "index.js", "server.js"):
            if os.path.isfile(os.path.join(self.path, name)):
                return name
        py = [f for f in self.files() if f.endswith(".py")]
        return py[0] if py else None

    def add_history(self, request, summary, ok, principal=None):
        items = self.history()
        items.append({"quando": datetime.now().strftime("%Y-%m-%d %H:%M"), "pedido": request,
                      "resumo": summary, "funcionou": ok, "principal": principal})
        os.makedirs(os.path.dirname(self._history_path()), exist_ok=True)
        with open(self._history_path(), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        readme = self.read("README.md") if os.path.exists(os.path.join(self.path, "README.md")) else f"# {self.name}\n"
        if "## Histórico" not in readme:
            readme += "\n## Histórico\n"
        readme += f"\n- {items[-1]['quando']}: {request} — {summary}\n"
        self.write("README.md", readme)


def list_projects(base=None):
    base = os.path.abspath(base or APPS_DIR)
    if not os.path.isdir(base):
        return []
    return sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n, ".jarvis")))


def find_project(name, base=None):
    """Acha um projeto pelo nome falado ("o app da calculadora" -> calculadora)."""
    wanted = slug(name)
    names = list_projects(base)
    if wanted in names:
        return Project(wanted, base)
    words = set(wanted.split("_")) - {"app", "o", "a", "do", "da", "de"}
    best = max(names, key=lambda n: len(words & set(n.split("_"))), default=None)
    if best and words & set(best.split("_")):
        return Project(best, base)
    return None
