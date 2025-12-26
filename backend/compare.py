import json
import google.generativeai as genai
from schemas import Event, ComparisonResult
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from prompts import COMPARISON_PROMPT

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def compare_events(event1: Event, event2: Event) -> ComparisonResult:
    if not GEMINI_API_KEY:
        return ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification="consistent",
            explanation="Mock consistency check (No API Key)"
        )

    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    print(f"DEBUG: Comparing Event {event1.event_id} vs {event2.event_id}")
    
    prompt = COMPARISON_PROMPT.format(
        type_1=event1.statement_type,
        actor_1=event1.actor,
        action_1=event1.action,
        target_1=event1.target,
        time_1=event1.time,
        location_1=event1.location,
        type_2=event2.statement_type,
        actor_2=event2.actor,
        action_2=event2.action,
        target_2=event2.target,
        time_2=event2.time,
        location_2=event2.location
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        print(f"DEBUG: Comparison LLM Response: {response.text}")
        
        result_json = json.loads(response.text)
        
        return ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification=result_json.get("classification", "consistent"),
            explanation=result_json.get("explanation", "No explanation provided.")
        )

    except Exception as e:
        print(f"Error during LLM comparison: {e}")
        return ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification="consistent", # Default to safe fallback
            explanation=f"Error during comparison: {str(e)}"
        )
