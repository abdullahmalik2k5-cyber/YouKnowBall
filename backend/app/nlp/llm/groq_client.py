import os
from groq import Groq
from app.nlp.llm.prompts import SYSTEM_PROMPT, get_user_prompt
from app.nlp.llm.validators import validate_llm_json

def parse_with_groq(question: str) -> dict:
    """Sends the question to Groq's Llama 3 8B model to extract intent and entities."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Silently fail to fallback mode
        return {"type": "invalid", "value": None}
    
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": get_user_prompt(question)}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        validated = validate_llm_json(content)
        if validated:
            return validated
    except Exception as e:
        print(f"Groq API Error: {e}")
    
    return {"type": "invalid", "value": None}
