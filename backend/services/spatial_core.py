import json
from functools import lru_cache
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "spatial_map.json"


@lru_cache
def load_spatial_map() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _site(site_id: str) -> dict | None:
    return next((site for site in load_spatial_map()["sites"] if site["id"] == site_id), None)


def _landmark(site: dict, landmark_id: str) -> dict | None:
    return next((landmark for landmark in site["landmarks"] if landmark["id"] == landmark_id), None)


def list_sites() -> list[dict]:
    return [
        {
            "id": site["id"],
            "name": site["name"],
            "type": site["type"],
            "description": site["description"],
        }
        for site in load_spatial_map()["sites"]
    ]


def resolve_qr(qr_code: str) -> dict | None:
    for site in load_spatial_map()["sites"]:
        qr = next((item for item in site["qr_codes"] if item["code"] == qr_code), None)
        if not qr:
            continue

        landmark = _landmark(site, qr["landmark_id"])
        if not landmark:
            return None

        return {
            "site": {
                "id": site["id"],
                "name": site["name"],
                "type": site["type"],
            },
            "landmark": landmark,
            "text": landmark["spoken"],
        }

    return None


def list_destinations(site_id: str) -> list[dict] | None:
    site = _site(site_id)
    if not site:
        return None

    return [
        {
            "id": landmark["id"],
            "name": landmark["name"],
            "floor": landmark["floor"],
            "kind": landmark["kind"],
        }
        for landmark in site["landmarks"]
        if landmark["kind"] in {"bathroom_men", "bathroom_women", "safe_point", "elevator", "entrance"}
    ]


def get_route(site_id: str, from_landmark_id: str, destination_id: str) -> dict | None:
    site = _site(site_id)
    if not site:
        return None

    origin = _landmark(site, from_landmark_id)
    destination = _landmark(site, destination_id)
    if not origin or not destination:
        return None

    route = next(
        (
            item
            for item in site["routes"]
            if item["from"] == from_landmark_id and item["to"] == destination_id
        ),
        None,
    )
    if not route:
        return None

    text = " ".join(route["steps"])
    return {
        "site": {"id": site["id"], "name": site["name"], "type": site["type"]},
        "from": origin,
        "to": destination,
        "steps": route["steps"],
        "text": text,
    }


def get_emergency_guidance(site_id: str, from_landmark_id: str | None = None) -> dict | None:
    site = _site(site_id)
    if not site:
        return None

    emergency = site["emergency"]
    safe_landmark = _landmark(site, emergency["safe_landmark_id"])
    origin = _landmark(site, from_landmark_id) if from_landmark_id else None

    return {
        "site": {"id": site["id"], "name": site["name"], "type": site["type"]},
        "from": origin,
        "safe_landmark": safe_landmark,
        "text": emergency["message"],
    }
