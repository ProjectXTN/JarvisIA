"""Fala em fluxo: a primeira frase toca enquanto o resto ainda é gerado.

Três etapas em paralelo:
  1. divisão: lê os pedaços de texto (do modelo, em stream, ou um texto pronto)
     e corta em frases;
  2. síntese: transforma cada frase em áudio, sempre uma ou duas à frente;
  3. reprodução: toca na ordem, na thread de quem chamou.

Se você interromper ("pare"), as três param e os áudios ainda não tocados são
apagados. Este módulo não conhece Google TTS, ffplay nem microfone: recebe as
funções prontas, o que permite testá-lo sem áudio.
"""

import queue
import re
import threading

# Fim de frase: . ! ? … seguido de espaço (aspas/parênteses no meio são aceitos).
# "6.2" e "R$ 4,26" não cortam porque não há espaço depois do ponto.
_SENTENCE_END = re.compile(r"[.!?…]+[\"'”’)\]]*\s+")


def iter_sentences(pieces, first_min=1, second_min=40, min_len=90):
    """Junta pedaços de texto e devolve frases completas assim que ficam prontas.

    A primeira frase sai assim que termina, para a fala começar logo. A segunda
    é curta (~second_min), para ficar pronta antes de a primeira acabar de
    tocar: a primeira costuma ser breve ("Bom dia, Pedro.") e um segundo trecho
    longo deixava uma pausa. As seguintes são agrupadas até ~min_len, para a
    fala não ficar picotada.
    """
    buffer, emitted = "", 0
    for piece in pieces:
        if not piece:
            continue
        buffer += piece
        while True:
            threshold = (first_min, second_min)[emitted] if emitted < 2 else min_len
            cut = None
            for match in _SENTENCE_END.finditer(buffer):
                if match.end() >= threshold:
                    cut = match.end()
                    break
            if cut is None:
                break
            sentence, buffer = buffer[:cut].strip(), buffer[cut:]
            if sentence:
                emitted += 1
                yield sentence
    if buffer.strip():
        yield buffer.strip()


def run_pipeline(pieces, synthesize, play, prepare, discard, max_chars=1200,
                 lookahead=2, on_sentence=None):
    """Executa a fala em fluxo. Devolve (texto falado, interrompido).

    - synthesize(texto) -> caminho do áudio ou None
    - play(caminho, texto) -> True se você interrompeu
    - prepare(texto, orçamento) -> texto pronto para falar ('' para pular)
    - discard(caminho): apaga um áudio que não vai tocar
    """
    stop = threading.Event()
    sentences = queue.Queue()
    audios = queue.Queue(maxsize=lookahead)
    DONE = object()

    def put_audio(item):
        while not stop.is_set():
            try:
                audios.put(item, timeout=0.2)
                return True
            except queue.Full:
                continue
        return False

    def splitter():
        budget, seen = max_chars, set()
        try:
            for raw in iter_sentences(pieces):
                if stop.is_set() or budget <= 0:
                    break
                text = prepare(raw, budget)
                key = re.sub(r"\W+", " ", text.lower()).strip()
                if not text or key in seen:
                    continue
                seen.add(key)
                budget -= len(text)
                sentences.put(text)
        except Exception as error:  # falha do modelo no meio: fala o que já veio
            print(f"[FALA] Texto interrompido na origem: {error}")
        finally:
            closer = getattr(pieces, "close", None)
            if stop.is_set() and callable(closer):
                try:
                    closer()  # encerra o stream do modelo
                except Exception:
                    pass
            sentences.put(DONE)

    def synthesizer():
        try:
            while not stop.is_set():
                text = sentences.get()
                if text is DONE:
                    break
                path = synthesize(text)
                if path is None:
                    continue
                if not put_audio((text, path)):
                    discard(path)
                    break
        except Exception as error:
            print(f"[FALA] Falha na síntese: {error}")
        finally:
            put_audio(DONE) if not stop.is_set() else None

    threads = [threading.Thread(target=splitter, daemon=True),
               threading.Thread(target=synthesizer, daemon=True)]
    for thread in threads:
        thread.start()

    spoken, interrupted = [], False
    try:
        while True:
            try:
                item = audios.get(timeout=0.2)
            except queue.Empty:
                if not threads[1].is_alive() and audios.empty():
                    break  # síntese terminou sem avisar (erro)
                continue
            if item is DONE:
                break
            text, path = item
            if on_sentence:
                on_sentence(text)
            try:
                interrupted = bool(play(path, text))
            finally:
                discard(path)
            spoken.append(text)
            if interrupted:
                break
    finally:
        stop.set()
        for thread in threads:
            thread.join(timeout=2)
        while True:  # áudios gerados que não chegaram a tocar
            try:
                item = audios.get_nowait()
            except queue.Empty:
                break
            if item is not DONE:
                discard(item[1])
    return " ".join(spoken), interrupted
