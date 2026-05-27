from sqlalchemy.orm import Session
from app.nlp.regex_patterns import parse_with_rules
from app.nlp.llm.groq_client import parse_with_groq

def parse_question(db: Session, question: str) -> dict:
    """Orchestrates question parsing: Rule-based patterns first, then Groq LLM fallback."""
    cleaned = question.strip()
    if not cleaned:
        return {
            "type": "invalid",
            "value": None,
            "error_type": "empty_question",
            "message": "You entered an empty question. Please ask something!"
        }
        
    # Layer 1: Rule-Based Parser (0ms latency, free)
    result = parse_with_rules(db, cleaned)
    if result:
        return result
        
    # Layer 2: LLM Fallback (Groq API)
    result = parse_with_groq(cleaned)
    return result
