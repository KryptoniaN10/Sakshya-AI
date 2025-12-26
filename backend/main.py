from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import AnalyzeRequest, AnalysisReport, ReportRow, ExtractedEvents
from ingestion import clean_text
from extraction import extract_events_from_text
from compare import compare_events
from heuristics import apply_legal_heuristics
from report import generate_final_report

app = FastAPI(title="Sakshya AI", description="AI-assisted legal decision support.")

# CORS - Allow all for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Sakshya AI Backend Running"}

@app.post("/analyze", response_model=AnalysisReport)
async def analyze_statements(request: AnalyzeRequest):
    """
    Main pipeline:
    1. Clean texts.
    2. Extract events (LLM).
    3. Compare events (LLM).
    4. Apply Legal Heuristics.
    5. Generate Report.
    """
    print(f"!!! RECEIVING REQUEST ON PORT 8005 !!! {request.statement_1_type} vs {request.statement_2_type}")

    # 1. Ingestion
    text1 = clean_text(request.statement_1_text)
    text2 = clean_text(request.statement_2_text)

    # 2. Extraction
    print("Extracting events...")
    events1 = await extract_events_from_text(text1, request.statement_1_type)
    events2 = await extract_events_from_text(text2, request.statement_2_type)
    
    print(f"Extracted {len(events1)} events from Doc 1 and {len(events2)} events from Doc 2.")

    # 3. Comparison & 4. Heuristics
    # Naive O(N*M) comparison for MVP. 
    # Ideally should clustering or pre-filtering, but for MVP we compare all.
    # To reduce LLM calls, we could use embeddings, but here we do direct LLM compare 
    # as per "Compare two extracted events" instruction.
    # However, N*M is expensive. We will try to filter to only relevant ones or 
    # just limit to top 5 events for the MVP demo if it gets too large.
    # For now, let's assume short statements (3-5 events max).
    
    report_rows = []
    
    # We only compare if we have events.
    # This logic assumes we want to find contradictions.
    # If Statement 1 says X and Statement 2 says nothing about X, it's an omission?
    # Or strict contradiction search.
    
    for e1 in events1:
        for e2 in events2:
            # We skip comparing if they are obviously unrelated? 
            # No, let the LLM decide or use "consistent" as default.
            # Optimization: Check if actors or actions match partially?
            # For MVP, full cross-comparison.
            
            comparison_result = await compare_events(e1, e2)
            
            # Use Heuristics
            row = apply_legal_heuristics(comparison_result, e1, e2)
            
            # We only keep rows that are NOT consistent (or Minor/Material/Critical)
            # Actually, we want to show everything or just the conflicts?
            # User wants "Confrontation table". Usually implies showing conflicts.
            # But let's show everything that isn't just "consistent" / "irrelevant".
            
            if row.classification != "consistent":
                 report_rows.append(row)
                 
    print(f"Found {len(report_rows)} discrepancies.")

    # 5. Report
    report = generate_final_report(report_rows)
    return report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
