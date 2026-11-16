"""
Script de calibración interactiva de la cámara y profundidad.
Delega internamente en 'core.calibrator.CameraCalibrator'.
"""
import sys
from core.config import AppConfig
from core.calibrator import CameraCalibrator

def main():
    camera_id = 0
    if len(sys.argv) > 1:
        try:
            camera_id = int(sys.argv[1])
        except ValueError:
            pass

    config = AppConfig(camera_id=camera_id)
    calibrator = CameraCalibrator(config)
    calibrator.run()

if __name__ == "__main__":
    main()
