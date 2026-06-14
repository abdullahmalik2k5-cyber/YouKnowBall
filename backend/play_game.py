"""
You Know Ball? — CLI game runner.

Usage:
    python play_game.py [difficulty]

    difficulty: easy | medium | hard  (default: hard)

Examples:
    python play_game.py           # Hard mode (all top-5 league players)
    python play_game.py medium    # Medium mode (top-6 clubs per league, 500+ mins)
    python play_game.py easy      # Easy mode (top-4 clubs per league, 500+ mins)
"""

import sys
import os
import re

# Add backend directory to sys.path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.nlp.parser import parse_question
from app.game.candidate_engine.engine import CandidateEngine
from app.game.difficulty import select_hidden_player
from app.game.queries.handlers import (
    handle_nationality,
    handle_current_club,
    handle_club_history,
    handle_position,
    handle_competition_history,
    handle_continent,
    handle_age,
    handle_foot,
)
from app.nlp.llm.explainer import generate_explanation


DIFFICULTY_LABELS = {
    "easy": "🟢 Reel Watcher (Easy)   — top-4 clubs per league, recognised starters",
    "medium": "🟡 Mid (Medium)          — top-6 clubs per league, 500+ minutes played",
    "hard": "🔴 Ball Knower (Hard)    — all players from the top-5 European leagues",
}


def normalize_guess(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip().lower())


def guess_matches(guess: str, target: str) -> bool:
    """
    Returns True if the guess is a close enough match for the target name.
    Accepts:
      - Exact full name match (case-insensitive)
      - Full last name match (e.g. 'Haaland' for 'Erling Haaland')
      - Reversed name match (e.g. 'Messi Lionel' for 'Lionel Messi')
    Does NOT accept single-letter or short substring guesses.
    """
    g = normalize_guess(guess)
    t = normalize_guess(target)

    if g == t:
        return True

    # Allow matching on last name only (must be > 3 chars to prevent abuse)
    parts = t.split()
    if len(parts) > 1:
        last_name = parts[-1]
        if len(last_name) > 3 and g == last_name:
            return True
        # Reversed order match (first/last swapped)
        reversed_name = " ".join(reversed(parts))
        if g == reversed_name:
            return True

    return False


