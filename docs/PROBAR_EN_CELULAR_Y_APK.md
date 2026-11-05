# Probar Sensus AI en celular y generar APK

## Estado actual

La app movil esta hecha con React Native + Expo.

Ahora mismo se puede probar de inmediato con **Expo Go**.

Todavia no hay un archivo `.apk` generado dentro del proyecto. Para tener APK hay que compilarlo.

## Probar rapido con Expo Go

### 1. Encender backend

```powershell
cd "C:\proyecto para ciegos app\SensusAI"
.\.venv\Scripts\Activate.ps1
python backend\app.py
```

Verificar:

```text
http://localhost:8000/health
```

Debe responder:

```json
{
  "ok": true,
  "app": "Sensus AI",
  "gemini_enabled": true
}
```

### 2. Sacar IP local de la PC

```powershell
ipconfig
```

Busca la IPv4 de tu Wi-Fi o red local. Ejemplo:

```text
192.168.1.50
```

### 3. Configurar frontend

Edita:

```text
frontend/.env
```

Cambia:

```text
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

por:

```text
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.50:8000
```

Usa tu propia IP.

### 4. Encender Expo

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npm start
```

Luego abre **Expo Go** en tu celular y escanea el QR.

## Probar funciones actuales

En la app puedes probar:

- `Leer ahora`: manda una imagen al backend y usa Gemini.
- `Tiempo real`: analiza cada pocos segundos.
- `QR oficina`: simula ubicacion por QR sin gastar IA.
- `Bano H`: pide ruta al bano de hombres usando Spatial Core.
- `Emergencia`: responde con guia segura basica.

## Generar APK

Opcion recomendada:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npx eas build -p android --profile preview
```

Si EAS no esta configurado, primero:

```powershell
npx eas login
npx eas build:configure
```

Luego repite:

```powershell
npx eas build -p android --profile preview
```

EAS genera un enlace de descarga del APK cuando termina.

## Importante

Para probar con otra persona:

- Primero probar solo en oficina o cuarto seguro.
- Siempre con persona supervisora.
- No usar en escaleras, calle, estacionamiento ni emergencia real todavia.
- Si la IA duda, detenerse.
