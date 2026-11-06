# Historial de cambios

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## 2026-11-05 — Primera arquitectura YOLO + Gemini

- Se añadió `POST /api/vision/fast-detect` para detección rápida sin consumir Gemini.
- Se añadió `GET /api/vision/capabilities` para que Expo conozca el motor activo.
- Se añadió `SafetyGovernor` con prioridad, crecimiento de cajas, histéresis y supresión de repeticiones.
- Se añadió el adaptador opcional `yolo_detector.py` y `backend/requirements-yolo.txt`.
- Expo usa YOLO automáticamente en tiempo real solo cuando `capabilities.yolo.available` es `true`; de lo contrario conserva Gemini.
- Se instaló y probó localmente `ultralytics` con el modelo pequeño `yolo26n.pt`; los pesos quedan fuera de GitHub.
- El EC2 pequeño mantiene Gemini sin YOLO para no arriesgar memoria ni disponibilidad.

## 2026-11-05 — Backend en EC2 y corrección de subida de imágenes

### Backend y nube

- Se preparó el backend FastAPI para ejecutarse con Docker en Amazon EC2.
- Se añadió `backend/Dockerfile` para construir una imagen reproducible.
- Se añadió `backend/.dockerignore` para evitar copiar secretos y archivos innecesarios.
- Se documentó el despliegue en `docs/DEPLOY_AWS_EC2.md`.
- Se desplegó el backend de prueba en una instancia Amazon Linux 2023 Arm64.
- Se verificó el endpoint `/health` desde fuera de la instancia.
- Se configuró Gemini únicamente en el backend; la clave no se incluye en GitHub ni en Expo.

### Frontend móvil

- Se corrigió el envío de imágenes desde React Native/Expo Go.
- Se reemplazó `expo-file-system/legacy.uploadAsync` por `fetch` con `FormData`.
- El campo multipart enviado al backend es `image`.
- La tarea se envía como el campo `task`.
- Se mantiene el contrato `POST /api/vision/analyze`.

### Motivo de la corrección

Expo Go generaba el error:

```text
ArgumentCastException: The 3rd argument cannot be cast to type UploadOptions
FieldInvalidTypeException: Cannot cast ... for field parameters
```

La causa era que `parameters` no era compatible con la implementación de `uploadAsync` disponible en el dispositivo. `FormData` evita esa conversión nativa y permite enviar la imagen y la tarea como multipart estándar.

### Prueba recomendada

1. Reiniciar Expo con `npx expo start -c`.
2. Abrir el proyecto en Expo Go.
3. Conceder permiso de cámara.
4. Pulsar **Leer ahora**.
5. Verificar que aparezca una respuesta del backend y, si la clave está activa, que el backend use Gemini.

### Seguridad

- No subir `.env` a GitHub.
- No colocar `GEMINI_API_KEY` en el frontend.
- Restringir el puerto 8000 después de la prueba pública.
- Rotar la clave de Gemini si fue expuesta o compartida fuera del servidor.
- Terminar la instancia EC2 cuando finalice la prueba para evitar consumo innecesario.
