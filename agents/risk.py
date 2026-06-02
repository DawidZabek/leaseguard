from models.schemas import ContractClause, ClauseRisk
from agents.legal import run_legal


def run_risk(clause: ContractClause) -> ClauseRisk:
    legal_result = run_legal(clause)

    return ClauseRisk(
        clause=clause,
        status=legal_result.get("status", "warning"),
        justification=legal_result.get("justification", ""),
        legal_basis=legal_result.get("legal_basis"),
        recommendation=legal_result.get("recommendation", ""),
    )
