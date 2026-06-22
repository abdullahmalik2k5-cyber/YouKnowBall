"""CLI internal gameplay tester — picks a random hidden player."""
import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.database import SessionLocal
from sqlalchemy import text

from app.game.queries.handlers import (
    handle_nationality,
    handle_current_club,
    handle_club_history,
    handle_position,
    handle_competition_history,
    handle_big_six,
)
from app.game.candidate_engine.engine import CandidateEngine


def main():
    db = SessionLocal()

    # Pick a random active player with all required relations
    query = text("""
        SELECT p.id, p.name, c.name as club_name, nat.name as nationality_name
        FROM players p
        JOIN clubs c ON p.current_club_id = c.id
        JOIN countries nat ON p.nationality_id = nat.id
        WHERE p.active = true
        LIMIT 1000
    """)
    players = db.execute(query).fetchall()

    if not players:
        print("Database is empty or missing relations!")
        db.close()
        return

    hidden = random.choice(players)
    hidden_id = str(hidden[0])
    print("--- INTERNAL GAMEPLAY TESTER ---")
    print(f"[HIDDEN PLAYER SELECTED: {hidden[1]}] (shhh!)")

    engine = CandidateEngine(db)
    print(f"Candidate pool initialized with {engine.get_remaining_count()} players.\n")

    print("Available Commands:")
    print("  nationality <country>    e.g. nationality Argentina")
    print("  current_club <club>      e.g. current_club Arsenal")
    print("  club_history <club>      e.g. club_history Juventus")
    print("  position <GK|DEF|MID|ATK>  e.g. position DEF")
    print("  competition <comp>       e.g. competition premier-league")
    print("  big_six                  Has he played for a Big Six club?")
    print("  q: quit")

    while True:
        cmd = input("\nEnter query > ").strip()
        if cmd.lower() == 'q':
            print(f"The hidden player was: {hidden[1]}")
            break

        parts = cmd.split(" ", 1)
        action = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        answer = "UNKNOWN"
        fact = ""

        if action == "nationality":
            answer, fact = handle_nationality(db, hidden_id, arg)
            engine.filter_by_nationality(arg, answer)

        elif action == "current_club":
            answer, fact = handle_current_club(db, hidden_id, arg)
            engine.filter_by_current_club(arg, answer)

        elif action == "club_history":
            answer, fact = handle_club_history(db, hidden_id, arg)
            engine.filter_by_club_history(arg, answer)

        elif action == "position":
            answer, fact = handle_position(db, hidden_id, arg.upper())
            engine.filter_by_position(arg.upper(), answer)

        elif action == "competition":
            answer, fact = handle_competition_history(db, hidden_id, arg)
            engine.filter_by_competition_history(arg, answer)

        elif action == "big_six":
            answer, fact = handle_big_six(db, hidden_id)
            engine.filter_by_big_six(answer)

        else:
            print(f"Unknown action '{action}'. Try: nationality, current_club, club_history, position, competition, big_six")
            continue

        print(f"ANSWER: {answer}  |  {fact}")
        print(f"Remaining Candidates: {engine.get_remaining_count()}")

        if engine.get_remaining_count() == 1:
            remaining_id = list(engine.pool)[0]
            remaining_name = db.execute(
                text("SELECT name FROM players WHERE id = :id"), {"id": remaining_id}
            ).scalar()
            print(f"\nPool narrowed to 1: {remaining_name}")
            break

    db.close()


if __name__ == "__main__":
    main()
