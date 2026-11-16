# 📋 Notas de Escaneo — ProyectoProfundidad
> Generado automáticamente por análisis de código. Fecha: 2026-11-16

---

## ¿Qué hace este proyecto?

Sistema de visión artificial en tiempo real para asistir a personas con discapacidad visual.
Tres tecnologías combinadas:

1. **Depth Anything V2** (HuggingFace) → estima distancias en metros desde la cámara
2. **YOLO11n** → detecta y nombra objetos (silla, persona, mesa, etc.)
3. **Windows SAPI / pyttsx3** → síntesis de voz que avisa al usuario de obstáculos

---

## Estructura de archivos

```
ProyectoProfundidad/
│
├── main.py                  ← CLI principal (run / calibrate / info)
├── requirements.txt         ← Dependencias pip
├── calibracion.json         ← Coeficientes a=1.0, b=0.0 (SIN CALIBRAR AÚN)
├── yolo11n.pt               ← Modelo YOLO11 nano (~5.4 MB, local)
│
├── core/                    ← Todo el código real está aquí
│   ├── __init__.py          ← Exporta las 4 clases principales
│   ├── config.py            ← AppConfig: todos los parámetros en un solo lugar
│   ├── depth.py             ← DepthEstimator: motor de profundidad
│   ├── detector.py          ← ObjectDetector + DetectionResult: motor YOLO
│   ├── voice.py             ← VoiceNarrator: TTS asíncrono no bloqueante
│   ├── calibrator.py        ← CameraCalibrator: calibración interactiva
│   └── assistant.py         ← VisualAssistant: orquestador del bucle principal
│
├── vision.py                ← Archivo LEGADO (retrocompatibilidad, no tocar)
├── calibrar.py              ← Archivo LEGADO (retrocompatibilidad, no tocar)
└── profundidad.py           ← Archivo LEGADO (typo corregido de profundiad.py)
```

---

## Qué hace cada clase del `core/`

### `AppConfig` (config.py)
- Dataclass con TODOS los parámetros del sistema
- Parámetros clave:
  - `camera_id = 0`
  - `device = "cuda"` si hay GPU, si no `"cpu"`
  - `dist_peligro = 1.0 m` → rojo
  - `dist_atencion = 2.5 m` → ámbar
  - `dist_obstaculo_frente = 1.6 m` → obstáculos genéricos
  - `cooldown_voz = 4.0 s` → anti-spam de alertas
  - `depth_every_n_frames = 4` → profundidad cada 4 frames para mantener FPS
  - Diccionario de ~30 clases COCO traducidas al español

### `DepthEstimator` (depth.py)
- Carga modelo Depth Anything V2 desde HuggingFace
- Redimensiona frames a 336×252 (múltiplos de 14 para ViT)
- Normaliza con constantes ImageNet
- Aplica corrección lineal: `dist_real = a * dist_modelo + b`
- Genera mapa de calor TURBO (azul=cerca, rojo=lejos)
- Lee y escribe `calibracion.json`

### `ObjectDetector` (detector.py)
- Carga YOLO11n desde `yolo11n.pt`
- Usa **percentil 25** de la zona interior del bounding box para medir distancia
  (captura superficie frontal del objeto, descarta fondo)
- Divide el frame en tercios para posición: "a tu derecha" / "al frente" / "a tu izquierda"
- Clasifica zona de riesgo: "cuidado" (rojo) / "atención" (ámbar) / "seguro" (verde)

### `VoiceNarrator` (voice.py)
- Hilo daemon en segundo plano con `queue.Queue(maxsize=1)`
- Si la cola está llena (sintetizador ocupado), el mensaje nuevo se descarta → no hay latencia acumulada
- Sistema de cooldown por clave `(nombre_objeto, posición, zona)` → evita repetir el mismo aviso
- Prioridad: Windows SAPI → pyttsx3 → print (fallback)

### `CameraCalibrator` (calibrator.py)
- Video en vivo con mira central 40×40 px
- Tecla `C` → toma un punto (valor del modelo vs distancia real ingresada por consola)
- Tecla `G` → regresión lineal con `np.polyfit()` → guarda en `calibracion.json`
- Requiere mínimo 2 puntos de calibración

### `VisualAssistant` (assistant.py)
- Orquestador del bucle principal frame a frame
- Flujo por frame:
  1. Captura frame de cámara
  2. Cada 4 frames → `DepthEstimator.estimate_calibrated()`
  3. `ObjectDetector.detect(frame, depth_map)`
  4. `check_central_obstacle()` → detecta obstáculos que YOLO no clasifica (paredes, postes)
  5. Selecciona el objeto más cercano < 2.5 m → `VoiceNarrator.say()`
  6. Dibuja bounding boxes + etiquetas
  7. Superpone HUD (FPS, estado voz)
  8. Genera mapa de calor y concatena en pantalla dividida
- Teclas en vivo: `ESC/Q` salir, `V` toggle voz, `S` guardar captura JPG

---

## CLI de main.py

```bash
python main.py run              # Arranca el asistente
python main.py calibrate        # Calibración interactiva
python main.py info             # Diagnóstico de hardware
```

Flags de `run`:
- `--camera N`          → ID de cámara (default: 0)
- `--device cpu/cuda`   → forzar hardware
- `--depth-interval N`  → profundidad cada N frames (default: 4)
- `--no-voice`          → solo visual, sin audio
- `--conf F`            → umbral YOLO (default: 0.35)
- `--crop-bars`         → recortar barras negras de cámara

---

## Estado actual

| Aspecto | Estado |
|---|---|
| Arquitectura modular | ✅ Limpia, bien separada |
| Configuración centralizada | ✅ AppConfig |
| Auto-detección GPU/CPU | ✅ |
| Voz asíncrona anti-spam | ✅ |
| Calibración de cámara | ⚠️ PENDIENTE — valores neutros (a=1.0, b=0.0) |
| API REST / endpoints | ❌ No existe |
| Integración con app móvil | ❌ No existe |
| Solo corre en local como CLI | ✅ (limitación actual) |

---

## Dependencias (requirements.txt)

| Librería | Para qué |
|---|---|
| `torch` + `torchvision` | Inferencia en CPU o CUDA |
| `transformers` | Cargar Depth Anything V2 desde HuggingFace |
| `ultralytics` | YOLO11 |
| `opencv-python` | Cámara, dibujo, visualización |
| `numpy` | Operaciones matriciales |
| `pywin32` / `pypiwin32` | Windows SAPI (voz nativa) |
| `pyttsx3` | Fallback de voz multiplataforma |

---

## Notas técnicas a tener en cuenta para el futuro

- El modelo de profundidad se descarga de HuggingFace la primera vez (~100-400 MB según variante)
- El modelo YOLO (`yolo11n.pt`) ya está incluido localmente en el repo
- `calibracion.json` guarda `a` y `b` → hay que re-calibrar si se cambia de cámara
- El flag `--crop-bars` está OFF por defecto para evitar saltos de resolución entre frames
- La voz busca voces en español por keywords: `["spanish", "sabina", "helena", "raul", "es-es", "es-mx"]`
