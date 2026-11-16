import cv2
import numpy as np
from core.config import AppConfig
from core.depth import DepthEstimator

class CameraCalibrator:
    """
    Herramienta interactiva para calibrar la escala métrica estimada por Depth Anything V2
    contra distancias reales medidas físicamente (ej. con cinta métrica).
    Calcula una regresión lineal: distancia_real = a * distancia_modelo + b.
    """

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.depth_estimator = DepthEstimator(self.config)
        self.measurements: list[tuple[float, float]] = [] # (modelo, real)

    def run(self):
        print(f"[Calibrador] Abriendo cámara ID {self.config.camera_id}...")
        cap = cv2.VideoCapture(self.config.camera_id)
        if not cap.isOpened():
            print(f"[ERROR] No se pudo abrir la cámara con ID {self.config.camera_id}.")
            return

        print("\n==================================================")
        print("         MODO DE CALIBRACIÓN DE PROFUNDIDAD       ")
        print("==================================================")
        print("Instrucciones:")
        print("1. Apunta el recuadro central verde hacia una pared u objeto plano.")
        print("2. Mide con una cinta métrica la distancia física real desde la cámara al objeto.")
        print("3. Presiona 'C' en la ventana para ingresar la distancia real.")
        print("4. Repite con al menos 2 o 3 distancias distintas (ej. 1.0m, 2.0m, 3.5m).")
        print("5. Presiona 'G' para calcular el ajuste lineal y guardarlo en calibracion.json.")
        print("6. Presiona 'ESC' para salir.")
        print("==================================================\n")

        try:
            while True:
                ok, raw_frame = cap.read()
                if not ok:
                    print("[Calibrador] Error leyendo frame de la cámara.")
                    break

                if self.config.crop_black_bars:
                    frame = self.depth_estimator.crop_bars(raw_frame)
                else:
                    frame = raw_frame
                h, w = frame.shape[:2]

                # Estimar profundidad cruda (sin calibrar)
                raw_depth = self.depth_estimator.estimate_raw(frame)

                cy, cx = h // 2, w // 2
                box_half = 20
                sample_region = raw_depth[cy - box_half:cy + box_half, cx - box_half:cx + box_half]
                val_modelo = float(np.median(sample_region)) if sample_region.size > 0 else 0.0

                view = frame.copy()
                # Dibujar mira central
                cv2.rectangle(view, (cx - box_half, cy - box_half), (cx + box_half, cy + box_half), (0, 255, 0), 2)
                cv2.circle(view, (cx, cy), 3, (0, 0, 255), -1)

                info_text = f"Modelo: {val_modelo:.2f} m | Puntos recolectados: {len(self.measurements)}"
                cv2.putText(view, info_text, (20, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                cv2.putText(view, "[C] Tomar punto | [G] Guardar | [ESC] Salir", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                cv2.imshow("Calibrador de Profundidad", view)
                key = cv2.waitKey(1) & 0xFF

                if key in (ord('c'), ord('C')):
                    # Pausar visualización brevemente para tomar entrada por consola
                    print(f"\n[Muestra] Valor medido por el modelo: {val_modelo:.3f} m")
                    try:
                        real_str = input(">> Ingrese distancia real medida físicamente (en metros): ").strip()
                        if real_str:
                            real_val = float(real_str)
                            self.measurements.append((val_modelo, real_val))
                            print(f"[OK] Punto registrado: Modelo={val_modelo:.3f} m -> Real={real_val:.3f} m")
                    except ValueError:
                        print("[AVISO] Valor numérico inválido. Intente de nuevo.")

                elif key in (ord('g'), ord('G')):
                    if len(self.measurements) < 2:
                        print(f"\n[AVISO] Se requieren al menos 2 puntos distintos para ajustar la recta. Puntos actuales: {len(self.measurements)}")
                    else:
                        m = np.array(self.measurements)
                        # Regresión lineal de primer orden: y = a*x + b
                        a, b = np.polyfit(m[:, 0], m[:, 1], 1)
                        saved_path = self.depth_estimator.save_calibration(a, b, self.measurements, self.config.calibration_file)
                        print(f"\n[ÉXITO] Calibración guardada en '{saved_path}'")
                        print(f"Fórmula: distancia_real = {a:.4f} * valor_modelo + ({b:.4f})")
                        print("Puntos utilizados:")
                        for mod, r in self.measurements:
                            ajustado = a * mod + b
                            print(f" - Modelo: {mod:.2f} m | Real: {r:.2f} m | Ajustado por fórmula: {ajustado:.2f} m")

                elif key == 27: # ESC
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[Calibrador] Finalizado.")

