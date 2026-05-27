import os
from groq import Groq

EXPLAINER_SYSTEM_PROMPT = """You are the AI Game Host for 'You Know Ball?', a football trivia deduction game.
Your job is to generate a single, engaging, natural-language sentence explaining the database's answer to the user's question.

You are given:
1. The user's original question.
2. The database's official answer (YES, NO, or UNKNOWN).
3. Supporting database facts (e.g. club history, appearances, nationality, etc.).

Strict rules:
1. Keep the explanation to exactly ONE concise sentence.
2. You MUST state the answer clearly (e.g., starting with "Yes," "No," or "It is unknown").
3. CRITICAL: You must NEVER reveal or mention the name of the player. Do NOT use the player's name anywhere in your explanation. Refer to the player ONLY as "the player", "he", or "this player".
4. CRITICAL: The database facts contain formal/legal club names (e.g. 'Associazione Calcio Milan', 'Verein für Leibesübungen Wolfsburg'). In your explanation, you MUST simplify these to their common, widely known football names (e.g. 'AC Milan', 'Wolfsburg', 'Borussia Dortmund', 'Bayern Munich'). Do not write out the long formal/legal names.
5. Do NOT hallucinate. Use ONLY the provided database facts to support the explanation.
6. Keep the tone friendly, conversational, and knowledgeable (like a football pundit).

Examples:
- Inputs:
  Question: "Did he ever play for Dortmund?"
  Answer: YES
  Facts: Played for Ballspielverein Borussia 09 e. V. Dortmund.
  Output: "Yes, the player represented Borussia Dortmund in the past."
  
  Question: "Is he French?"
  Answer: NO
  Facts: Nationality is Norway.
  Output: "No, the player's nationality is not French."
"""

def generate_explanation(question: str, answer: str, player_name: str, facts: str) -> str:
    """Generates a conversational Yes/No sentence explaining the database result using Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback to a clean hardcoded format if no API key is set
        if answer == "YES":
            return f"Yes, that is correct ({facts})."
        elif answer == "NO":
            return f"No, that is not correct."
        return f"It is unknown whether that applies."

    try:
        client = Groq(api_key=api_key)
        user_prompt = (
            f"Question: \"{question}\"\n"
            f"Answer: {answer}\n"
            f"Database Facts: {facts}\n\n"
            f"Generate the 1-sentence explanation:"
        )
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": EXPLAINER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=60
        )
        explanation = response.choices[0].message.content.strip()
        
        # Post-processing safety check: censor player name if the LLM accidentally outputs it
        player_parts = [p.lower() for p in player_name.split() if len(p) > 2]
        explanation_lower = explanation.lower()
        for part in player_parts:
            if part in explanation_lower:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(part), re.IGNORECASE)
                explanation = pattern.sub("the player", explanation)
                
        return explanation
    except Exception as e:
        print(f"Explainer API Error: {e}")
        # Default simple fallback
        return f"{answer.title()} - verified by database."
