"""Reconhecimento de interrupção sem prender a reprodução ou acumular workers."""
import queue
import threading
import time
import subprocess


class InterruptRecognizer:
    def __init__(self, transcribe):
        self.transcribe = transcribe
        self._busy = threading.Lock()

    def submit(self, blocks):
        if not self._busy.acquire(blocking=False):
            return None
        # Uma fila por pedido: resultado atrasado nunca invade a próxima fala.
        result = queue.Queue(maxsize=1)
        def work():
            try:
                result.put_nowait((self.transcribe(blocks), None))
            except Exception as error:
                result.put_nowait((None, error))
            finally:
                self._busy.release()
        try:
            threading.Thread(target=work, daemon=True).start()
        except Exception:
            self._busy.release()
            raise
        return result


def monitor_playback(proc, frames, is_speech, recognizer, is_interrupt,
                     spoken_text, timeout, recognition_timeout=2.0):
    """Espera o player, nunca a inferência. Retorna a ordem de parar ou None."""
    deadline = time.monotonic() + timeout
    pending = None
    pending_since = None
    segment, speech, silence = [], 0, 0
    recognition_enabled = recognizer is not None
    while proc.poll() is None:
        now = time.monotonic()
        if now >= deadline:
            print('[AUDIO] Reprodução excedeu o limite; encerrando o player.')
            return None
        if pending is not None:
            try:
                heard, error = pending.get_nowait()
            except queue.Empty:
                if now - pending_since >= recognition_timeout:
                    print('[AUDIO] Interrupção lenta; seguindo sem esperar o Whisper nesta fala.')
                    pending = None
                    recognition_enabled = False
            else:
                pending = None
                # O áudio pode ter acabado enquanto consultávamos o resultado.
                if proc.poll() is not None:
                    return None
                if error:
                    print(f'[AUDIO] Interrupção indisponível nesta fala: {error}')
                    recognition_enabled = False
                elif heard and is_interrupt(heard, spoken_text):
                    return heard
                elif heard:
                    print(f'[DEBUG] Ouvido durante a fala (ignorado): {heard}')
        try:
            block = frames.get(timeout=0.03)
        except queue.Empty:
            continue
        # Enquanto transcreve, descarta frames para não montar uma fila de eco.
        if pending is not None or not recognition_enabled:
            continue
        if is_speech(block):
            segment.append(block)
            speech += 1
            silence = 0
        elif segment:
            segment.append(block)
            silence += 1
        else:
            continue
        if silence < 10 and len(segment) < 84:
            continue
        if speech >= 6:
            pending = recognizer.submit(segment)
            pending_since = time.monotonic()
            if pending is None:
                recognition_enabled = False
        segment, speech, silence = [], 0, 0
    return None


def finish_player(proc):
    """Finalização limitada também quando o player falha ou é interrompido."""
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            print('[AUDIO] Player não confirmou encerramento após kill.')
