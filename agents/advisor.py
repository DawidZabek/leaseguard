import json
from models.schemas import ClauseRisk, LeaseReport
from agents.utils import generate_with_fallback

ADVISOR_PROMPT = """Jesteś doradcą najemców mieszkań. Na podstawie analizy klauzul:

{clauses_compact}

Zwróć JSON:
{{"questions_for_landlord":["pytanie 1","pytanie 2","pytanie 3"],"overall_recommendation":"2 zdania"}}

Pytania mają dotyczyć konkretnych problemów z umowy. Rekomendacja: podpisać / negocjować / odrzucić.
Zwróć TYLKO JSON."""


def run_advisor(clause_risks: list[ClauseRisk]) -> LeaseReport:
    risk_summary = {"ok": 0, "warning": 0, "illegal": 0}
    lines = []
    status_label = {"ok": "OK", "warning": "PODEJRZANA", "illegal": "NIELEGALNA"}

    for cr in clause_risks:
        risk_summary[cr.status] = risk_summary.get(cr.status, 0) + 1
        lines.append(f"- [{status_label.get(cr.status,'?')}] {cr.clause.clause_type}: {cr.clause.content}")

    prompt = ADVISOR_PROMPT.format(clauses_compact="\n".join(lines))
    text = generate_with_fallback(prompt)

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    result = json.loads(text)
    return LeaseReport(
        clauses=clause_risks,
        questions_for_landlord=result.get("questions_for_landlord", []),
        overall_recommendation=result.get("overall_recommendation", ""),
        risk_summary=risk_summary,
    )
