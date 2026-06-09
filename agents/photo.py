import json
from PIL import Image
import io
from models.schemas import RoomCondition
from agents.utils import generate_with_fallback


PHOTO_PROMPT = """Jesteś ekspertem od oceny stanu technicznego mieszkań w Polsce.

Przeanalizuj to zdjęcie pomieszczenia i zidentyfikuj:
1. Jakie to pomieszczenie (salon, sypialnia, łazienka, kuchnia, korytarz, itp.)
2. Wszelkie usterki, uszkodzenia, zabrudzenia lub problemy techniczne
3. Ogólny stan pomieszczenia

Zwróć JSON z polami:
- room_name: nazwa pomieszczenia
- defects: lista usterek jako array of strings (każda usterka to osobny string, konkretny i szczegółowy)
- general_condition: "dobry" / "średni" / "zły"
- recommendations: lista zaleceń do dokumentacji (array of strings)
- photo_description: krótki opis co widać na zdjęciu (1-2 zdania)

Bądź dokładny i szczegółowy. Każda usterka powinna być opisana precyzyjnie
(np. "pęknięcie tynku nad oknem ok. 30cm", "zardzewiały kran w zlewie", "plama wilgoci na suficie ok. 20x20cm").

Jeśli pomieszczenie jest w dobrym stanie i brak usterek, zwróć pustą listę defects.

Zwróć TYLKO JSON, bez dodatkowego tekstu.
"""


def _encode_image(image_path: str) -> dict:
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return {"mime_type": "image/jpeg", "data": buf.getvalue()}


def run_photo_analysis(image_path: str) -> RoomCondition:
    image_data = _encode_image(image_path)
    text = generate_with_fallback(PHOTO_PROMPT, image_data=image_data)

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    data = json.loads(text)
    return RoomCondition(
        room_name=data.get("room_name", "Pomieszczenie"),
        defects=data.get("defects", []),
        general_condition=data.get("general_condition", "średni"),
        recommendations=data.get("recommendations", []),
        photo_description=data.get("photo_description", ""),
    )
