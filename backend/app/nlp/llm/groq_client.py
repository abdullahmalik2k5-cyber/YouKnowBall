import os
from groq import Groq
from app.nlp.llm.prompts import SYSTEM_PROMPT, get_user_prompt
from app.nlp.llm.validators import validate_llm_json

def parse_with_groq(question: str) -> dict:
    """Sends the question to Groq's Llama 3 8B model to extract intent and entities."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "type": "invalid",
            "value": None,
            "error_type": "no_api_key",
            "message": "Groq API key is not configured in your .env file."
        }
    
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
            if validated.get("type") == "invalid":
                return {
                    "type": "invalid",
                    "value": None,
                    "error_type": "unsupported_question",
                    "message": "I could not identify a valid question about positions, clubs, competitions, or nationality. Try asking something like: 'Is he a midfielder?' or 'Did he play for Chelsea?'"
                }
            return validated
        else:
            return {
                "type": "invalid",
                "value": None,
                "error_type": "validation_failed",
                "message": "The AI's response format was malformed. Please rephrase your question slightly."
            }
    except Exception as e:
        err_msg = str(e)
        if "limit" in err_msg.lower() or "rate" in err_msg.lower():
            return {
                "type": "invalid",
                "value": None,
                "error_type": "rate_limited",
                "message": "The AI is currently rate-limited. Please wait a few seconds and try again."
            }
        return {
            "type": "invalid",
            "value": None,
            "error_type": "api_error",
            "message": f"An API connection error occurred: {err_msg}."
        }
