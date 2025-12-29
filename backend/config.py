import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
# print(f"DEBUG: Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Model configuration
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite" # Updated to working model 
