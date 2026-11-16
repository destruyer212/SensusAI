# Sistema Centralizado de Visión Artificial y Estimación de Profundidad Asistida

Este proyecto implementa un asistente inteligente en tiempo real para detección de obstáculos y asistencia a la navegación espacial. Combina **estimación monocular métrica de profundidad** (Depth Anything V2), **detección semántica de objetos** (YOLO11) y un **sistema de alertas audibles por voz** (Text-to-Speech) no bloqueante.

---

## 1. Análisis de los Archivos Originales

El proyecto original estaba dividido en tres archivos con responsabilidades separadas pero acopladas:

### 1. `vision.py` (Módulo de Profundidad)
* **Objetivo:** Cargar el modelo preentrenado de Hugging Face `depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf` para estimar profundidad a partir de una única imagen monocular RGB.
* **Procesamiento:**
  * `recortar_barras(frame)`: Recorta franjas negras superior e inferior generadas por algunas cámaras.
  * `estimar_profundidad(frame)`: Redimensiona la imagen a `336x252` (múltiplos de 14 para la arquitectura Vision Transformer), normaliza con media y desviación estándar de ImageNet, ejecuta inferencia en PyTorch y reescala la matriz al tamaño original.
  * `cargar_calibracion()` y `profundidad_calibrada()`: Aplica una transformación afín $distancia = a \cdot modelo + b$ para ajustar los valores del modelo a la óptica real de la cámara.
* **Limitaciones observadas:** Forzaba ejecución solo en CPU (`torch.set_num_threads(8)`), sin opción a usar CUDA/GPU; parámetros fijos sin posibilidad de parametrización externa.

### 2. `calibrar.py` (Herramienta de Calibración)
* **Objetivo:** Calcular empíricamente los factores de corrección lineal $a$ (pendiente) y $b$ (desplazamiento) para la cámara.
* **Mecanismo:**
  * Mide la mediana de profundidad en una ventana central de $40 \times 40$ píxeles.
  * El usuario apunta a una superficie a distancia conocida y presiona `C` para introducir la distancia real medida físicamente (en metros).
  * Al presionar `G`, utiliza `np.polyfit(..., 1)` para calcular la recta de mejor ajuste por mínimos cuadrados y la guarda en `calibracion.json`.
* **Limitaciones observadas:** Tenía configurado el índice de cámara en `1` (`cv2.VideoCapture(1)`), mientras que el script principal usaba `0`, provocando fallos si el usuario sólo tiene una cámara.

### 3. `profundiad.py` (Script Principal con Typo en el Nombre)
* **Objetivo:** Asistente en vivo que detecta objetos con YOLO, calcula su distancia espacial y emite advertencias sonoras.
* **Mecanismo:**
  * Captura de video en bucle principal.
  * Corre profundidad cada `DEPTH_CADA = 4` frames para mantener fluidez.
  * Ejecuta YOLO11 para localizar objetos (personas, sillas, mesas, etc.).
  * Calcula la distancia de cada objeto tomando el **percentil 25** de la zona central del bounding box (captura la superficie frontal del objeto descartando fondos).
  * Determina posición relativa horizontal: *"a tu derecha"*, *"al frente"*, *"a tu izquierda"*.
  * Clasifica el riesgo:
    * **Peligro** (< 1.0 m): Resaltado en **Rojo**.
    * **Atención** (< 2.5 m): Resaltado en **Ámbar**.
    * **Seguro** ($\ge$ 2.5 m): Resaltado en **Verde**.
  * Revisa un corredor central ciego (para objetos que YOLO no reconozca, como paredes o postes a < 1.6 m).
  * Emite voz mediante un hilo dedicado con Windows SAPI (`SpVoice`), evitando que la síntesis de voz congele el flujo de video.
* **Limitaciones observadas:** Código monolítico en un único archivo de bucle procedural, variables globales de cooldown, nombres hardcodeados y falta de CLI para personalizar parámetros.

---

