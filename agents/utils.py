import os
import re
import time
import google.generativeai as genai

# Ładuj wszystkie dostępne klucze: GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3, ...
def _load_api_keys() -> list[str]:
    keys = []
    primary = os.getenv("GEMINI_API_KEY", "").strip()
    if primary:
        keys.append(primary)
    i = 2
    while True:
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if not k:
            break
        keys.append(k)
        i += 1
    return keys

API_KEYS = _load_api_keys()

MODELS_FALLBACK = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]

# Modele z wyczerpanym limitem dziennym — per klucz API
_daily_exhausted: dict[str, set[str]] = {}


def _is_daily_limit(error: Exception) -> bool:
    return "PerDay" in str(error)


def _is_minute_limit(error: Exception) -> bool:
    return "PerMinute" in str(error)


def _retry_delay(error: Exception) -> int:
    match = re.search(r"retry_delay \{ seconds: (\d+)", str(error))
    return int(match.group(1)) + 2 if match else 30


def generate_with_fallback(prompt: str, image_data: dict | None = None) -> str:
    if not API_KEYS:
        raise RuntimeError("Brak klucza API. Ustaw GEMINI_API_KEY w pliku .env")

    last_error = None

    for api_key in API_KEYS:
        exhausted = _daily_exhausted.get(api_key, set())
        available_models = [m for m in MODELS_FALLBACK if m not in exhausted]

        if not available_models:
            # Wszystkie modele wyczerpane dla tego klucza — reset i próbuj dalej
            _daily_exhausted[api_key] = set()
            available_models = list(MODELS_FALLBACK)

        genai.configure(api_key=api_key)

        for model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                content = [image_data, prompt] if image_data else prompt
                response = model.generate_content(content)
                return response.text
            except Exception as e:
                err_str = str(e)
                if "429" not in err_str and "RESOURCE_EXHAUSTED" not in err_str:
                    raise

                if _is_daily_limit(e):
                    _daily_exhausted.setdefault(api_key, set()).add(model_name)
                    last_error = e
                    continue

                if _is_minute_limit(e):
                    wait = _retry_delay(e)
                    time.sleep(wait)
                    try:
                        response = model.generate_content(content)
                        return response.text
                    except Exception:
                        last_error = e
                        continue

                last_error = e
                continue

    raise last_error
