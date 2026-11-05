import json
import random
import re

from settings import settings

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None


SAFETY_PROMPT = """
Eres Sensus AI, un sistema de inteligencia espacial asistida para una prueba controlada con una persona ciega.
Responde en espanol latino, con frases muy cortas y utiles para audio.
Describe solo lo importante para orientacion segura: objetos, personas, puertas, caminos libres,
obstaculos cercanos, texto visible y ubicacion relativa aproximada.
No inventes. Si no estas seguro, dilo claramente.
No des instrucciones peligrosas. Si ves riesgo, recomienda detenerse y pedir ayuda.
La frase speech debe tener maximo 14 palabras, salvo emergencia.
Devuelve solo JSON valido con esta forma:
{
  "speech": "frase corta para leer en voz alta",
  "risk_level": "clear|notice|caution|danger|unknown",
  "action": "continue|slow_down|stop|turn_left|turn_right|search",
  "detections": [
    {
      "label": "objeto o lugar",
      "position": "frente|izquierda|derecha|suelo|lejos|desconocido",
      "distance": "muy cerca|cerca|media|lejos|desconocida",
      "confidence": "alta|media|baja"
    }
  ]
}
Maximo 4 detecciones. Si no estas seguro, usa risk_level unknown.
"""


MOCK_RESPONSES = [
    "Modo prueba. Parece haber una puerta al frente y una mesa a la derecha. Avanza despacio.",
    "Modo prueba. Hay un objeto bajo cerca del centro. Detente y verifica antes de caminar.",
    "Modo prueba. El camino parece libre al frente. Hay una pared o mueble a la izquierda.",
    "Modo prueba. No estoy seguro de la escena. Mantente quieto y pide confirmacion.",
]


def _task_instruction(task: str | None) -> str:
    if task == "find_keys":
        return (
            "Tarea actual: ayudar a encontrar una llave. Busca llaves, llavero, metal pequeno, "
            "mesa, piso, silla, mochila o superficies donde una llave podria estar. "
            "Si no ves la llave, di donde conviene revisar, sin inventar."
        )

    return "Tarea actual: orientar al usuario y advertir obstaculos relevantes."


def _parse_model_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "text": raw_text,
            "risk_level": "unknown",
            "action": "slow_down",
            "detections": [],
        }

    text = str(data.get("speech") or data.get("text") or "").strip()
    detections = data.get("detections") if isinstance(data.get("detections"), list) else []
    return {
        "text": text,
        "risk_level": data.get("risk_level", "unknown"),
        "action": data.get("action", "slow_down"),
        "detections": detections[:4],
    }


async def analyze_scene(image_bytes: bytes, mime_type: str, task: str | None = None) -> dict:
    if not settings.gemini_enabled or genai is None:
        text = random.choice(MOCK_RESPONSES)
        return {
            "mode": "mock",
            "text": text,
            "confidence": "demo",
            "risk_level": "unknown",
            "action": "slow_down",
            "detections": [],
        }

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(
            [
                SAFETY_PROMPT,
                _task_instruction(task),
                {
                    "mime_type": mime_type,
                    "data": image_bytes,
                },
            ],
            generation_config={
                "temperature": 0.0,
                "top_p": 0.4,
                "max_output_tokens": settings.gemini_max_output_tokens,
                "response_mime_type": "application/json",
            },
            request_options={"timeout": settings.gemini_timeout_seconds},
        )
        parsed = _parse_model_response(response.text or "")
    except Exception:
        return {
            "mode": "ai_error",
            "text": "No pude usar la IA visual ahora. Detente y vuelve a intentar.",
            "confidence": "error",
            "risk_level": "unknown",
            "action": "stop",
            "detections": [],
        }

    if not parsed["text"]:
        parsed["text"] = "No pude interpretar la imagen. Detente y verifica con una persona cercana."

    return {
        "mode": "gemini",
        "text": parsed["text"],
        "confidence": "model_estimate",
        "risk_level": parsed["risk_level"],
        "action": parsed["action"],
        "detections": parsed["detections"],
    }
