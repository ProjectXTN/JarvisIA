"""Limites de segurança do que o Jarvis faz sozinho (Fase 7, item 60).

Tudo que roda sem o Pedro pedir (estudo autônomo, reflexão, iniciativa) só pode
LER: buscar na internet, ler páginas, consultar a própria memória. Nada de
abrir programas, executar comandos, comprar, enviar mensagens ou apagar.
O código autônomo chama allowed() antes de cada ação e autonomous_tool() em
vez de run_tool().
"""

# Ferramentas que o Jarvis pode usar por conta própria
READ_ONLY_TOOLS = frozenset({
    "buscar_na_internet", "buscar_noticias", "previsao_do_tempo", "data_e_hora",
    "consultar_memoria", "listar_memorias", "consultar_documentos", "consultar_emocoes",
})
# Domínios que o estudo autônomo não lê (login, compra, redes privadas)
BLOCKED_HOSTS = ("localhost", "127.0.0.1", "192.168.", "10.", "paypal.", "bank", "banco")


class NotAllowed(PermissionError):
    pass


def allowed(tool_name):
    return tool_name in READ_ONLY_TOOLS


def check_url(url):
    low = (url or "").lower()
    if not low.startswith(("http://", "https://")):
        raise NotAllowed(f"Endereço não permitido: {url}")
    host = low.split("//", 1)[1].split("/", 1)[0]
    if any(host.startswith(b) or b in host for b in BLOCKED_HOSTS):
        raise NotAllowed(f"Endereço bloqueado para estudo autônomo: {host}")
    return url


def autonomous_tool(name, arguments):
    """Executa uma ferramenta em nome do próprio Jarvis, só se for de leitura."""
    if not allowed(name):
        raise NotAllowed(f"Ferramenta '{name}' não pode ser usada sem o Pedro pedir.")
    from brain.tools import run_tool

    return run_tool(name, arguments)
