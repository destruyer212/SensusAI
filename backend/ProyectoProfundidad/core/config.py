import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import torch

@dataclass
class AppConfig:
    """Configuración centralizada para el asistente de visión y profundidad."""
    
    # Cámara y Video
    camera_id: int = 0
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    crop_black_bars: bool = False  # Recorte de barras negras (desactivado por defecto para evitar saltos de resolución)
    
    # Dispositivo y Rendimiento
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    torch_threads: int = 8
    
    # Modelo de Profundidad (Depth Anything V2)
    depth_model_name: str = "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf"
    depth_width: int = 336       # Múltiplo de 14 para el ViT del modelo
    depth_height: int = 252      # Múltiplo de 14 para el ViT del modelo
    depth_every_n_frames: int = 4  # Ejecutar estimación cada N frames para fluidez
    max_depth_colormap: float = 5.0 # Metros máximos para normalización del mapa de color
    
    # Modelo de Detección (YOLO)
    yolo_model_path: str = "yolo11n.pt"
    yolo_confidence: float = 0.35
    
    # Umbrales de Seguridad (en metros)
    dist_peligro: float = 1.0          # < 1.0 m -> Alerta de peligro (rojo)
    dist_atencion: float = 2.5         # < 2.5 m -> Alerta de atención (amarillo)
    dist_obstaculo_frente: float = 1.6 # Obstáculo no clasificado al frente
    
    # Cooldown y Control de Alertas
    cooldown_voz: float = 4.0          # Segundos mínimos entre alertas repetidas
    
    # Sistema de Voz (TTS)
    voice_enabled: bool = True
    voice_rate: int = 2                # Velocidad (-10 a 10 para SAPI)
    voice_lang_keywords: List[str] = field(default_factory=lambda: [
        "spanish", "sabina", "helena", "raul", "es-es", "es-mx"
    ])
    
    # Archivos de Calibración
    calibration_file: str = "calibracion.json"
    
    # Diccionario de traducción de clases COCO (YOLO) a español
    class_translations: Dict[str, str] = field(default_factory=lambda: {
        "person": "persona",
        "bicycle": "bicicleta",
        "car": "auto",
        "motorcycle": "motocicleta",
        "airplane": "avión",
        "bus": "autobús",
        "train": "tren",
        "truck": "camión",
        "boat": "bote",
        "traffic light": "semáforo",
        "fire hydrant": "hidrante",
        "stop sign": "señal de pare",
        "bench": "banca",
        "backpack": "mochila",
        "umbrella": "paraguas",
        "handbag": "bolso",
        "bottle": "botella",
        "chair": "silla",
        "couch": "sofá",
        "potted plant": "planta",
        "bed": "cama",
        "dining table": "mesa",
        "toilet": "inodoro",
        "tv": "televisor",
        "laptop": "laptop",
        "mouse": "ratón",
        "remote": "control remoto",
        "keyboard": "teclado",
        "cell phone": "teléfono",
        "microwave": "microondas",
        "oven": "horno",
        "sink": "lavamanos",
        "refrigerator": "refrigerador",
        "book": "libro",
        "clock": "reloj",
        "door": "puerta",
        "stairs": "escaleras",
    })

    def apply_torch_settings(self):
        """Aplica la configuración de hilos a PyTorch."""
        try:
            torch.set_num_threads(self.torch_threads)
        except Exception:
            pass

