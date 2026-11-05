# Guia rapida para el equipo

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

Este documento permite entender Sensus AI y ejecutar una prueba local sin leer todo el repositorio.

## 1. Mapa mental

Sensus AI tiene tres responsabilidades separadas:

```text
Frontend: camara, permisos, voz, vibracion e interfaz
Backend: contrato API, validacion, IA, comandos y seguridad
Spatial Core: sitios, QR, destinos y rutas interiores
```

El frontend no debe decidir por su cuenta que significa una escena. El backend devuelve una respuesta estructurada y el frontend la presenta.

## 2. Orden recomendado de lectura

1. `README.md`: instalacion y panorama general.
2. `contexto/CONTEXTO_MAESTRO.md`: mision, limites y decisiones permanentes.
3. `docs/API_CONTRACT.md`: contrato que no debe romperse.
4. `docs/STACK_TECNOLOGICO.md`: responsabilidades por tecnologia.
5. El documento especifico del cambio que se va a realizar.

## 3. Arrancar el proyecto

Backend, desde `C:\proyecto para ciegos app\SensusAI`:

```powershell
.\.venv\Scripts\Activate.ps1
python backend\app.py
```

Frontend, en otra terminal:

```powershell
cd frontend
npm install
npx expo start
```

Comprobaciones:

```text
Backend:  http://localhost:8000/health
Docs API: http://localhost:8000/docs
Expo:     http://localhost:8081
```

## 4. Archivos que se tocan con mas frecuencia

| Necesidad | Archivo o carpeta |
| --- | --- |
| Agregar endpoint | `backend/routes/` |
| Cambiar logica de IA | `backend/services/vision_ai.py` |
| Cambiar comandos `Sensus ...` | `backend/services/command_core.py` |
| Cambiar mapas, QR o destinos | `backend/data/spatial_map.json` y `backend/services/spatial_core.py` |
| Cambiar llamadas HTTP | `frontend/src/api/sensusClient.js` |
| Cambiar pantalla movil | `frontend/App.js` |
| Cambiar colores | `frontend/src/theme/colors.js` |
| Cambiar contrato | `docs/API_CONTRACT.md` y el endpoint correspondiente |

## 5. Flujo de una orden por voz

```text
Usuario: "Sensus quiero ir al bano"
        |
        v
Interpretacion del intent en Command Core
        |
        v
Busqueda de ubicacion por QR o punto conocido
        |
        v
Spatial Core calcula el siguiente tramo
        |
        v
Frontend habla una instruccion corta
```

En Expo Go se puede probar el flujo con controles simulados. El wake word y la escucha permanente requieren una compilacion nativa posterior.

## 6. Reglas antes de hacer un cambio

- Mantener las respuestas cortas y aptas para audio.
- No inventar certeza: usar `unknown` cuando falten datos.
- No enviar la llave de Gemini al frontend.
- No guardar imagenes ni audio por defecto.
- No romper endpoints existentes sin actualizar el contrato y las pruebas.
- Probar primero en oficina o habitacion controlada.

## 7. Prueba minima antes de compartir cambios

1. Ejecutar `python -m py_compile backend\app.py backend\routes\command.py backend\services\command_core.py`.
2. Abrir `/health` y `/docs`.
3. Probar `Sensus quiero ir al bano`, `Sensus busca mis llaves` y `Sensus emergencia`.
4. Confirmar que la camara pide permiso y que la pantalla muestra el estado.
5. Confirmar que `.env` no aparece en `git status`.

## 8. Limites del prototipo

Sensus AI es asistencia experimental. No debe presentarse como sistema autonomo de seguridad ni como sustituto de ayudas de movilidad, acompanamiento o personal de emergencia.
