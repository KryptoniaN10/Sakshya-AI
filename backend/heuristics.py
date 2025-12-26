from schemas import ComparisonResult, ReportRow, Event

def apply_legal_heuristics(comparison: ComparisonResult, event1: Event, event2: Event) -> ReportRow:
    """
    Refines the LLM classification based on legal rules.
    """
    classification = comparison.classification
    explanation = comparison.explanation
    severity = "Minor"
    legal_basis = "General Consistency"

    # Rule 1: FIR Omission -> Downgrade severity
    if classification == "omission":
        if event1.statement_type == "FIR" or event2.statement_type == "FIR":
             severity = "Minor"
             legal_basis = "The FIR is not substantive evidence. It may be used only to corroborate or contradict its maker, and omissions must be assessed cautiously in light of surrounding circumstances."
        else:
             severity = "Material"
             legal_basis = "Omission of material facts in sworn testimony may amount to a contradiction."

    # Rule 2: Contradiction logic
    if classification == "contradiction":
        explanation_lower = explanation.lower()
        
        # Critical: Identity or Presence
        if "identity" in explanation_lower or "presence" in explanation_lower or "role" in explanation_lower:
            severity = "Critical"
            legal_basis = "Contradiction regarding the identity or core role of the accused goes to the root of the prosecution case."
        
        # Material: Weapon or Timeline
        elif "weapon" in explanation_lower or "gun" in explanation_lower or "knife" in explanation_lower:
            severity = "Material"
            legal_basis = "Material contradiction regarding the weapon used affects the credibility of the ocular account."
        elif "time" in explanation_lower and "minor" not in explanation_lower:
            severity = "Material"
            legal_basis = "Significant discrepancy in the timeline of events."
        
        # Default Material for other contradictions
        else:
            severity = "Material"
            legal_basis = "Material contradiction under Section 145 of the Bharatiya Sakshya Adhiniyam."

    # Rule 3: Minor Discrepancy
    if classification == "minor_discrepancy":
        severity = "Minor"
        legal_basis = "Minor discrepancies in time or detail are natural in human verification and do not necessarily falsify the testimony (Bharwada Bhoginbhai v. State of Gujarat)."
        
    if classification == "consistent":
        severity = "Minor" 
        legal_basis = "Corroboration under Section 157 of the Bharatiya Sakshya Adhiniyam."

    return ReportRow(
        id=f"{comparison.event_1_id}-{comparison.event_2_id}",
        source_1=f"{event1.statement_type}: {event1.actor} {event1.action}",
        source_2=f"{event2.statement_type}: {event2.actor} {event2.action}",
        classification=classification,
        severity=severity,
        legal_basis=legal_basis,
        source_sentence_refs=[event1.source_sentence, event2.source_sentence]
    )
