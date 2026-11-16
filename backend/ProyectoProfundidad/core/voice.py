import time
import queue
import threading
from typing import Any, Optional
from core.config import AppConfig

class VoiceNarrator:
    """
    Sistema de síntesis de voz (Text-to-Speech) asíncrono y no bloqueante.
    Mantiene un hilo en segundo plano con una cola de tamaño controlado
    para evitar saturación de mensajes y permitir avisos en tiempo real.
    """

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.queue = queue.Queue(maxsize=1)
        self.history = {}
        self.is_running = True
        self.thread = None

        if self.config.voice_enabled:
            self._start_thread()

    def _start_thread(self):
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def _worker_loop(self):
        speaker = None
        engine_type = "none"

        # Intentar inicializar Windows SAPI
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Buscar voz en español
            voices = speaker.GetVoices()
            for v in voices:
                desc = v.GetDescription().lower()
                if any(kw in desc for kw in self.config.voice_lang_keywords):
                    speaker.Voice = v
                    break
            speaker.Rate = self.config.voice_rate
            engine_type = "sapi"
        except Exception as e:
            # Fallback a pyttsx3 si está instalado
            try:
                import pyttsx3
                speaker = pyttsx3.init()
                speaker.setProperty('rate', 150)
                engine_type = "pyttsx3"
            except Exception:
                speaker = None
                engine_type = "print_fallback"

        while self.is_running:
            try:
                text = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if engine_type == "sapi":
                    speaker.Speak(text)
                elif engine_type == "pyttsx3":
                    speaker.say(text)
                    speaker.runAndWait()
                else:
                    print(f"[Voz simulada]: {text}")
            except Exception as e:
                print(f"[VoiceNarrator] Error reproduciendo voz: {e}")

    def can_notify(self, key: Any, cooldown: Optional[float] = None) -> bool:
        """
        Determina si ha pasado suficiente tiempo (cooldown) para repetir un aviso sobre la misma clave.
        """
        cd = cooldown if cooldown is not None else self.config.cooldown_voz
        now = time.time()
        last_time = self.history.get(key, 0.0)
        if now - last_time >= cd:
            self.history[key] = now
            return True
        return False

    def say(self, text: str, key: Optional[Any] = None, cooldown: Optional[float] = None) -> bool:
        """
        Envía un texto a la cola de voz si la clave cumple el tiempo de espera (cooldown).
        Retorna True si fue puesto en cola, False si fue descartado.
        """
        if not self.config.voice_enabled:
            return False

        if key is not None and not self.can_notify(key, cooldown):
            return False

        try:
            self.queue.put_nowait(text)
            return True
        except queue.Full:
            # Si el sintetizador aún está ocupado hablando, descartamos para no acumular latencia
            return False

    def stop(self):
        """Detiene el hilo de voz."""
        self.is_running = False

