# Despliegue del backend de Sensus AI en EC2

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## Importante

La actividad de Explore AWS y el despliegue de Sensus AI deben tratarse como dos cosas separadas. Para ganar el credito de EC2 no hace falta publicar toda la aplicacion. El backend puede desplegarse despues en una instancia propia y controlada.

La configuración actual ejecuta YOLO y profundidad monocular dentro de la instancia. Gemini está
desactivado en la EC2 de prueba. Cualquier
clave de Gemini debe permanecer en el `.env` del servidor y nunca en Expo,
GitHub o una imagen Docker.

## Arquitectura de prueba

```text
APK Android / React Native
        |
        | HTTP temporal para la prueba
        v
EC2 + FastAPI :8000
        |
        +--> YOLO11n local
        +--> Depth Anything V2 Metric Indoor Small local (CPU)
        +--> Safety Governor
        +--> Spatial Core local
        +--> Command Core local
```

## Requisitos de la instancia

Para una prueba pequeña:

- Amazon Linux 2023 o Ubuntu 24.04.
- `m7i-flex.large` para la prueba actual: 2 vCPU y 8 GiB de RAM.
- Disco gp3 de 20 GB.
- Puerto 8000 solo temporalmente y solo desde la IP de prueba.
- Para uso real: HTTPS mediante un dominio y un reverse proxy.

No guardar imagenes ni audio por defecto.

## Ejecucion con Docker

Desde la carpeta `backend`:

```bash
docker build -t sensus-backend .
docker run -d --name sensus-backend --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  sensus-backend
```

Comprobacion:

```text
http://IP_PUBLICA:8000/health
http://IP_PUBLICA:8000/docs
```

## Variables minimas del servidor

```text
APP_NAME=Sensus AI
HOST=0.0.0.0
PORT=8000
RELOAD=false
ALLOWED_ORIGINS=https://tu-dominio-o-ip-de-prueba
GEMINI_API_KEY=colocar_la_clave_solo_en_el_servidor
GEMINI_MODEL=gemini-flash-lite-latest
GEMINI_TIMEOUT_SECONDS=7
GEMINI_MAX_OUTPUT_TOKENS=220
MAX_UPLOAD_BYTES=4194304
```

## Conectar el APK Android

En `frontend/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://100.24.55.64:8000
```

Para produccion debe ser una URL HTTPS. Luego reiniciar Expo:

```bash
npx expo start -c
```

## Limpieza para evitar costes

Cuando termine la prueba:

1. Detener y eliminar el contenedor.
2. Detener o terminar la instancia segun corresponda.
3. Eliminar volumenes EBS no usados.
4. Liberar IPs publicas o Elastic IPs que queden sueltas.
5. Revisar Billing, Free Tier y Credits.

## Seguridad antes de desplegar

- Rotar la clave Gemini si alguna vez se compartio fuera del `.env` local.
- No usar `ALLOWED_ORIGINS=*` en una URL publica.
- No abrir SSH al mundo; restringirlo a la IP del desarrollador.
- No usar este prototipo como unica guia en escaleras, calles o emergencias reales.
