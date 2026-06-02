import os
import requests
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

# Kluczowe przepisy ustawy o ochronie praw lokatorów (Dz.U. 2001 nr 71 poz. 733)
# Załadowane statycznie jako fallback gdy ISAP API niedostępne
TENANT_LAW_CHUNKS = [
    {
        "id": "art_6_1",
        "text": "Art. 6. § 1. Zawarcie umowy najmu może być uzależnione od wpłacenia przez najemcę kaucji zabezpieczającej pokrycie należności z tytułu najmu lokalu, przysługujących wynajmującemu w dniu opróżnienia lokalu. Kaucja nie może przekraczać dwunastokrotności miesięcznego czynszu za dany lokal, obliczonego według stawki czynszu obowiązującej w dniu zawarcia umowy najmu.",
        "article": "art. 6 ust. 1",
        "topic": "kaucja"
    },
    {
        "id": "art_6_2",
        "text": "Art. 6. § 2. W przypadku najmu okazjonalnego lokalu kaucja nie może przekraczać sześciokrotności miesięcznego czynszu za dany lokal, obliczonego według stawki czynszu obowiązującej w dniu zawarcia umowy najmu.",
        "article": "art. 6 ust. 2",
        "topic": "kaucja najem okazjonalny"
    },
    {
        "id": "art_6_4",
        "text": "Art. 6. § 4. Zwrot zwaloryzowanej kaucji następuje w kwocie równej iloczynowi kwoty miesięcznego czynszu obowiązującego w dniu zwrotu kaucji i krotności czynszu przyjętej przy pobieraniu kaucji, jednak w kwocie nie niższej niż kaucja pobrana. Kaucja podlega zwrotowi w ciągu miesiąca od dnia opróżnienia lokalu lub nabycia jego własności przez najemcę, po potrąceniu należności wynajmującego z tytułu najmu lokalu.",
        "article": "art. 6 ust. 4",
        "topic": "zwrot kaucji"
    },
    {
        "id": "art_8a",
        "text": "Art. 8a. Właściciel może podwyższyć czynsz albo inne opłaty za używanie lokalu, wypowiadając jego dotychczasową wysokość, najpóźniej na koniec miesiąca kalendarzowego, z zachowaniem terminów wypowiedzenia. Termin wypowiedzenia wysokości czynszu albo innych opłat za używanie lokalu wynosi 3 miesiące, chyba że strony w umowie ustalą termin dłuższy.",
        "article": "art. 8a",
        "topic": "podwyżka czynszu"
    },
    {
        "id": "art_9",
        "text": "Art. 9. § 1. Jeżeli podwyżka czynszu albo innych opłat za używanie lokalu przekracza w danym roku kalendarzowym wskaźnik inflacji ogłoszony przez Prezesa Głównego Urzędu Statystycznego, lokator może zakwestionować podwyżkę, składając pisemne oświadczenie w terminie 2 miesięcy od dnia wypowiedzenia.",
        "article": "art. 9",
        "topic": "kwestionowanie podwyżki"
    },
    {
        "id": "art_10",
        "text": "Art. 10. § 1. Właściciel lokalu, w którym czynsz jest niższy niż 3% wartości odtworzeniowej lokalu w skali roku, może dokonać podwyżki czynszu jednorazowo lub w etapach pod warunkiem, że na żądanie lokatora złoży na piśmie przyczynę podwyżki i jej kalkulację.",
        "article": "art. 10",
        "topic": "podwyżka czynszu powyżej 3%"
    },
    {
        "id": "art_11_1",
        "text": "Art. 11. § 1. Jeżeli lokator jest uprawniony do odpłatnego używania lokalu, wypowiedzenie przez właściciela stosunku prawnego może nastąpić tylko z przyczyn określonych w ust. 2–5 oraz w art. 21 ust. 4 i 5 niniejszej ustawy.",
        "article": "art. 11 ust. 1",
        "topic": "wypowiedzenie umowy"
    },
    {
        "id": "art_11_2",
        "text": "Art. 11. § 2. Nie później niż na miesiąc naprzód, na koniec miesiąca kalendarzowego, właściciel może wypowiedzieć stosunek prawny, jeżeli lokator: 1) pomimo pisemnego upomnienia nadal używa lokalu w sposób sprzeczny z umową lub niezgodnie z jego przeznaczeniem lub zaniedbuje obowiązki, dopuszczając do powstania szkód, lub niszczy urządzenia przeznaczone do wspólnego korzystania przez mieszkańców albo wykracza w sposób rażący lub uporczywy przeciwko porządkowi domowemu; 2) jest w zwłoce z zapłatą czynszu, innych opłat za używanie lokalu lub opłat niezależnych od właściciela pobieranych przez właściciela za co najmniej trzy pełne okresy płatności pomimo uprzedzenia go na piśmie o zamiarze wypowiedzenia stosunku prawnego i wyznaczenia dodatkowego, miesięcznego terminu do zapłaty zaległych i bieżących należności; 3) wynajął, podnajął albo oddał do bezpłatnego używania lokal lub jego część bez wymaganej pisemnej zgody właściciela.",
        "article": "art. 11 ust. 2",
        "topic": "przyczyny wypowiedzenia przez właściciela"
    },
    {
        "id": "art_11_4",
        "text": "Art. 11. § 4. Nie później niż na trzy lata naprzód, na koniec miesiąca kalendarzowego, właściciel może wypowiedzieć stosunek prawny lokatorowi, o ile zamierza zamieszkać w należącym do niego lokalu.",
        "article": "art. 11 ust. 4",
        "topic": "wypowiedzenie właściciel zamieszkanie"
    },
    {
        "id": "art_6e",
        "text": "Art. 6e. § 1. Najemca jest obowiązany utrzymywać lokal oraz pomieszczenia, do których używania jest uprawniony, we właściwym stanie technicznym i higieniczno-sanitarnym oraz przestrzegać porządku domowego. Najemca jest też obowiązany dbać i chronić przed uszkodzeniem lub dewastacją części budynku przeznaczone do wspólnego użytku.",
        "article": "art. 6e",
        "topic": "obowiązki najemcy"
    },
    {
        "id": "art_6c",
        "text": "Art. 6c. Najemca może wprowadzić w lokalu ulepszenia tylko za zgodą wynajmującego i na podstawie pisemnej umowy określającej sposób rozliczeń z tego tytułu.",
        "article": "art. 6c",
        "topic": "ulepszenia w lokalu"
    },
    {
        "id": "art_19a",
        "text": "Art. 19a. Umową najmu okazjonalnego lokalu jest umowa najmu lokalu służącego do zaspokajania potrzeb mieszkaniowych, zawarta na czas oznaczony, nie dłuższy niż 10 lat.",
        "article": "art. 19a",
        "topic": "najem okazjonalny"
    },
    {
        "id": "art_6b",
        "text": "Art. 6b. § 1. Wynajmujący jest obowiązany do zapewnienia sprawnego działania istniejących instalacji i urządzeń związanych z budynkiem umożliwiających najemcy korzystanie z wody, paliw gazowych i ciekłych, ciepła, energii elektrycznej, dźwigów osobowych oraz innych instalacji i urządzeń stanowiących wyposażenie lokalu i budynku.",
        "article": "art. 6b",
        "topic": "obowiązki wynajmującego instalacje"
    },
    {
        "id": "art_6d",
        "text": "Art. 6d. Najemca jest obowiązany informować wynajmującego o wszelkich uszkodzeniach i awariach wymagających naprawy przez wynajmującego niezwłocznie po ich stwierdzeniu.",
        "article": "art. 6d",
        "topic": "informowanie o usterkach"
    },
    {
        "id": "art_15",
        "text": "Art. 15. § 1. Jeżeli lokator jest uprawniony do używania lokalu, a zajmuje lokal o powierzchni użytkowej przekraczającej 80 m² lub lokal wybudowany po dniu 5 listopada 1980 r., właściciel, który planuje wykonanie robót budowlanych wymagających opróżnienia lokalu, jest obowiązany zapewnić lokal zamienny.",
        "article": "art. 15",
        "topic": "lokal zamienny remont"
    },
]


def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="tenant_law",
        embedding_function=ef,
        metadata={"description": "Ustawa o ochronie praw lokatorów"}
    )
    return collection


def setup_rag():
    """Inicjalizuje ChromaDB z przepisami ustawy o ochronie praw lokatorów."""
    collection = get_chroma_collection()

    if collection.count() > 0:
        return collection

    documents = [chunk["text"] for chunk in TENANT_LAW_CHUNKS]
    metadatas = [{"article": c["article"], "topic": c["topic"]} for c in TENANT_LAW_CHUNKS]
    ids = [chunk["id"] for chunk in TENANT_LAW_CHUNKS]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"RAG: załadowano {len(TENANT_LAW_CHUNKS)} przepisów do ChromaDB")
    return collection


def query_law(query: str, n_results: int = 3) -> list[dict]:
    """Wyszukuje najbardziej relevantne przepisy dla danego zapytania."""
    collection = get_chroma_collection()
    if collection.count() == 0:
        setup_rag()

    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "article": results["metadatas"][0][i]["article"],
            "topic": results["metadatas"][0][i]["topic"],
        })
    return chunks
