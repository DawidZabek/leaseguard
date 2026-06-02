import os
import json
from datetime import date
import google.generativeai as genai
from models.schemas import RoomCondition, HandoverProtocol

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


PROTOCOL_PROMPT = """Jesteś specjalistą od tworzenia protokołów zdawczo-odbiorczych mieszkań w Polsce.

Na podstawie analizy pomieszczeń wygeneruj profesjonalny protokół zdawczo-odbiorczy.

DATA SPORZĄDZENIA: {today}
ADRES: {address}

WYNIKI ANALIZY POMIESZCZEŃ:
{rooms_summary}

Stwórz profesjonalny protokół zdawczo-odbiorczy w języku polskim który:
1. Jest sformułowany formalnie i prawnie
2. Zawiera datę i adres
3. Opisuje stan każdego pomieszczenia z wymienionymi usterkami
4. Zawiera klauzulę o dokumentacji fotograficznej
5. Ma miejsce na podpisy obu stron

Zwróć TYLKO tekst protokołu, bez JSON, bez dodatkowych komentarzy.
"""


def run_protocol(rooms: list[RoomCondition], address: str = "") -> HandoverProtocol:
    rooms_summary = []
    total_defects = 0

    for room in rooms:
        total_defects += len(room.defects)
        defects_text = "\n".join([f"  - {d}" for d in room.defects]) if room.defects else "  - Brak usterek"
        rooms_summary.append(
            f"POMIESZCZENIE: {room.room_name}\n"
            f"Stan ogólny: {room.general_condition}\n"
            f"Usterki:\n{defects_text}\n"
            f"Opis: {room.photo_description}"
        )

    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = PROTOCOL_PROMPT.format(
        today=date.today().strftime("%d.%m.%Y"),
        address=address or "adres do uzupełnienia",
        rooms_summary="\n\n".join(rooms_summary),
    )
    response = model.generate_content(prompt)

    return HandoverProtocol(
        property_address=address,
        rooms=rooms,
        protocol_text=response.text.strip(),
        total_defects=total_defects,
    )
