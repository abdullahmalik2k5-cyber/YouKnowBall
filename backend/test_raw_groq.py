import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load env vars
from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.nlp.parser import parse_question
from app.nlp.llm.groq_client import parse_with_groq
from groq import Groq
from app.nlp.llm.prompts import SYSTEM_PROMPT, get_user_prompt

def test_raw_groq():
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    questions = [
        "Does he play for the Merengues in Spain?",
        "Did he play for the team coached by Pep Guardiola currently?",
        "Has he ever won the Champions League?"
    ]
    
    print("=== RAW GROQ RESPONSES ===")
    for q in questions:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": get_user_prompt(q)}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        print(f"Question: \"{q}\"")
        print(f"Response: {response.choices[0].message.content}\n")

if __name__ == "__main__":
    test_raw_groq()