## 2. Nueva Arquitectura Centralizada

El código ha sido refactorizado en una arquitectura modular limpia bajo el paquete `core/`, con un punto de entrada unificado `main.py` y compatibilidad total con los nombres antiguos:

```
c:\AGENTE IA\PRUEBA_PROFUNDIDAD\
│
├── core/
│   ├── __init__.py          # Exportaciones limpias del paquete
│   ├── config.py            # Fuente única de verdad (AppConfig)
│   ├── depth.py             # DepthEstimator (Depth Anything V2 + CUDA/CPU + Colormap)
│   ├── detector.py          # ObjectDetector (YOLO11 + Distancias + Zonas espaciales)
│   ├── voice.py             # VoiceNarrator (TTS asíncrono no bloqueante con cooldowns)
│   ├── calibrator.py        # CameraCalibrator (Ajuste lineal interactivo y guardado)
│   └── assistant.py         # VisualAssistant (Orquestador del bucle principal y HUD)
│
├── main.py                  # CLI centralizada (run, calibrate, info)
├── vision.py                # Capa de compatibilidad hacia atrás
├── calibrar.py              # Capa de compatibilidad hacia atrás
├── profundidad.py           # Script con nombre corregido
├── calibracion.json         # Coeficientes de calibración (a, b)
└── requirements.txt         # Dependencias del proyecto
```

### Ventajas de la nueva arquitectura:
1. **Configuración Única (`AppConfig`):** Se centralizan umbrales de peligro (1.0m), atención (2.5m), detección ciega (1.6m), resolución de inferencia, traducciones y parámetros de cámara.
2. **Aceleración por Hardware Automática:** Si hay GPU NVIDIA disponible, el sistema usa automáticamente `cuda` para una tasa de fotogramas por segundo (FPS) mucho mayor; en caso contrario, conmuta suavemente a `cpu` optimizada.
3. **Robustez de Audio:** El sintetizador maneja Windows SAPI nativo y cuenta con fallback automático, cola descartable de 1 elemento (no acumula mensajes atrasados) y cooldowns inteligentes por tupla `(objeto, posición, severidad)`.
4. **Punto de Entrada CLI Unificado:** Con `python main.py` puedes inspeccionar el hardware, calibrar la cámara o arrancar el asistente pasando parámetros por línea de comandos.
5. **Retrocompatibilidad:** Si tienes scripts existentes que hagan `from vision import ...` o ejecuten `python profundiad.py`, seguirán funcionando de inmediato.

---

## 3. ¿Qué es lo que se tiene que hacer? (Guía Paso a Paso)

Sigue estos pasos ordenados para poner el sistema en funcionamiento:

### Paso 1: Configurar el Entorno de Python
Si tu entorno virtual actual presenta inconsistencias, se recomienda reconstruirlo limpiamente:

```powershell
# 1. Situarse en la carpeta del proyecto
cd "c:\AGENTE IA\PRUEBA_PROFUNDIDAD"

# 2. (Opcional si el entorno actual falla) Crear entorno virtual nuevo:
python -m venv .venv

# 3. Activar el entorno virtual:
.\.venv\Scripts\activate

# 4. Instalar las dependencias limpias:
pip install -r requirements.txt
```

