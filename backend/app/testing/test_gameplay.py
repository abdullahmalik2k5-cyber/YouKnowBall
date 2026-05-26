"""CLI internal gameplay tester."""
import sys
import os

# Add backend directory to sys path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.database import SessionLocal
from sqlalchemy import text
import random

from app.game.queries import handlers
from app.game.candidate_engine.engine import CandidateEngine

def main():
    db = SessionLocal()
    
    # 1. Randomly select hidden player
    # Let's get a random active player with a current club and nationality
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
        return

    hidden = random.choice(players)
    hidden_id = str(hidden[0])
    print(f"--- INTERNAL GAMEPLAY TESTER ---")
    print(f"[HIDDEN PLAYER SELECTED: {hidden[1]}] (shhh!)")
    
    engine = CandidateEngine(db)
    print(f"Candidate pool initialized with {engine.get_remaining_count()} players.\n")
    
    print("Available Commands: ")
    print("1: nationality <country> (e.g. nationality Argentina)")
    print("2: current_club <club> (e.g. current_club Arsenal)")
    print("3: club_history <club> (e.g. club_history Juventus)")
    print("4: position <position> (e.g. position DEF)")
    print("5: competition <comp> (e.g. competition Premier League)")
    print("q: quit")
    
    while True:
        cmd = input("\nEnter query > ").strip()
        if cmd.lower() == 'q':
            break
            
        parts = cmd.split(" ", 1)
        if len(parts) < 2:
            print("Invalid command.")
            continue
            
        action, arg = parts[0], parts[1]
        
        answer = "UNKNOWN"
        if action == "nationality":
            answer = handlers.handle_nationality(db, hidden_id, arg)
            if answer != "UNKNOWN":
                engine.filter_by_nationality(arg, answer)
        elif action == "current_club":
            answer = handlers.handle_current_club(db, hidden_id, arg)
            if answer != "UNKNOWN":
                engine.filter_by_current_club(arg, answer)
        elif action == "club_history":
            answer = handlers.handle_club_history(db, hidden_id, arg)
            if answer != "UNKNOWN":
                engine.filter_by_club_history(arg, answer)
        elif action == "position":
            answer = handlers.handle_position(db, hidden_id, arg)
            if answer != "UNKNOWN":
                engine.filter_by_position(arg, answer)
        elif action == "competition":
            answer = handlers.handle_competition_history(db, hidden_id, arg)
            if answer != "UNKNOWN":
                engine.filter_by_competition_history(arg, answer)
        else:
            print("Unknown action.")
            continue
            
        print(f"ANSWER: {answer}")
        print(f"Remaining Candidates: {engine.get_remaining_count()}")
        
        if engine.get_remaining_count() == 1:
            remaining_id = list(engine.pool)[0]
            remaining_name = db.execute(text("SELECT name FROM players WHERE id = :id"), {"id": remaining_id}).scalar()
            print(f"\nWINNER! The engine has narrowed it down to: {remaining_name}")
            break

if __name__ == "__main__":
    main()
