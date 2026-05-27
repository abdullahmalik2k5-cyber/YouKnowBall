import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load env vars
from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.nlp.parser import parse_question

def test_nlp_layer():
    db = SessionLocal()
    
    test_cases = [
        "Is he a defender?",
        "Is he a Goalkeeper?",
        "Is he French?",
        "Is he from Germany?",
        "Did he ever play for Arsenal?",
        "Does he play for Real Madrid currently?",
        "Has he played in the Premier League?",
    ]
    
    print("=== TESTING RULE-BASED NLP LAYER ===")
    for q in test_cases:
        res = parse_question(db, q)
        print(f"Question: \"{q}\"")
        print(f"Parsed:   {res}\n")

    # If GROQ_API_KEY is configured, test LLM parsing
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print("=== TESTING LLM FALLBACK NLP LAYER (GROQ) ===")
        llm_test_cases = [
            "Does he play for the Merengues in Spain?",  # Real Madrid
            "Is he a striker?", # ATK
            "Did he play for the team coached by Pep Guardiola currently?", # Man City
        ]
        for q in llm_test_cases:
            res = parse_question(db, q)
            print(f"Question: \"{q}\"")
            print(f"Parsed:   {res}\n")
    else:
        print("Note: GROQ_API_KEY not configured. Skipping LLM tests.")

if __name__ == "__main__":
    test_nlp_layer()
