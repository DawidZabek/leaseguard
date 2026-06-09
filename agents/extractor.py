import json
from models.schemas import ContractClause, ClauseRisk
from rag.setup import query_law
from agents.utils import generate_with_fallback


EXTRACT_AND_ANALYZE_PROMPT = """Jesteś prawnikiem specjalizującym się w prawie najmu w Polsce.

Przeanalizuj poniższą umowę najmu. Wykonaj DWA zadania w jednym kroku:

1. Wyodrębnij wszystkie istotne klauzule (kaucja, czynsz, wypowiedzenie, naprawy, zwierzęta, kary, podnajem, czas trwania)
2. Dla każdej klauzuli oceń ryzyko prawne na podstawie ustawy o ochronie praw lokatorów

PRZEPISY USTAWY O OCHRONIE PRAW LOKATORÓW (do weryfikacji):
{law_context}

Zwróć JSON array gdzie każdy element ma pola:
- clause_type: typ klauzuli (string)
- content: opis treści klauzuli (1-2 zdania)
- raw_excerpt: dosłowny fragment z umowy
- article_reference: artykuł ustawy którego dotyczy (lub null)
- status: "ok" / "warning" / "illegal"
- justification: uzasadnienie oceny (2-3 zdania)
- legal_basis: konkretny artykuł ustawy (lub null)
- recommendation: zalecenie dla najemcy (1-2 zdania)

Zwróć TYLKO JSON array, bez żadnego dodatkowego tekstu.

UMOWA:
{contract_text}
"""


def run_extractor(contract_text: str) -> tuple[list[ContractClause], list[ClauseRisk]]:
    law_chunks = query_law("kaucja wypowiedzenie czynsz najem", n_results=8)
    law_context = "\n\n".join([f"{c['article']}: {c['text']}" for c in law_chunks])

    prompt = EXTRACT_AND_ANALYZE_PROMPT.format(
        law_context=law_context,
        contract_text=contract_text,
    )
    text = generate_with_fallback(prompt)

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    raw_items = json.loads(text)
    clauses = []
    clause_risks = []

    for item in raw_items:
        clause = ContractClause(
            clause_type=item.get("clause_type") or "nieznany",
            content=item.get("content") or "",
            article_reference=item.get("article_reference") or None,
            raw_excerpt=item.get("raw_excerpt") or "",
        )
        risk = ClauseRisk(
            clause=clause,
            status=item.get("status") or "warning",
            justification=item.get("justification") or "",
            legal_basis=item.get("legal_basis") or None,
            recommendation=item.get("recommendation") or "",
        )
        clauses.append(clause)
        clause_risks.append(risk)

    return clauses, clause_risks
