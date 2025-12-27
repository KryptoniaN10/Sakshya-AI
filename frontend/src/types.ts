export interface ReportRow {
    id: string;
    source_1: string;
    source_2: string;
    classification: "contradiction" | "omission" | "consistent" | "minor_discrepancy";
    severity: "Minor" | "Material" | "Critical";
    legal_basis: string;
    source_sentence_refs: string[];
}

export interface AnalysisReport {
    input_language: string;
    analysis_language: string;
    rows: ReportRow[];
    disclaimer: string;
}

export interface AnalyzeRequest {
    statement_1_text: string;
    statement_1_type: string;
    statement_2_text: string;
    statement_2_type: string;
}
