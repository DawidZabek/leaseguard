import os
import json
import google.generativeai as genai
from models.schemas import ClauseRisk, LeaseReport

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


ADVISOR_PROMPT = """Jesteś doradcą dla najemców mieszkań w Polsce.

Na podstawie analizy klauzul umowy przygotuj:
1. Listę pytań do zadania właścicielowi przed podpisaniem umowy
2. Ogólną rekomendację dla najemcy

WYNIKI ANALIZY KLAUZUL:
{clauses_summary}

STATYSTYKI:
- Klauzule OK: {ok_count}
- Klauzule podejrzane: {warning_count}
- Klauzule niezgodne z prawem: {illegal_count}

Zwróć JSON z polami:
- questions_for_landlord: lista pytań (array of strings), minimum 3 pytania
- overall_recommendation: ogólna rekomendacja dla najemcy (2-3 zdania)

Pytania powinny być konkretne i odnosić się do wykrytych problemów.
Rekomendacja powinna być jednoznaczna: czy podpisać, negocjować, czy odrzucić umowę.

Zwróć TYLKO JSON, bez dodatkowego tekstu.
"""


def run_advisor(clause_risks: list[ClauseRisk]) -> LeaseReport:
    risk_summary = {"ok": 0, "warning": 0, "illegal": 0}
    clauses_summary = []

    for cr in clause_risks:
        risk_summary[cr.status] = risk_summary.get(cr.status, 0) + 1
        emoji = {"ok": "✅", "warning": "⚠️", "illegal": "❌"}.get(cr.status, "?")
        clauses_summary.append(
            f"{emoji} [{cr.clause.clause_type}] {cr.clause.content}\n"
            f"   Ocena: {cr.justification}"
        )

    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = ADVISOR_PROMPT.format(
        clauses_summary="\n\n".join(clauses_summary),
        ok_count=risk_summary["ok"],
        warning_count=risk_summary["warning"],
        illegal_count=risk_summary["illegal"],
    )
    response = model.generate_content(prompt)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    advisor_result = json.loads(text)

    return LeaseReport(
        clauses=clause_risks,
        questions_for_landlord=advisor_result.get("questions_for_landlord", []),
        overall_recommendation=advisor_result.get("overall_recommendation", ""),
        risk_summary=risk_summary,
    )
