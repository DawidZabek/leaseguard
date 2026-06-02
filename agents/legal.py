import os
import google.generativeai as genai
from models.schemas import ContractClause
from rag.setup import query_law

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


LEGAL_PROMPT = """Jesteś prawnikiem specjalizującym się w prawie najmu w Polsce.

Zweryfikuj poniższą klauzulę umowy najmu pod kątem ustawy o ochronie praw lokatorów.

KLAUZULA:
Typ: {clause_type}
Treść: {content}
Fragment umowy: {raw_excerpt}

RELEVANTNE PRZEPISY USTAWY:
{law_chunks}

Na podstawie powyższych przepisów oceń czy klauzula:
1. Jest ZGODNA z prawem (ok)
2. Jest PODEJRZANA/NIEKORZYSTNA dla najemcy, ale nie wprost nielegalna (warning)
3. Jest NIEZGODNA z prawem (illegal)

Zwróć odpowiedź jako JSON z polami:
- status: "ok" / "warning" / "illegal"
- justification: uzasadnienie (2-3 zdania)
- legal_basis: konkretny artykuł ustawy (lub null)
- recommendation: zalecenie dla najemcy (1-2 zdania)

Zwróć TYLKO JSON, bez dodatkowego tekstu.
"""


def run_legal(clause: ContractClause) -> dict:
    law_chunks = query_law(f"{clause.clause_type} {clause.content}", n_results=3)
    law_text = "\n\n".join([
        f"{c['article']}: {c['text']}" for c in law_chunks
    ])

    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = LEGAL_PROMPT.format(
        clause_type=clause.clause_type,
        content=clause.content,
        raw_excerpt=clause.raw_excerpt,
        law_chunks=law_text,
    )
    response = model.generate_content(prompt)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    import json
    return json.loads(text)
