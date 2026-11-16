"""
Paquete central para el sistema de visión y estimación de profundidad asistida.
"""
from core.config import AppConfig
from core.depth import DepthEstimator
from core.detector import ObjectDetector
from core.voice import VoiceNarrator

__all__ = ["AppConfig", "DepthEstimator", "ObjectDetector", "VoiceNarrator"]

