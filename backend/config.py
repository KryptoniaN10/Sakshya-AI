import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
# print(f"DEBUG: Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Model configuration
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Updated to working model

# Sarvam Speech-to-Text configuration
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    print("WARNING: SARVAM_API_KEY not found in environment variables. Speech-to-text will be disabled.")

# Endpoint and model name for Sarvam STT.
# Refer to Sarvam docs and override these via environment variables if needed.
SARVAM_STT_URL = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "sarvam-stt")

