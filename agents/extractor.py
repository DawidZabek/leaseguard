import os
import json
import google.generativeai as genai
from models.schemas import ContractClause

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


EXTRACTOR_PROMPT = """Jesteś ekspertem od analizy umów najmu mieszkań w Polsce.

Przeanalizuj poniższą umowę najmu i wyodrębnij wszystkie istotne klauzule prawne.
Skup się na:
- kaucji (wysokość, warunki zwrotu)
- czynszu i opłatach dodatkowych
- terminie wypowiedzenia umowy
- odpowiedzialności za naprawy i usterki
- zasadach dotyczących zwierząt, palenia, podnajmu
- karach umownych
- obowiązkach stron
- czasie trwania umowy

Dla każdej klauzuli zwróć JSON array z obiektami o polach:
- clause_type: typ klauzuli (np. "kaucja", "wypowiedzenie", "czynsz", "naprawy", "zwierzęta", "kary umowne", "czas trwania")
- content: krótki opis treści klauzuli (1-2 zdania)
- article_reference: artykuł ustawy o ochronie praw lokatorów który może dotyczyć tej klauzuli (lub null)
- raw_excerpt: dosłowny fragment tekstu umowy

Zwróć TYLKO JSON array, bez dodatkowego tekstu.

UMOWA:
{contract_text}
"""


def run_extractor(contract_text: str) -> list[ContractClause]:
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = EXTRACTOR_PROMPT.format(contract_text=contract_text)
    response = model.generate_content(prompt)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    raw_clauses = json.loads(text)
    clauses = []
    for item in raw_clauses:
        clauses.append(ContractClause(
            clause_type=item.get("clause_type", "nieznany"),
            content=item.get("content", ""),
            article_reference=item.get("article_reference"),
            raw_excerpt=item.get("raw_excerpt", ""),
        ))
    return clauses
