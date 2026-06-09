import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Fallback chain — jeśli model przekroczy limit, próbuje następny
MODELS_FALLBACK = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]


def generate_with_fallback(prompt: str, image_data: dict | None = None) -> str:
    last_error = None
    for model_name in MODELS_FALLBACK:
        try:
            model = genai.GenerativeModel(model_name)
            if image_data:
                response = model.generate_content([image_data, prompt])
            else:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
                last_error = e
                continue
            raise
    raise last_error
