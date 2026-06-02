from pydantic import BaseModel, Field
from typing import Literal


class ContractClause(BaseModel):
    clause_type: str = Field(description="Typ klauzuli (kaucja, wypowiedzenie, czynsz, zwierzęta, etc.)")
    content: str = Field(description="Treść klauzuli z umowy")
    article_reference: str | None = Field(default=None, description="Potencjalny artykuł ustawy którego dotyczy")
    raw_excerpt: str = Field(description="Oryginalny fragment tekstu z umowy")


class ClauseRisk(BaseModel):
    clause: ContractClause
    status: Literal["ok", "warning", "illegal"] = Field(
        description="ok=zgodna z prawem, warning=podejrzana/niekorzystna, illegal=niezgodna z prawem"
    )
    justification: str = Field(description="Uzasadnienie oceny ryzyka")
    legal_basis: str | None = Field(default=None, description="Podstawa prawna (artykuł ustawy)")
    recommendation: str = Field(description="Zalecenie dla najemcy")


class RoomCondition(BaseModel):
    room_name: str = Field(description="Nazwa pomieszczenia (salon, sypialnia, łazienka, etc.)")
    defects: list[str] = Field(default_factory=list, description="Lista wykrytych usterek/uszkodzeń")
    general_condition: Literal["dobry", "średni", "zły"] = Field(description="Ogólny stan pomieszczenia")
    recommendations: list[str] = Field(default_factory=list, description="Zalecenia do dokumentacji")
    photo_description: str = Field(description="Opis tego co widać na zdjęciach")


class LeaseReport(BaseModel):
    clauses: list[ClauseRisk] = Field(description="Lista klauzul z ocenami ryzyka")
    questions_for_landlord: list[str] = Field(description="Pytania do zadania właścicielowi")
    overall_recommendation: str = Field(description="Ogólna rekomendacja dla najemcy")
    risk_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Podsumowanie: {'ok': N, 'warning': N, 'illegal': N}"
    )


class HandoverProtocol(BaseModel):
    property_address: str = Field(default="", description="Adres nieruchomości")
    rooms: list[RoomCondition] = Field(description="Lista pomieszczeń z usterkami")
    protocol_text: str = Field(description="Gotowy protokół zdawczo-odbiorczy jako tekst")
    total_defects: int = Field(default=0, description="Łączna liczba usterek")
