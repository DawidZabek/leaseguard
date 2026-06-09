import os
import re
import requests
import chromadb
from chromadb.utils import embedding_functions
from bs4 import BeautifulSoup

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

# Ustawa o ochronie praw lokatorów — Dz.U. 2001 nr 71 poz. 733
ISAP_ELI_URL = "https://api.sejm.gov.pl/eli/acts/DU/2001/733/text.html"

# Artykuły kluczowe dla najmu — pobierane priorytetowo
KEY_ARTICLES = {1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 21, 25, 26, 28}


def _fetch_law_from_isap() -> list[dict]:
    """Pobiera tekst ustawy z ISAP ELI API i zwraca listę chunków (artykuł → tekst)."""
    headers = {"User-Agent": "LeaseGuard/1.0 (projekt edukacyjny; kontakt: student)"}
    response = requests.get(ISAP_ELI_URL, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    chunks = []

    # Każdy artykuł ma id zawierający "arti_N"
    article_divs = soup.find_all("div", id=re.compile(r"arti_\d+$"))

    for div in article_divs:
        art_id = div.get("id", "")
        match = re.search(r"arti_(\d+)$", art_id)
        if not match:
            continue
        art_num = int(match.group(1))

        # Pobierz czysty tekst artykułu (bez tagów HTML)
        raw_text = div.get_text(separator=" ", strip=True)
        # Normalizuj białe znaki
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        if len(raw_text) < 30:
            continue

        chunks.append({
            "id": f"art_{art_num}",
            "text": raw_text,
            "article": f"art. {art_num}",
            "topic": f"artykuł {art_num} ustawy o ochronie praw lokatorów",
            "priority": art_num in KEY_ARTICLES,
        })

    return chunks


def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="tenant_law",
        embedding_function=ef,
        metadata={"description": "Ustawa o ochronie praw lokatorów — źródło: ISAP ELI API"},
    )
    return collection


def setup_rag() -> None:
    """Inicjalizuje ChromaDB. Pobiera ustawę z ISAP API lub używa fallbacku."""
    collection = get_chroma_collection()

    if collection.count() > 0:
        return

    print("RAG: pobieranie ustawy z ISAP ELI API (api.sejm.gov.pl)...")
    try:
        chunks = _fetch_law_from_isap()
        if not chunks:
            raise ValueError("Brak artykułów w odpowiedzi ISAP")
        print(f"RAG: pobrano {len(chunks)} artykułów z ISAP API")
    except Exception as e:
        print(f"RAG: błąd pobierania z ISAP ({e}), używam wbudowanego fallbacku")
        chunks = _get_fallback_chunks()

    documents = [c["text"] for c in chunks]
    metadatas = [{"article": c["article"], "topic": c["topic"]} for c in chunks]
    ids = [c["id"] for c in chunks]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"RAG: załadowano {len(chunks)} przepisów do ChromaDB")


# Zawsze dołączane — kaucja, podwyżka, wypowiedzenie, prawo do używania lokalu
PINNED_ARTICLE_IDS = ["art_6", "art_8", "art_9", "art_11"]
# Maksymalna długość tekstu artykułu w prompcie (długie artykuły skracamy)
ARTICLE_EXCERPT_LIMIT = 400


def _excerpt(text: str) -> str:
    if len(text) <= ARTICLE_EXCERPT_LIMIT:
        return text
    return text[:ARTICLE_EXCERPT_LIMIT] + "…"


def query_law(query: str, n_results: int = 3) -> list[dict]:
    """Zwraca przypięte artykuły kluczowe + semantyczne wyniki dla zapytania."""
    collection = get_chroma_collection()
    if collection.count() == 0:
        setup_rag()

    # Zawsze dołącz kluczowe artykuły
    chunks: list[dict] = []
    seen_ids: set[str] = set()
    pinned = collection.get(ids=PINNED_ARTICLE_IDS)
    for i, doc in enumerate(pinned["documents"]):
        if doc:
            art_id = PINNED_ARTICLE_IDS[i]
            seen_ids.add(art_id)
            chunks.append({
                "text": _excerpt(doc),
                "article": pinned["metadatas"][i]["article"],
                "topic": pinned["metadatas"][i]["topic"],
            })

    # Semantyczne uzupełnienie dla pozostałych tematów
    extra = collection.query(query_texts=[query], n_results=min(n_results + 3, collection.count()))
    for i, doc in enumerate(extra["documents"][0]):
        meta = extra["metadatas"][0][i]
        art_id = extra["ids"][0][i]
        if art_id not in seen_ids and len(chunks) < len(PINNED_ARTICLE_IDS) + n_results:
            seen_ids.add(art_id)
            chunks.append({
                "text": _excerpt(doc),
                "article": meta["article"],
                "topic": meta["topic"],
            })

    return chunks


