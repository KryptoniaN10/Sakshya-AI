from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- Event/Extraction Models ---

class Event(BaseModel):
    event_id: str
    actor: str
    action: str
    target: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    source_sentence: str
    statement_type: Literal["FIR", "Section 161", "Section 164", "Court Deposition"]

class ExtractedEvents(BaseModel):
    events: List[Event]

# --- Comparison Models ---

class ComparisonResult(BaseModel):
    event_1_id: str
    event_2_id: str
    classification: Literal["contradiction", "omission", "consistent", "minor_discrepancy"]
    explanation: str
    
class ComparisonRequest(BaseModel):
    events_list_1: List[Event]
    events_list_2: List[Event]

# --- Report Models ---

class ReportRow(BaseModel):
    id: str
    source_1: str # e.g., "FIR Event: Actor hit Target"
    source_2: str # e.g., "161 Event: Actor slapped Target"
    classification: Literal["contradiction", "omission", "consistent", "minor_discrepancy"]
    severity: Literal["Minor", "Material", "Critical"]
    legal_basis: str
    source_sentence_refs: List[str]
    # For transparency, we might want original and English refs?
    # For now, source_sentence_refs will hold the ORIGINAL text logic if we map back.
    # But extraction gives English events. This is tricky.
    # Let's add explicit fields if needed, but per requirement "Render final results in input language"
    # we just translate the fields in place.

class AnalysisReport(BaseModel):
    input_language: str
    analysis_language: str = "en"
    rows: List[ReportRow]
    disclaimer: str

# --- API Request/Response Models ---

class UploadResponse(BaseModel):
    filename: str
    message: str
    content_preview: str

class AnalyzeRequest(BaseModel):
    statement_1_text: str
    statement_1_type: str
    statement_2_text: str
    statement_2_type: str