def main():
    # ── Parse difficulty from CLI ─────────────────────────────────────────────
    difficulty = sys.argv[1].lower().strip() if len(sys.argv) > 1 else "hard"
    if difficulty not in ("easy", "medium", "hard"):
        print(f"⚠️  Unknown difficulty '{difficulty}'. Defaulting to 'hard'.")
        difficulty = "hard"

    db = SessionLocal()

    # ── Select hidden player ──────────────────────────────────────────────────
    print(f"\n🔄 Selecting a hidden player [{difficulty.upper()} mode]...")
    result = select_hidden_player(db, difficulty)
    if not result:
        print("❌ Error: No eligible players found for this difficulty. Please run ingestion first.")
        return

    hidden_player_id, hidden_player_name = result

    # ── Game header ───────────────────────────────────────────────────────────
    print("\n⚽ ═══════════════════════════════════════════════════════════ ⚽")
    print("                       YOU KNOW BALL?")
    print(f"                 {DIFFICULTY_LABELS[difficulty]}")
    print("⚽ ═══════════════════════════════════════════════════════════ ⚽")
    print("\nRules:")
    print("  • You have up to 20 yes/no questions to narrow down the player.")
    print("  • You have exactly 3 guesses to name them.")
    print("  • Type 'g' or 'guess' to submit a guess at any time.")
    print("  • Ask anything: nationality, club, position, league, continent, age, foot, etc.")
    print("  • Type 'q' to quit.\n")

    # ── Initialise candidate engine ───────────────────────────────────────────
    engine = CandidateEngine(db, difficulty)
    print(f"\n📊 Candidate pool: {engine.get_remaining_count()} players\n")
    print("═" * 60 + "\n")

    question_count = 0
    max_questions = 20
    guess_count = 0
    max_guesses = 3
    consecutive_invalid = 0  # Charge a turn after 3 consecutive invalid inputs

    while True:
        try:
            # ── Game over check ───────────────────────────────────────────────
            if question_count >= max_questions:
                print(f"\n⏰ Game Over! You used all {max_questions} questions.")
                print(f"   The hidden player was: {hidden_player_name}")
                break

            status = f"[Q: {question_count}/{max_questions}  |  Guesses: {guess_count}/{max_guesses}  |  Pool: {engine.get_remaining_count()}]"
            action = input(f"{status}\n❓ Your question (or 'g'=guess, 'q'=quit): ").strip()

            if not action:
                continue

            if action.lower() == 'q':
                print(f"\n👋 Quitting. The hidden player was: {hidden_player_name}")
                break

            # ── Guess mode ────────────────────────────────────────────────────
            if action.lower() in ('g', 'guess'):
                guess_count += 1
                player_guess = input(f"🤔 Your guess ({guess_count}/{max_guesses}): ").strip()

                if guess_matches(player_guess, hidden_player_name):
                    print(f"\n🏆 CORRECT! The player was {hidden_player_name}! Outstanding!")
                    break
                else:
                    print(f"❌ Wrong guess! That is not the player.")
                    if guess_count >= max_guesses:
                        print(f"\n💀 No guesses left! The player was: {hidden_player_name}")
                        break
                    remaining = max_guesses - guess_count
                    print(f"   {remaining} guess(es) remaining. Keep questioning!\n")
                continue

            # ── Question mode ─────────────────────────────────────────────────
            question = action
            print("\n🤖 Parsing your question...")
            parsed = parse_question(db, question)

            if parsed["type"] == "invalid" or not parsed.get("value"):
                err_msg = parsed.get(
                    "message",
                    "I couldn't understand that question. Try asking about: nationality, "
                    "continent, club, position, league, age, or preferred foot."
                )
                print(f"⚠️  {err_msg}")
                consecutive_invalid += 1
                if consecutive_invalid >= 3:
                    # Charge a question turn after 3 consecutive invalid inputs
                    question_count += 1
                    consecutive_invalid = 0
                    print(f"   (3 invalid questions in a row — turn deducted. {max_questions - question_count} turns left.)\n")
                else:
                    print(f"   (No turn charged — invalid #{consecutive_invalid}/3)\n")
                continue

            consecutive_invalid = 0  # Reset on a valid question
            question_count += 1
            q_type = parsed["type"]
            q_value = parsed["value"]

            print(f"   → Parsed as: type='{q_type}', value='{q_value}'")

            # ── Dispatch to handler ────────────────────────────────────────────
            answer = "UNKNOWN"
            fact_details = ""

            if q_type == "nationality":
                answer, fact_details = handle_nationality(db, hidden_player_id, q_value)
                engine.filter_by_nationality(q_value, answer)

            elif q_type == "current_club":
                answer, fact_details = handle_current_club(db, hidden_player_id, q_value)
                engine.filter_by_current_club(q_value, answer)

            elif q_type == "club_history":
                answer, fact_details = handle_club_history(db, hidden_player_id, q_value)
                engine.filter_by_club_history(q_value, answer)

            elif q_type == "position":
                answer, fact_details = handle_position(db, hidden_player_id, q_value)
                engine.filter_by_position(q_value, answer)

            elif q_type == "competition":
                answer, fact_details = handle_competition_history(db, hidden_player_id, q_value)
                engine.filter_by_competition_history(q_value, answer)

            elif q_type == "continent":
                answer, fact_details = handle_continent(db, hidden_player_id, q_value)
                engine.filter_by_continent(q_value, answer)

            elif q_type == "age":
                operator = q_value["operator"]
                years = q_value["years"]
                answer, fact_details = handle_age(db, hidden_player_id, operator, years)
                engine.filter_by_age(operator, years, answer)

            elif q_type == "foot":
                answer, fact_details = handle_foot(db, hidden_player_id, q_value)
                engine.filter_by_foot(q_value, answer)

            else:
                print(f"⚠️  Question type '{q_type}' is not yet handled. No turn charged.")
                question_count -= 1
                continue

            # ── Generate AI host explanation ───────────────────────────────────
            explanation = generate_explanation(question, answer, hidden_player_name, fact_details)

            answer_emoji = {"YES": "✅", "NO": "❌", "UNKNOWN": "❓"}.get(answer, "❓")
            print(f"\n{answer_emoji} [{answer}] — {explanation}")
            print(f"   📊 Candidates remaining: {engine.get_remaining_count()}")
            print("\n" + "─" * 60 + "\n")

        except KeyboardInterrupt:
            print(f"\n\n👋 Interrupted. The hidden player was: {hidden_player_name}")
            break


if __name__ == "__main__":
    main()
