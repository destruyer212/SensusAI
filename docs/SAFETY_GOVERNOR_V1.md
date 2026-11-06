# Safety Governor v1

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

Safety Governor decide cuando Sensus AI debe analizar, hablar y alertar.

## Objetivo

Evitar tres problemas:

- Gastar IA visual innecesariamente.
- Acumular respuestas atrasadas.
- Cansar al usuario repitiendo lo mismo.

## Reglas actuales

### Una consulta a la vez

La app no toma otra foto si ya hay un analisis en curso.

Esto evita colas de imagenes antiguas.

### Descartar respuestas tardias

Si una respuesta de tiempo real demora demasiado, se descarta.

```text
REALTIME_MAX_RESPONSE_AGE_MS = 8000
```

### Intervalo adaptativo

El intervalo cambia segun riesgo:

```text
clear   -> 9.0 segundos
notice  -> 6.5 segundos
caution -> 3.8 segundos
danger  -> 2.6 segundos
unknown -> 7.0 segundos
```

Si hay peligro, consulta mas rapido.
Si el camino esta despejado, baja frecuencia.

### Imagen mas liviana

En tiempo real se sube una imagen con menor calidad:

```text
quality = 0.34
```

En lectura manual:

```text
quality = 0.50
```

Esto reduce latencia y costo.

### No repetir lo mismo

Sensus no repite el mismo mensaje si acaba de decirlo.

```text
MIN_REPEAT_SPEECH_MS = 12000
```

Excepcion:

- `danger`
- `stop`
- alertas urgentes

## Flujo ideal

```text
Camara
  -> captura liviana
  -> backend Gemini JSON corto
  -> Safety Governor revisa edad/riesgo/repeticion
  -> voz + vibracion solo si aporta valor
```

## Siguiente mejora

La implementación inicial ya está preparada en `backend/services/safety_governor.py` y `backend/services/yolo_detector.py`. El gobernador calcula posición, tamaño relativo y crecimiento de la caja entre frames, aplica histéresis y suprime repeticiones. El endpoint rápido es `POST /api/vision/fast-detect`; el estado real de los motores se consulta en `GET /api/vision/capabilities`.

Si YOLO no está instalado o no hay modelo, la API no inventa detecciones: devuelve `503` y Gemini continúa siendo el camino semántico. La validación debe empezar en oficina, con acompañamiento y sin caminar mirando el teléfono.
