from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import AnalyzeRequest, AnalysisReport, ReportRow, ExtractedEvents
from ingestion import clean_text
from extraction import extract_events_from_text
from compare import compare_events
from heuristics import apply_legal_heuristics
from report import generate_final_report
from filters import should_compare_events, group_omissions, comparison_cache
from translation import detect_language, translate_to_english, translate_text
from fastapi import UploadFile, File, Form
from schemas import UploadResponse
from ocr import extract_text_from_file

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

@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    statement_type: str = Form(...)
):
    """
    Handles PDF/Image upload, extracts text via OCR or PDF parsing.
    """
    print(f"Received file: {file.filename}, Type: {statement_type}")
    
    try:
        contents = await file.read()
        extraction_result = await extract_text_from_file(contents, file.filename)
        
        if extraction_result["method"] == "error":
            # Pass through specific errors (like Tesseract missing)
            raise HTTPException(status_code=500, detail=extraction_result["error"])
            
        return UploadResponse(
            filename=file.filename,
            message=f"Text extracted using {extraction_result['method']} ({extraction_result['confidence']} confidence)",
            content_preview=extraction_result["text"]  # Send full text as 'preview' for editing
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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

    # 1. Ingestion & Language Detection
    origin_text1 = clean_text(request.statement_1_text)
    origin_text2 = clean_text(request.statement_2_text)
    
    # Detect from combined text for better accuracy
    detected_lang = detect_language(origin_text1[:500] + " " + origin_text2[:500])
    print(f"DEBUG: Detected Language: {detected_lang}")

    # Translation (Input -> English)
    if detected_lang != "en":
        print(f"DEBUG: Translating input from {detected_lang} to English...")
        text1 = await translate_to_english(origin_text1, detected_lang)
        text2 = await translate_to_english(origin_text2, detected_lang)
    else:
        text1 = origin_text1
        text2 = origin_text2

    # 2. Extraction (on English text)
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

    # 3. Suppression Filters (Pre-LLM) & Comparison
    processed_count = 0
    skipped_count = 0
    
    print(f"DEBUG: Starting comparison loop for {len(events1)} x {len(events2)} events")
    
    for i, e1 in enumerate(events1):
        for j, e2 in enumerate(events2):
            # --- OBJECTIVE 1: SUPPRESSION RULES ---
            # print(f"DEBUG: Checking filter for {e1.event_id} vs {e2.event_id}")
            if not should_compare_events(e1, e2):
                skipped_count += 1
                # print(f"DEBUG: Skipped {e1.event_id} vs {e2.event_id}")
                continue

            processed_count += 1
            print(f"DEBUG: Comparing {e1.event_id} vs {e2.event_id}")
            comparison_result = await compare_events(e1, e2)
            
            # Use Heuristics
            row = apply_legal_heuristics(comparison_result, e1, e2)
            
            if row.classification != "consistent":
                 report_rows.append(row)
                 
    print(f"Comparison Stats: processed={processed_count}, skipped={skipped_count}, discrepancies={len(report_rows)}")

    # --- OBJECTIVE 2: GROUPING ---
    # report_rows = group_omissions(report_rows) # Placeholder for complex logic if implemented


    # 5. Report
    report = generate_final_report(report_rows, detected_lang)
    
    # 6. Translation (Output -> Detected Lang)
    report.input_language = detected_lang
    report.analysis_language = "en"
    
    if detected_lang != "en":
        print(f"DEBUG: Translating report back to {detected_lang}...")
        translated_rows = []
        for row in report.rows:
            # Translate visible fields
            row.classification = await translate_text(row.classification, detected_lang)
            row.explanation = await translate_text(row.explanation, detected_lang)
            row.legal_basis = await translate_text(row.legal_basis, detected_lang)
            row.severity = await translate_text(row.severity, detected_lang)
            # source_1 / source_2 might remain in English or be translated. 
            # Prompt says "Output format: classification, severity, explanation, source_sentence_original".
            # ReportRow doesn't strictly have "source_sentence_original" field yet, it relies on `source_sentence_refs`.
            # To be safe, we translate visible parts.
            translated_rows.append(row)
        
        report.rows = translated_rows
        report.disclaimer = await translate_text(report.disclaimer, detected_lang)

    return report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
