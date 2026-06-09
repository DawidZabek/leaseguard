import json
from PIL import Image
import io
from models.schemas import RoomCondition
from agents.utils import generate_with_fallback


PHOTO_PROMPT = """Jesteś rzeczoznawcą sporządzającym protokół zdawczo-odbiorczy mieszkania w Polsce.

Twoim zadaniem jest ocena FIZYCZNEGO stanu pomieszczenia pod kątem usterek istotnych przy przekazaniu lokalu.

Zgłaszaj TYLKO rzeczywiste usterki fizyczne:
- uszkodzenia mechaniczne (pęknięcia, rysy, dziury, odpryski tynku, zarysowania)
- ślady wilgoci, pleśni, zacieki na ścianach/suficie
- uszkodzony sprzęt (niedziałające gniazdka, krany, zamki, okna)
- zabrudzenia trwałe (plamy na podłodze, ścianie)
- zniszczenia mebli lub wyposażenia stanowiącego część lokalu

NIE zgłaszaj:
- normalnego, estetycznego wyglądu (kolor ściany, styl mebli, dekoracje)
- drobnych niedoskonałości niewidocznych w normalnym użytkowaniu
- elementów wyglądających "zbyt dobrze" lub "zbyt nowych"
- czegokolwiek dotyczącego stylu, designu lub gustu

Jeśli zdjęcie przedstawia pomieszczenie w dobrym stanie bez widocznych usterek fizycznych — zwróć pustą listę defects. Nie wymuszaj usterek na siłę.

Zwróć JSON:
- room_name: nazwa pomieszczenia (salon, sypialnia, łazienka, kuchnia, korytarz, inne)
- defects: lista fizycznych usterek (array of strings, każda opisana konkretnie np. "pęknięcie tynku nad oknem ~15cm") lub []
- general_condition: "dobry" / "średni" / "zły"
- recommendations: zalecenia do protokołu, np. "udokumentować stan podłogi przed wprowadzeniem" (array) lub []
- photo_description: 1 zdanie co widać na zdjęciu

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
