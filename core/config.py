"""Estado por pedido.

IS_API_REQUEST diz se o comando atual veio da API (responder em texto) ou da
voz (falar). Antes era uma variável global: um pedido da API ligava o modo
API e, enquanto isso, o Jarvis de voz também parava de falar. Agora o valor
vale só para a thread que atende o pedido.
"""

import threading
from contextlib import contextmanager

_state = threading.local()

# Ligado quando o modelo de conversa terminou de carregar na abertura (ou falhou).
# Depois de reiniciar o PC o Ollama abre frio e o gemma4 leva um tempo para
# sair do disco; enquanto isso, quem precisa do Ollama espera aqui.
MODEL_READY = threading.Event()
# Hora (time.monotonic) do último pedido do Pedro; a rotina de fundo espera ele parar
LAST_ACTIVITY = 0.0


def __getattr__(name):
    if name == "IS_API_REQUEST":
        return getattr(_state, "api", False)
    raise AttributeError(name)


@contextmanager
def api_request():
    """Marca a thread atual como pedido da API até o fim do bloco."""
    previous = getattr(_state, "api", False)
    _state.api = True
    try:
        yield
    finally:
        _state.api = previous
