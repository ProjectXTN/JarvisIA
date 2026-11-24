"""Executa coisas DENTRO da pasta do projeto (Fase 8, itens 64, 66 e 67).

  - venv próprio em <projeto>/.venv, criado com o mesmo Python do Jarvis;
  - instalar pacotes só no venv do projeto (pip) ou com npm na pasta;
  - rodar o app com tempo limite: se ainda estiver rodando no fim do tempo
    sem erro (janela, servidor), conta como "abriu";
  - build com PyInstaller (.exe) ou npm run build.
Nunca usa shell: cada comando é uma lista de argumentos, com cwd no projeto.
"""
import os
import re
import shutil
import subprocess
import sys

from brain.dev.projeto import OutsideProject

_PACKAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-\[\],]*([<>=!~]=?[A-Za-z0-9.*+\-]+)?$")
CREATE_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _venv_python(project):
    win = os.path.join(project.path, ".venv", "Scripts", "python.exe")
    unix = os.path.join(project.path, ".venv", "bin", "python")
    return win if os.name == "nt" else unix


def _run(cmd, cwd, timeout, env=None):
    try:
        done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace", creationflags=CREATE_FLAGS, env=env)
        return done.returncode, (done.stdout or "") + (done.stderr or "")
    except subprocess.TimeoutExpired as error:
        parts = [error.stdout or "", error.stderr or ""]  # podem vir em bytes no timeout
        out = "".join(p.decode("utf-8", "replace") if isinstance(p, bytes) else p for p in parts)
        return None, out
    except FileNotFoundError as error:
        return 127, str(error)


def _tail(text, limit=4000):
    text = text or ""
    return text if len(text) <= limit else "...\n" + text[-limit:]


def ensure_venv(project):
    python = _venv_python(project)
    if os.path.isfile(python):
        return python
    code, out = _run([sys.executable, "-m", "venv", ".venv"], project.path, 180)
    if code != 0 or not os.path.isfile(python):
        raise RuntimeError(f"Não consegui criar o venv: {_tail(out, 800)}")
    return python


def install(project, packages, manager="pip"):
    packages = [str(p).strip() for p in (packages or []) if str(p).strip()]
    bad = [p for p in packages if not _PACKAGE.match(p) or p.startswith("-")]
    if bad or not packages:
        return False, f"Nomes de pacote inválidos: {bad or 'nenhum'}"
    if manager == "npm":
        npm = shutil.which("npm")
        if not npm:
            return False, "npm não está instalado neste PC."
        code, out = _run([npm, "install", *packages], project.path, 600)
    else:
        python = ensure_venv(project)
        code, out = _run([python, "-m", "pip", "install", "--disable-pip-version-check", *packages],
                         project.path, 600)
    return code == 0, _tail(out)


def run(project, entry, args=(), timeout=25):
    """Roda o app. Devolve (situação, saída): 'ok', 'abriu' (seguia rodando) ou 'erro'."""
    target = project.resolve(entry)
    if not os.path.isfile(target):
        return "erro", f"Arquivo não existe: {entry}"
    rel = os.path.relpath(target, project.path)
    args = [str(a) for a in (args or [])][:10]
    if rel.endswith(".py"):
        cmd = [ensure_venv(project), rel, *args]
    elif rel.endswith((".js", ".mjs")):
        node = shutil.which("node")
        if not node:
            return "erro", "Node.js não está instalado neste PC."
        cmd = [node, rel, *args]
    else:
        return "erro", "Só sei rodar arquivos .py e .js."
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    code, out = _run(cmd, project.path, timeout, env)
    if code is None:
        last = out.strip().splitlines()[-1] if out.strip() else ""
        if "Traceback" in out or "Error" in last:
            return "erro", _tail(out)
        return "abriu", _tail(out) or "(seguia rodando quando o tempo acabou, sem erro)"
    return ("ok" if code == 0 else "erro"), _tail(out) or f"(saiu com código {code})"


def build(project, entry):
    """Gera o executável (.py com PyInstaller) ou roda npm run build."""
    if os.path.isfile(os.path.join(project.path, "package.json")):
        npm = shutil.which("npm")
        if not npm:
            return False, "npm não está instalado neste PC."
        code, out = _run([npm, "run", "build"], project.path, 900)
        return code == 0, _tail(out)
    target = project.resolve(entry)
    python = ensure_venv(project)
    ok, out = install(project, ["pyinstaller"])
    if not ok:
        return False, out
    rel = os.path.relpath(target, project.path)
    code, out = _run([python, "-m", "PyInstaller", "--noconfirm", "--onefile", rel], project.path, 900)
    return code == 0, _tail(out)


def open_folder(project):
    code = shutil.which("code")
    try:
        if code:
            subprocess.Popen([code, project.path], creationflags=CREATE_FLAGS)
        elif hasattr(os, "startfile"):
            os.startfile(project.path)
    except OSError as error:
        print(f"[DEV] Não consegui abrir a pasta: {error}")


__all__ = ["OutsideProject", "ensure_venv", "install", "run", "build", "open_folder"]
