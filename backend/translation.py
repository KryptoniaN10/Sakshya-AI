from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Supported Indian languages + English
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ml": "Malayalam",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali"
}

def detect_language(text: str) -> str:
    """
    Detects language using langdetect library.
    Returns ISO code (e.g., 'en', 'hi', 'ml').
    Default to 'en' on failure or short text.
    """
    if not text or len(text.strip()) < 10:
        return "en"
    
    try:
        lang = detect(text)
        # Check if supported, otherwise treat as English (or handle error)
        # For now, we trust the detector but only act if it's one of our target Indic languages
        if lang in SUPPORTED_LANGUAGES:
            return lang
        return "en" # Fallback for unknown langs to English processing
    except LangDetectException:
        return "en"

async def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translates text from source_lang to English using the LLM.
    """
    if source_lang == "en":
        return text

    if not GEMINI_API_KEY:
        print("WARNING: No API Key for translation. Returning original text.")
        return text

    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    prompt = f"""You are a professional legal translator. 
    Translate the following {SUPPORTED_LANGUAGES.get(source_lang, source_lang)} legal text into English.
    Preserve the legal meaning, sentence structure, and tone.
    Do NOT summarize. Provide a direct translation.
    
    Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Translation Error (to English): {e}")
        return text # Fail safe: return original

async def translate_text(text: str, target_lang: str) -> str:
    """
    Generic translator (English -> Target).
    """
    if target_lang == "en" or not text:
        return text

    if not GEMINI_API_KEY:
        return text

    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    target_lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    
    prompt = f"""Translate the following text into {target_lang_name}.
    Preserve legal terminology and tone.
    
    Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Translation Error (to {target_lang}): {e}")
        return text
