import os
from groq import Groq

EXPLAINER_SYSTEM_PROMPT = """You are the AI Game Host for 'You Know Ball?', a football trivia deduction game.
Your job is to generate a single, engaging, natural-language sentence explaining the database's answer to the user's question.

You are given:
1. The user's original question.
2. The database's official answer (YES, NO, or UNKNOWN).
3. The hidden player's name.
4. Supporting database facts (e.g. club history, appearances, nationality, etc.).

Strict rules:
1. Keep the explanation to exactly ONE concise sentence.
2. You MUST state the answer clearly (e.g., starting with "Yes," "No," or "It is unknown").
3. Do NOT hallucinate. Use ONLY the provided database facts to support the explanation.
4. Keep the tone friendly, conversational, and knowledgeable (like a football pundit).

Examples:
- Inputs:
  Question: "Did he ever play in Italy?"
  Answer: YES
  Player: Erling Haaland
  Facts: Played for Molde, Bryne, Red Bull Salzburg, Borussia Dortmund, Manchester City.
  Output: "Yes, Erling Haaland has never played for an Italian club throughout his career." (Wait, if answer is YES, this example would say: "Yes, but Erling Haaland has actually never played for a club in Italy.")
  
  Let's correct:
  Question: "Did he ever play in Germany?"
  Answer: YES
  Player: Erling Haaland
  Facts: Played for Borussia Dortmund (2020-2022).
  Output: "Yes, Erling Haaland played for Borussia Dortmund in Germany between 2020 and 2022."
"""

def generate_explanation(question: str, answer: str, player_name: str, facts: str) -> str:
    """Generates a conversational Yes/No sentence explaining the database result using Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback to a clean hardcoded format if no API key is set
        if answer == "YES":
            return f"Yes, that is correct for {player_name} ({facts})."
        elif answer == "NO":
            return f"No, that is not correct for {player_name}."
        return f"It is unknown whether that applies to {player_name}."

    try:
        client = Groq(api_key=api_key)
        user_prompt = (
            f"Question: \"{question}\"\n"
            f"Answer: {answer}\n"
            f"Player Name: {player_name}\n"
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
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Explainer API Error: {e}")
        # Default simple fallback
        return f"{answer.title()} - verified by database."