def reset_rag() -> None:
    """Usuwa i odbudowuje bazę RAG (np. po aktualizacji ustawy)."""
    import shutil
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    setup_rag()


# --- Fallback: kluczowe przepisy na wypadek braku dostępu do ISAP ---

def _get_fallback_chunks() -> list[dict]:
    return [
        {
            "id": "art_6_1",
            "text": "Art. 6. § 1. Zawarcie umowy najmu może być uzależnione od wpłacenia przez najemcę kaucji zabezpieczającej pokrycie należności z tytułu najmu lokalu, przysługujących wynajmującemu w dniu opróżnienia lokalu. Kaucja nie może przekraczać dwunastokrotności miesięcznego czynszu za dany lokal, obliczonego według stawki czynszu obowiązującej w dniu zawarcia umowy najmu.",
            "article": "art. 6 ust. 1", "topic": "kaucja",
        },
        {
            "id": "art_6_4",
            "text": "Art. 6. § 4. Zwrot zwaloryzowanej kaucji następuje w kwocie równej iloczynowi kwoty miesięcznego czynszu obowiązującego w dniu zwrotu kaucji i krotności czynszu przyjętej przy pobieraniu kaucji. Kaucja podlega zwrotowi w ciągu miesiąca od dnia opróżnienia lokalu lub nabycia jego własności przez najemcę, po potrąceniu należności wynajmującego z tytułu najmu lokalu.",
            "article": "art. 6 ust. 4", "topic": "zwrot kaucji",
        },
        {
            "id": "art_8a",
            "text": "Art. 8a. Właściciel może podwyższyć czynsz albo inne opłaty za używanie lokalu, wypowiadając jego dotychczasową wysokość, najpóźniej na koniec miesiąca kalendarzowego, z zachowaniem terminów wypowiedzenia. Termin wypowiedzenia wysokości czynszu albo innych opłat za używanie lokalu wynosi 3 miesiące, chyba że strony w umowie ustalą termin dłuższy.",
            "article": "art. 8a", "topic": "podwyżka czynszu",
        },
        {
            "id": "art_11_2",
            "text": "Art. 11. § 2. Nie później niż na miesiąc naprzód, na koniec miesiąca kalendarzowego, właściciel może wypowiedzieć stosunek prawny, jeżeli lokator jest w zwłoce z zapłatą czynszu za co najmniej trzy pełne okresy płatności lub używa lokalu w sposób sprzeczny z umową.",
            "article": "art. 11 ust. 2", "topic": "wypowiedzenie przez właściciela",
        },
        {
            "id": "art_11_4",
            "text": "Art. 11. § 4. Nie później niż na trzy lata naprzód, na koniec miesiąca kalendarzowego, właściciel może wypowiedzieć stosunek prawny lokatorowi, o ile zamierza zamieszkać w należącym do niego lokalu.",
            "article": "art. 11 ust. 4", "topic": "wypowiedzenie właściciel zamieszkanie",
        },
        {
            "id": "art_6b",
            "text": "Art. 6b. Wynajmujący jest obowiązany do zapewnienia sprawnego działania istniejących instalacji i urządzeń związanych z budynkiem umożliwiających najemcy korzystanie z wody, paliw gazowych i ciekłych, ciepła, energii elektrycznej, dźwigów osobowych oraz innych instalacji i urządzeń stanowiących wyposażenie lokalu i budynku.",
            "article": "art. 6b", "topic": "obowiązki wynajmującego instalacje",
        },
        {
            "id": "art_6e",
            "text": "Art. 6e. Najemca jest obowiązany utrzymywać lokal oraz pomieszczenia, do których używania jest uprawniony, we właściwym stanie technicznym i higieniczno-sanitarnym oraz przestrzegać porządku domowego.",
            "article": "art. 6e", "topic": "obowiązki najemcy",
        },
        {
            "id": "art_19a",
            "text": "Art. 19a. Umową najmu okazjonalnego lokalu jest umowa najmu lokalu służącego do zaspokajania potrzeb mieszkaniowych, zawarta na czas oznaczony, nie dłuższy niż 10 lat.",
            "article": "art. 19a", "topic": "najem okazjonalny",
        },
    ]
