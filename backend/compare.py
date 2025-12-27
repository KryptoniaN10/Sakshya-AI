import json
import google.generativeai as genai
from schemas import Event, ComparisonResult
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from prompts import COMPARISON_PROMPT
from filters import comparison_cache, get_cache_key

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def compare_events(event1: Event, event2: Event) -> ComparisonResult:
    # --- OBJECTIVE 4: RATE LIMIT & DEDUPLICATION (CACHE) ---
    cache_key = get_cache_key(event1, event2)
    if cache_key in comparison_cache:
        print(f"DEBUG: Cache Hit for {cache_key}")
        cached_result = comparison_cache[cache_key]
        # Return a copy with correct IDs
        return ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification=cached_result.classification,
            explanation=cached_result.explanation
        )

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
        # print(f"DEBUG: Comparison LLM Response: {response.text}")
        
        result_json = json.loads(response.text)
        
        result = ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification=result_json.get("classification", "consistent"),
            explanation=result_json.get("explanation", "No explanation provided.")
        )
        
        # Save to cache
        comparison_cache[cache_key] = result
        return result

    except Exception as e:
        print(f"Error during LLM comparison: {e}")
        # --- OBJECTIVE 5: SAFETY FALLBACK ---
        # Use a valid classification literal as defined in schemas.py to avoid
        # Pydantic validation errors when constructing the response.
        return ComparisonResult(
            event_1_id=event1.event_id,
            event_2_id=event2.event_id,
            classification="consistent",
            explanation="Skipped analysis due to LLM error; treating as consistent for stability."
        )
