import time
from typing import Optional
import cv2
import numpy as np

from core.config import AppConfig
from core.depth import DepthEstimator
from core.detector import ObjectDetector, DetectionResult
from core.voice import VoiceNarrator

class VisualAssistant:
    """
    Coordinador central del asistente de visión para asistencia a la navegación.
    Integra captura de video, estimación de profundidad métrica, detección de objetos YOLO,
    detección de obstáculos genéricos, alertas por voz y visualización en tiempo real.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.depth_estimator = DepthEstimator(self.config)
        self.detector = ObjectDetector(self.config)
        self.voice = VoiceNarrator(self.config)

    def check_central_obstacle(self, depth_map: np.ndarray, detections: list[DetectionResult]) -> Optional[DetectionResult]:
        """
        Detecta obstáculos no clasificados por YOLO en el corredor central de avance.
        """
        if depth_map is None:
            return None

        h, w = depth_map.shape[:2]
        # Franja central de tránsito
        y1, y2 = int(h * 0.25), int(h * 0.95)
        x1, x2 = int(w * 0.25), int(w * 0.75)

        corridor = depth_map[y1:y2, x1:x2]
        if corridor.size == 0:
            return None

        dist_frente = float(np.percentile(corridor, 20))

        # Si ya hay un objeto YOLO detectado al frente en distancia de atención, no duplicar
        already_has_front = any(d.position == "al frente" and d.distance and d.distance < self.config.dist_atencion for d in detections)

        if dist_frente < self.config.dist_obstaculo_frente and not already_has_front:
            zone, color = self.detector.get_zone_and_color(dist_frente)
            return DetectionResult(
                class_id=-1,
                name_en="obstacle",
                name_es="obstáculo al frente",
                confidence=1.0,
                box_xyxy=(x1, y1, x2, y2),
                center=((x1 + x2) // 2, (y1 + y2) // 2),
                position="al frente",
                distance=dist_frente,
                zone=zone,
                color=color
            )
        return None

    def run(self):
        """
        Ejecuta el bucle principal de asistencia en tiempo real.
        """
        print(f"[VisualAssistant] Iniciando captura desde cámara ID {self.config.camera_id}...")
        cap = cv2.VideoCapture(self.config.camera_id)
        if not cap.isOpened():
            print(f"[ERROR] No se pudo abrir la cámara con ID {self.config.camera_id}.")
            return

        depth_map = None
        frame_idx = 0
        prev_time = time.time()
        fps = 0.0

        print("\n=== Asistente de Visión Activo ===")
        print("Teclas: [ESC / Q] Salir | [V] Alternar Voz | [S] Captura de pantalla\n")

        try:
            while True:
                ok, raw_frame = cap.read()
                if not ok:
                    print("[VisualAssistant] Fin del flujo de video o error de captura.")
                    break

                # Recorte opcional de barras negras si está explícitamente activado
                if self.config.crop_black_bars:
                    frame = self.depth_estimator.crop_bars(raw_frame)
                else:
                    frame = raw_frame
                h, w = frame.shape[:2]

                # Ejecutar estimación de profundidad periódicamente para mantener alto FPS
                if frame_idx % self.config.depth_every_n_frames == 0 or depth_map is None:
                    depth_map = self.depth_estimator.estimate_calibrated(frame)
                frame_idx += 1

                # Garantizar sincronía de dimensiones entre el frame actual y el mapa de profundidad previo
                if depth_map is not None and depth_map.shape[:2] != (h, w):
                    depth_map = cv2.resize(depth_map, (w, h), interpolation=cv2.INTER_LINEAR)

                # Detección de objetos YOLO
                detections = self.detector.detect(frame, depth_map)

                # Obstáculo genérico en corredor central
                obstacle = self.check_central_obstacle(depth_map, detections)
                if obstacle:
                    detections.append(obstacle)

                # Priorizar alertas por voz (el obstáculo o entidad más cercano)
                candidates_for_alert = [
                    d for d in detections 
                    if d.distance is not None and d.distance < self.config.dist_atencion
                ]

                if candidates_for_alert:
                    closest = min(candidates_for_alert, key=lambda x: x.distance)
                    key = (closest.name_es, closest.position, closest.zone)
                    if closest.name_es == "obstáculo al frente":
                        message = "Cuidado, obstáculo muy cerca al frente"
                    else:
                        message = f"{closest.zone}, {closest.name_es} {closest.position}, a {closest.distance:.1f} metros"
                    self.voice.say(message, key=key)

                # Dibujar bounding boxes y etiquetas sobre el frame
                for d in detections:
                    x1, y1, x2, y2 = d.box_xyxy
                    dist_str = f"{d.distance:.1f} m" if d.distance is not None else "? m"
                    label = f"{d.name_es} {dist_str}"
                    
                    # Si es el corredor central genérico, dibujar línea punteada/delgada
                    if d.class_id == -1:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), d.color, 2)
                        cv2.putText(frame, label, (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, d.color, 2)
                    else:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), d.color, 2)
                        cv2.putText(frame, label, (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, d.color, 2)

                # Calcular FPS
                curr_time = time.time()
                fps = 0.9 * fps + 0.1 * (1.0 / max(curr_time - prev_time, 1e-5))
                prev_time = curr_time

                # Superponer HUD de estado en frame
                cv2.putText(frame, f"FPS: {fps:.1f}", (15, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                voice_status = "ON" if self.config.voice_enabled else "OFF"
                cv2.putText(frame, f"Voz: {voice_status}", (15, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

                # Generar mapa de calor visual de profundidad
                depth_vis = self.depth_estimator.colorize(depth_map)

                # Punto central de referencia en el mapa de profundidad
                cy, cx = h // 2, w // 2
                cv2.circle(depth_vis, (cx, cy), 5, (255, 255, 255), -1)
                center_dist = depth_map[cy, cx]
                cv2.putText(depth_vis, f"Centro: {center_dist:.2f} m", (cx + 10, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Asegurar dimensiones idénticas antes de concatenar horizontalmente
                if depth_vis.shape[:2] != frame.shape[:2]:
                    depth_vis = cv2.resize(depth_vis, (w, h), interpolation=cv2.INTER_LINEAR)

                # Concatenar horizontalmente para visualización lado a lado
                combined_view = np.hstack([frame, depth_vis])
                cv2.imshow("Sistema Centralizado de Vision y Profundidad", combined_view)

                # Control de teclado
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord('q'), ord('Q')):
                    break
                elif key in (ord('v'), ord('V')):
                    self.config.voice_enabled = not self.config.voice_enabled
                    print(f"[VisualAssistant] Voz {'Activada' if self.config.voice_enabled else 'Desactivada'}")
                elif key in (ord('s'), ord('S')):
                    ts = int(time.time())
                    filename = f"captura_{ts}.jpg"
                    cv2.imwrite(filename, combined_view)
                    print(f"[VisualAssistant] Captura guardada como '{filename}'")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.voice.stop()
            print("[VisualAssistant] Finalizado correctamente.")

