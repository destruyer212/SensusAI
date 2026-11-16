import argparse
import sys
import torch
import cv2

from core.config import AppConfig
from core.assistant import VisualAssistant
from core.calibrator import CameraCalibrator
from core.depth import DepthEstimator

def show_system_info(config: AppConfig):
    print("=" * 60)
    print("        INFORMACIÓN DEL SISTEMA Y ENTORNO")
    print("=" * 60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"OpenCV: {cv2.__version__}")
    print(f"PyTorch: {torch.__version__}")
    cuda_ok = torch.cuda.is_available()
    print(f"CUDA disponible: {cuda_ok}")
    if cuda_ok:
        print(f"Dispositivo GPU: {torch.cuda.get_device_name(0)}")
    print(f"Dispositivo configurado: {config.device}")
    print(f"Hilos CPU PyTorch: {config.torch_threads}")
    print(f"Cámara ID por defecto: {config.camera_id}")
    print(f"Modelo Profundidad: {config.depth_model_name}")
    print(f"Modelo YOLO: {config.yolo_model_path}")
    print(f"Archivo de Calibración: {config.calibration_file}")

    # Comprobar calibración existente
    estimator = DepthEstimator(config)
    print(f"Parámetros de Calibración Actuales: a={estimator.a:.4f}, b={estimator.b:.4f}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="Sistema Centralizado de Visión Artificial y Estimación de Profundidad Asistida."
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Comando 'run'
    run_parser = subparsers.add_parser("run", help="Inicia el asistente en tiempo real (visión + YOLO + profundidad + voz)")
    run_parser.add_argument("--camera", type=int, default=0, help="ID de la cámara (por defecto: 0)")
    run_parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda", "auto"], help="Dispositivo de cómputo")
    run_parser.add_argument("--depth-interval", type=int, default=4, help="Calcular profundidad cada N frames (por defecto: 4)")
    run_parser.add_argument("--no-voice", action="store_true", help="Desactiva los avisos por voz")
    run_parser.add_argument("--conf", type=float, default=0.35, help="Umbral de confianza para YOLO")
    run_parser.add_argument("--crop-bars", action="store_true", help="Activar recorte automático de barras negras")

    # Comando 'calibrate'
    calib_parser = subparsers.add_parser("calibrate", help="Inicia la herramienta interactiva de calibración de profundidad")
    calib_parser.add_argument("--camera", type=int, default=0, help="ID de la cámara (por defecto: 0)")
    calib_parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda", "auto"], help="Dispositivo de cómputo")
    calib_parser.add_argument("--crop-bars", action="store_true", help="Activar recorte automático de barras negras")

    # Comando 'info'
    subparsers.add_parser("info", help="Muestra diagnósticos de hardware, modelos y calibración")

    args = parser.parse_args()

    # Si no se pasó comando, por defecto se ejecuta 'run'
    command = args.command or "run"

    # Construir configuración
    config = AppConfig()
    if hasattr(args, "camera") and args.camera is not None:
        config.camera_id = args.camera
    if hasattr(args, "device") and args.device:
        if args.device == "auto":
            config.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            config.device = args.device
    if hasattr(args, "depth_interval") and args.depth_interval:
        config.depth_every_n_frames = args.depth_interval
    if hasattr(args, "no_voice") and args.no_voice:
        config.voice_enabled = False
    if hasattr(args, "conf") and args.conf:
        config.yolo_confidence = args.conf
    if hasattr(args, "crop_bars") and args.crop_bars:
        config.crop_black_bars = True

    if command == "run":
        assistant = VisualAssistant(config)
        assistant.run()
    elif command == "calibrate":
        calibrator = CameraCalibrator(config)
        calibrator.run()
    elif command == "info":
        show_system_info(config)

if __name__ == "__main__":
    main()

