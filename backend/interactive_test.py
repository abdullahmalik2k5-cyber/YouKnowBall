"""
interactive_test.py — CLI interactive tester locked to Erling Haaland.

Fixed issues vs original:
  - Uses safe guess_matches() (no substring cheat)
  - Uses handlers module for all question types (consistent with play_game.py)
  - Supports ALL question types: nationality, current_club, club_history, position,
    competition, big_six, continent, age, foot
  - Charges a turn penalty after 3 consecutive invalid inputs
"""
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.nlp.parser import parse_question
from app.game.queries.handlers import (
    handle_nationality,
    handle_current_club,
    handle_club_history,
    handle_position,
    handle_competition_history,
    handle_big_six,
    handle_continent,
    handle_age,
    handle_foot,
)
from app.game.candidate_engine.engine import CandidateEngine
from app.nlp.llm.explainer import generate_explanation
from sqlalchemy import text


def normalize_guess(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip().lower())


def guess_matches(guess: str, target: str) -> bool:
    """
    Safe guess matching — exact full name, last name only, or reversed name.
    Does NOT allow substring guessing (e.g. 'a', 'land').
    """
    g = normalize_guess(guess)
    t = normalize_guess(target)

    if g == t:
        return True

    parts = t.split()
    if len(parts) > 1:
        last_name = parts[-1]
        if len(last_name) > 3 and g == last_name:
            return True
        reversed_name = " ".join(reversed(parts))
        if g == reversed_name:
            return True

    return False


def main():
    db = SessionLocal()

    # Fixed hidden player for repeatable testing
    haaland_id = "66da82cb-d561-5f56-8b71-ef716f1c4322"
    target_player_name = "Erling Haaland"

    player_exists = db.execute(
        text("SELECT name FROM players WHERE id = :id"),
        {"id": haaland_id}
    ).fetchone()

    if not player_exists:
        print("Error: Erling Haaland not found. Please run ingestion first.")
        db.close()
        return

    print("\n   YOU KNOW BALL? - INTERACTIVE TESTER (Haaland)")
    print("=" * 54)
    print("Rules:")
    print("  - Up to 20 questions, 3 guesses.")
    print("  - Type 'g' or 'guess' to submit a guess at any time.")
    print("  - Type 'q' to quit.\n")

    engine = CandidateEngine(db)
    print(f"Candidate pool: {engine.get_remaining_count()} players\n")
    print("=" * 54 + "\n")

    question_count = 0
    max_questions = 20
    guess_count = 0
    max_guesses = 3
    consecutive_invalid = 0

    while True:
        try:
            if question_count >= max_questions:
                print(f"\nGame Over! You used all {max_questions} questions.")
                print(f"The hidden player was: {target_player_name}")
                break

            status = f"[Q: {question_count}/{max_questions}  |  Guesses: {guess_count}/{max_guesses}  |  Pool: {engine.get_remaining_count()}]"
            action = input(f"{status}\nYour question (or 'g'=guess, 'q'=quit): ").strip()

            if not action:
                continue

            if action.lower() == 'q':
                print(f"\nQuitting. The hidden player was: {target_player_name}")
                break

            # ── Guess mode ──────────────────────────────────────────────────
            if action.lower() in ('g', 'guess'):
                guess_count += 1
                player_guess = input(f"Your guess ({guess_count}/{max_guesses}): ").strip()

                if guess_matches(player_guess, target_player_name):
                    print(f"\nCORRECT! The player was {target_player_name}!")
                    break
                else:
                    print("Wrong guess!")
                    if guess_count >= max_guesses:
                        print(f"\nNo guesses left! The player was: {target_player_name}")
                        break
                    print(f"   {max_guesses - guess_count} guess(es) remaining.\n")
                continue

            # ── Question mode ────────────────────────────────────────────────
            print("\nParsing your question...")
            parsed = parse_question(db, action)

            if parsed["type"] == "invalid" or not parsed.get("value"):
                err_msg = parsed.get("message", "Could not understand that question.")
                print(f"   {err_msg}")
                consecutive_invalid += 1
                if consecutive_invalid >= 3:
                    question_count += 1
                    consecutive_invalid = 0
                    print(f"   (3 invalid in a row — turn deducted. {max_questions - question_count} turns left.)\n")
                else:
                    print(f"   (No turn charged — invalid #{consecutive_invalid}/3)\n")
                continue

            consecutive_invalid = 0
            question_count += 1
            q_type = parsed["type"]
            q_value = parsed["value"]
            print(f"   Parsed as: type='{q_type}', value='{q_value}'")

            # ── Dispatch ─────────────────────────────────────────────────────
            answer = "UNKNOWN"
            fact_details = ""

            if q_type == "nationality":
                answer, fact_details = handle_nationality(db, haaland_id, q_value)
                engine.filter_by_nationality(q_value, answer)

            elif q_type == "current_club":
                answer, fact_details = handle_current_club(db, haaland_id, q_value)
                engine.filter_by_current_club(q_value, answer)

            elif q_type == "club_history":
                answer, fact_details = handle_club_history(db, haaland_id, q_value)
                engine.filter_by_club_history(q_value, answer)

            elif q_type == "position":
                answer, fact_details = handle_position(db, haaland_id, q_value)
                engine.filter_by_position(q_value, answer)

            elif q_type == "competition":
                answer, fact_details = handle_competition_history(db, haaland_id, q_value)
                engine.filter_by_competition_history(q_value, answer)

            elif q_type == "big_six":
                answer, fact_details = handle_big_six(db, haaland_id)
                engine.filter_by_big_six(answer)

            elif q_type == "continent":
                answer, fact_details = handle_continent(db, haaland_id, q_value)
                engine.filter_by_continent(q_value, answer)

            elif q_type == "age":
                operator = q_value["operator"]
                years = q_value["years"]
                answer, fact_details = handle_age(db, haaland_id, operator, years)
                engine.filter_by_age(operator, years, answer)

            elif q_type == "foot":
                answer, fact_details = handle_foot(db, haaland_id, q_value)
                engine.filter_by_foot(q_value, answer)

            else:
                print(f"   Question type '{q_type}' is not yet handled. No turn charged.")
                question_count -= 1
                continue

            explanation = generate_explanation(action, answer, target_player_name, fact_details)
            emoji = {"YES": "[YES]", "NO": "[NO]", "UNKNOWN": "[?]"}.get(answer, "[?]")
            print(f"\n{emoji} {explanation}")
            print(f"   Candidates remaining: {engine.get_remaining_count()}")
            print("\n" + "-" * 54 + "\n")

        except KeyboardInterrupt:
            print(f"\n\nInterrupted. The hidden player was: {target_player_name}")
            break

    db.close()


if __name__ == "__main__":
    main()
