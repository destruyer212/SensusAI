"""
Script de ejecución de asistencia de visión y profundidad (nombre corregido).
Delega en el coordinador centralizado 'core.assistant.VisualAssistant'.
"""
import sys
from core.config import AppConfig
from core.assistant import VisualAssistant

def main():
    camera_id = 0
    if len(sys.argv) > 1:
        try:
            camera_id = int(sys.argv[1])
        except ValueError:
            pass

    config = AppConfig(camera_id=camera_id)
    assistant = VisualAssistant(config)
    assistant.run()

if __name__ == "__main__":
    main()