> **Nota:** Si dispones de tarjeta gráfica NVIDIA con soporte CUDA, puedes instalar la versión de PyTorch con CUDA para máxima velocidad:
> `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

---

### Paso 2: Verificar Diagnóstico del Sistema
Comprueba que los modelos, cámara y hardware sean detectados correctamente:

```powershell
python main.py info
```
Este comando te mostrará:
* Versiones de Python, OpenCV y PyTorch.
* Disponibilidad de aceleración CUDA.
* Estado de los archivos de calibración.

---

### Paso 3: Calibrar la Cámara (Recomendado para Máxima Precisión)
Cada lente de cámara tiene un ángulo de visión (FOV) y distorsión específicos. La calibración asegura que 1.5 metros medidos por el modelo correspondan exactamente a 1.5 metros físicos.

1. Ejecuta el modo calibración (especifica `--camera 0` o `--camera 1` según tu webcam):
   ```powershell
   python main.py calibrate --camera 0
   ```
2. Apunta la cámara hacia una pared o un objeto plano grande.
3. Con una **cinta métrica**, mide la distancia desde el lente de la cámara hasta la superficie (por ejemplo: `1.0` metro).
4. Presiona la tecla **`C`** en la ventana de video e ingresa `1.0` en la consola.
5. Retrocede o cambia a otra distancia (ej. `2.0` metros), presiona **`C`** e ingresa `2.0`.
6. Repite a una tercera distancia (ej. `3.0` metros).
7. Presiona la tecla **`G`** para calcular la regresión lineal y guardar automáticamente en `calibracion.json`.
8. Presiona **`ESC`** para salir.

---

### Paso 4: Iniciar el Asistente en Tiempo Real
Inicia el sistema completo con visión, detección YOLO, profundidad y síntesis de voz:

```powershell
python main.py run
```

#### Opciones y flags útiles:
* Cambiar de cámara (si tienes más de una):
  ```powershell
  python main.py run --camera 1
  ```
* Ejecutar sin audio (solo visual):
  ```powershell
  python main.py run --no-voice
  ```
* Forzar ejecución en CPU o GPU:
  ```powershell
  python main.py run --device cpu
  python main.py run --device cuda
  ```
* Ajustar intervalo de cálculo de profundidad (para equipos con menor potencia):
  ```powershell
  # Calcula profundidad cada 6 fotogramas para aumentar FPS
  python main.py run --depth-interval 6
  ```

---

### Paso 5: Controles Interactivos Durante la Ejecución
En la ventana interactiva puedes utilizar los siguientes atajos de teclado:

| Tecla | Acción |
|---|---|
| **`ESC`** o **`Q`** | Cerrar y finalizar la aplicación de forma segura. |
| **`V`** | Activar o desactivar las alertas por voz en tiempo real. |
| **`S`** | Guardar una captura de pantalla instantánea (formato `.jpg`). |

---

## 5. Solución de Problemas Frecuentes

### Error `ValueError: along dimension 0, the array at index 0 has size 360 and the array at index 1 has size 480`
* **Causa:** Ocurría cuando la función de recorte de barras negras (`crop_bars`) alteraba dinámicamente la altura del frame (por ejemplo, en el arranque de la cámara o zonas con baja luminosidad) mientras que el mapa de profundidad (`depth_map`) retenía las dimensiones del fotograma previo debido al intervalo de cálculo periódico (`depth_every_n_frames`).
* **Solución aplicada:** Se sincronizan automáticamente las dimensiones de `depth_map` y `depth_vis` con las del `frame` actual antes de la concatenación (`np.hstack`), y el recorte agresivo de barras viene desactivado por defecto (`crop_black_bars = False`). Puede forzarse con `--crop-bars` si su cámara realmente tiene barras negras fijas.

---

## 4. Estructura de Visualización (Pantalla Dividida)

Durante la ejecución, la pantalla se divide en dos paneles:
1. **Panel Izquierdo (RGB + Detecciones):**
   * Vista de la cámara con bounding boxes.
   * Color **Rojo**: Obstáculo a menos de 1.0 m (*Peligro / Cuidado*).
   * Color **Ámbar / Naranja**: Objeto entre 1.0 m y 2.5 m (*Atención*).
   * Color **Verde**: Objeto a más de 2.5 m (*Seguro*).
   * Indicador en tiempo real de FPS y estado de voz.
2. **Panel Derecho (Mapa de Calor Métrico Turbo):**
   * **Azul oscuro / Cian:** Objetos muy cercanos.
   * **Verde / Amarillo:** Distancia intermedia.
   * **Rojo:** Objetos lejanos (hasta 5.0 metros).
   * Mira central en blanco con lectura exacta en metros del centro de tu campo visual.

