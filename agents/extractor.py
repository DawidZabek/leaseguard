import json
import re
from models.schemas import ContractClause, ClauseRisk
from rag.setup import query_law
from agents.utils import generate_with_fallback, strip_json_fences

CONTRACT_CHAR_LIMIT = 6000

EXTRACT_AND_ANALYZE_PROMPT = """Jesteś prawnikiem od prawa najmu w Polsce. Przeanalizuj umowę i zwróć JSON array.

PRZEPISY USTAWY O OCHRONIE PRAW LOKATORÓW (na podstawie tych przepisów oceniaj klauzule):
{law_context}

ZASADY EKSTRAKCJI:
1. Każdy punkt numerowany (1., 2., 3. itd.) to OSOBNA klauzula — nie łącz ich w jeden obiekt
2. Każdy zakaz i każde ograniczenie to osobna klauzula
3. Klauzula obciążająca najemcę naprawami ze zwykłego zużycia jest niezgodna z ustawą
4. Zakaz lub ograniczenie niewynikające z uzasadnionego interesu wynajmującego może być klauzulą abuzywną (art. 385¹ KC)

ZASADY WYPEŁNIANIA POLA legal_basis:
- Dla klauzul "illegal" i "warning": pole legal_basis jest OBOWIĄZKOWE — podaj konkretny artykuł z kontekstu powyżej który narusza lub, jeśli narusza KC, wpisz np. "art. 385¹ KC" (klauzule abuzywne) lub "art. 11 ust. 1 KC" itd.
- Dla klauzul "ok": legal_basis może być null jeśli klauzula nie opiera się na konkretnym przepisie

Dla każdej klauzuli zwróć obiekt JSON:
{{"clause_type":"string","content":"1 zdanie","raw_excerpt":"dosłowny fragment z umowy","article_reference":"art. X lub null","status":"ok|warning|illegal","justification":"1 zdanie","legal_basis":"konkretny artykuł — WYMAGANY dla illegal/warning","recommendation":"1 zdanie"}}

Zwróć TYLKO JSON array, bez żadnego tekstu przed ani po.

UMOWA:
{contract_text}"""


def _compress_contract(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    text = text.strip()
    if len(text) > CONTRACT_CHAR_LIMIT:
        text = text[:CONTRACT_CHAR_LIMIT] + "\n[...tekst skrócony do 6000 znaków]"
    return text


def run_extractor(contract_text: str) -> tuple[list[ContractClause], list[ClauseRisk]]:
    # RAG: pobierz artykuły ustawy pokrywające typowe tematy umowy najmu
    law_chunks = query_law(
        "kaucja czynsz podwyżka wypowiedzenie naprawy zakazy ograniczenia korzystanie lokal",
        n_results=3,
    )
    law_context = "\n".join([f"{c['article']}: {c['text']}" for c in law_chunks])

    prompt = EXTRACT_AND_ANALYZE_PROMPT.format(
        law_context=law_context,
        contract_text=_compress_contract(contract_text),
    )
    text = strip_json_fences(generate_with_fallback(prompt))

    raw_items = json.loads(text)
    clauses, clause_risks = [], []
    for item in raw_items:
        clause_type = item.get("clause_type") or "nieznany"
        legal_basis = item.get("legal_basis") or None

        clause = ContractClause(
            clause_type=clause_type,
            content=item.get("content") or "",
            article_reference=item.get("article_reference") or legal_basis,
            raw_excerpt=item.get("raw_excerpt") or "",
        )
        clause_risks.append(ClauseRisk(
            clause=clause,
            status=item.get("status") or "warning",
            justification=item.get("justification") or "",
            legal_basis=legal_basis,
            recommendation=item.get("recommendation") or "",
        ))
        clauses.append(clause)
    return clauses, clause_risks
