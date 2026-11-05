import re
from unicodedata import combining, normalize


def _clean(text: str) -> str:
    normalized = normalize("NFD", text.lower())
    no_accents = "".join(char for char in normalized if not combining(char))
    return re.sub(r"\s+", " ", no_accents).strip()


def interpret_command(text: str, site_id: str | None = None, landmark_id: str | None = None) -> dict:
    command = _clean(text)

    if "sensus" in command:
        command = command.split("sensus", 1)[1].strip()

    if any(word in command for word in ["llave", "llaves", "llavero"]):
        return {
            "intent": "find_object",
            "task": "find_keys",
            "text": "Buscando llaves. Apunta lentamente al suelo, mesa y superficies cercanas.",
            "requires_camera": True,
            "requires_route": False,
            "destination_id": None,
        }

    if any(word in command for word in ["bano", "banio", "servicio", "servicios"]):
        destination_id = "office_mens_bathroom"
        if site_id == "university_pilot":
            destination_id = "u_p7_mens_bathroom"
        if any(word in command for word in ["mujer", "mujeres", "damas"]):
            destination_id = "office_womens_bathroom"
            if site_id == "university_pilot":
                destination_id = "u_p7_womens_bathroom"

        return {
            "intent": "route",
            "task": "navigation",
            "text": "Te ayudo a ir al bano. Necesito tu ubicacion actual por QR o punto conocido.",
            "requires_camera": False,
            "requires_route": True,
            "destination_id": destination_id,
        }

    if any(word in command for word in ["emergencia", "ayuda", "auxilio", "seguridad"]):
        return {
            "intent": "emergency",
            "task": "emergency",
            "text": "Modo emergencia. Detente y pide apoyo cercano.",
            "requires_camera": False,
            "requires_route": False,
            "destination_id": None,
        }

    if any(word in command for word in ["que ves", "leer", "entorno", "delante", "frente"]):
        return {
            "intent": "scan_scene",
            "task": "navigation",
            "text": "Analizando lo que tienes delante.",
            "requires_camera": True,
            "requires_route": False,
            "destination_id": None,
        }

    return {
        "intent": "unknown",
        "task": "navigation",
        "text": "No entendi el comando. Puedes decir: quiero ir al bano, busca mis llaves, o emergencia.",
        "requires_camera": False,
        "requires_route": False,
        "destination_id": None,
    }
