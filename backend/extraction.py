import json
import google.generativeai as genai
from schemas import ExtractedEvents, Event
from prompts import EXTRACTION_PROMPT
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def extract_events_from_text(text: str, statement_type: str) -> list[Event]:
    """
    Uses Gemini API to extract structured events.
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set.")
        return []

    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    prompt = EXTRACTION_PROMPT.format(statement_type=statement_type, text=text)

    print(f"DEBUG: Extracting from text (len={len(text)}): {text[:50]}...")
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        print(f"DEBUG: LLM Raw Response: {response.text}")
        
        # Clean the response - sometimes LLM adds markdown or extra text
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()
        
        result_json = json.loads(response_text)
        events_data = result_json.get("events", [])
        print(f"DEBUG: Parsed {len(events_data)} events.")
        
        events = []
        for e in events_data:
            events.append(Event(
                event_id=f"{statement_type}_{len(events)+1}", # Simple ID generation
                actor=e.get("actor", "Unknown"),
                action=e.get("action", "Unknown"),
                target=e.get("target"),
                time=e.get("time"),
                location=e.get("location"),
                source_sentence=e.get("source_sentence", ""),
                statement_type=statement_type # Force the type
            ))
            
        return events

    except json.JSONDecodeError as je:
        print(f"JSON Decode Error during LLM extraction: {je}")
        print(f"Response was: {response.text if 'response' in locals() else 'No response'}")
        return []
    except Exception as e:
        print(f"Error during LLM extraction: {e}")
        import traceback
        traceback.print_exc()
        return []
