# LeaseGuard — Inteligentny asystent najemcy

## Problem biznesowy

Najemca podpisuje umowę najmu nie rozumiejąc klauzul i traci kaucję za usterki, które zastał przy wprowadzeniu. Weryfikacja umowy u prawnika kosztuje **300–500 zł** i trwa **2 godziny**. LeaseGuard redukuje to do **2 minut** i **0 zł**.

**Dla kogo:** firmy zarządzające nieruchomościami (Mzuri), agencje (Metrohouse, Freedom), platformy ogłoszeniowe (Otodom).

---

## Funkcje

### Moduł 1 — Analiza umowy najmu
- Wyodrębnia wszystkie klauzule (kaucja, wypowiedzenie, czynsz, naprawy, kary)
- Weryfikuje każdą klauzulę względem **ustawy o ochronie praw lokatorów** (RAG na ChromaDB)
- Klasyfikuje ryzyko: ✅ OK / ⚠️ Podejrzana / ❌ Niezgodna z prawem
- Generuje pytania do zadania właścicielowi + rekomendację końcową

### Moduł 2 — Protokół zdawczo-odbiorczy
- Analizuje zdjęcia mieszkania (Gemini Vision)
- Wykrywa usterki pokój po pokoju
- Generuje profesjonalny protokół zdawczo-odbiorczy gotowy do wydruku

---

## Demo — Golden Path

**Umowa z kaucją 4 miesiące (10 000 zł):**
- Agent flaguje ❌ niezgodność z art. 6 ust. 1 (max kaucja = 12× czynsz, ale 4 miesiące jest zgodne — agent sprawdza)
- Agent flaguje ❌ brak okresu wypowiedzenia dla wynajmującego (art. 11)
- Agent flaguje ⚠️ jednostronne prawo do podwyżki czynszu (art. 8a)
- Generuje 5 pytań do właściciela + rekomendację negocjacji

**Edge case — umowa bez okresu wypowiedzenia:**
- Agent wykrywa brak + oznacza ❌ i ostrzega o prawie do natychmiastowego eksmisji

---

## Architektura — 6 agentów

```
Moduł 1: Analiza umowy
  ExtractorAgent  →  LegalAgent (RAG)  →  RiskAgent  →  AdvisorAgent
  
Moduł 2: Protokół
  PhotoAnalysisAgent (Gemini Vision)  →  ProtocolAgent
```

**Stack:** Python 3.11 · Flask · Google Gemini 2.5 Flash · Agno · Pydantic v2 · ChromaDB

---

## Instalacja i uruchomienie

```bash
# 1. Sklonuj repo i wejdź do katalogu
git clone https://github.com/DawidZabek/leaseguard
cd leaseguard

# 2. Utwórz środowisko wirtualne
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skonfiguruj klucz API
cp .env.example .env
# Uzupełnij GEMINI_API_KEY w pliku .env

# 5. Uruchom aplikację
python app.py
```

Aplikacja dostępna pod: **http://localhost:5000**

---

## Struktura plików

```
leaseguard/
├── app.py                  # Flask app + API endpoints
├── agents/
│   ├── extractor.py        # ExtractorAgent — wyciąga klauzule
│   ├── legal.py            # LegalAgent — RAG na ChromaDB
│   ├── risk.py             # RiskAgent — klasyfikacja ryzyka
│   ├── advisor.py          # AdvisorAgent — rekomendacja końcowa
│   ├── photo.py            # PhotoAnalysisAgent — Gemini Vision
│   └── protocol.py         # ProtocolAgent — generuje protokół
├── models/
│   └── schemas.py          # Pydantic models
├── rag/
│   └── setup.py            # ChromaDB + przepisy ustawy
├── templates/              # HTML (Flask/Jinja2)
├── static/                 # CSS + JS
├── data/                   # Przykładowe umowy do testów
└── requirements.txt
```

---

## Podstawa prawna

RAG oparty na **Ustawie z dnia 21 czerwca 2001 r. o ochronie praw lokatorów, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego** (Dz.U. 2001 nr 71 poz. 733 ze zm.) — pobierana z ISAP API (isap.sejm.gov.pl).
