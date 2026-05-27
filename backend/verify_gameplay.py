import sys
import os

# Add backend directory to sys path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from sqlalchemy import text
from app.game.queries import handlers
from app.game.candidate_engine.engine import CandidateEngine

def run_simulation():
    db = SessionLocal()
    
    # 1. Fetch a valid active player with a club and nationality
    query = text("""
        SELECT p.id, p.name, c.name as club_name, nat.name as nationality_name, p.position_group
        FROM players p
        JOIN clubs c ON p.current_club_id = c.id
        JOIN countries nat ON p.nationality_id = nat.id
        WHERE p.active = true
        LIMIT 1
    """)
    player = db.execute(query).fetchone()
    if not player:
        print("Error: No active players found in the database.")
        return
        
    hidden_id, name, club, nationality, position = player
    print(f"=== SIMULATING GAMEPLAY DEDUCTION FOR PLAYER: {name} ===")
    print(f"Target Details: Club='{club}', Nationality='{nationality}', Position='{position}'\n")
    
    engine = CandidateEngine(db)
    print(f"Initial Candidate Pool Size: {engine.get_remaining_count()} players")
    
    # 2. Filter by nationality
    print(f"1. Querying nationality: '{nationality}'...")
    ans = handlers.handle_nationality(db, str(hidden_id), nationality)
    print(f"   Answer: {ans}")
    engine.filter_by_nationality(nationality, ans)
    print(f"   Candidates remaining: {engine.get_remaining_count()}")
    
    # 3. Filter by current club
    print(f"2. Querying current club: '{club}'...")
    ans = handlers.handle_current_club(db, str(hidden_id), club)
    print(f"   Answer: {ans}")
    engine.filter_by_current_club(club, ans)
    print(f"   Candidates remaining: {engine.get_remaining_count()}")
    
    # 4. Filter by position group
    print(f"3. Querying position: '{position}'...")
    ans = handlers.handle_position(db, str(hidden_id), position)
    print(f"   Answer: {ans}")
    engine.filter_by_position(position, ans)
    print(f"   Candidates remaining: {engine.get_remaining_count()}")
    
    # Verify the winner
    if engine.get_remaining_count() >= 1:
        winner_ids = list(engine.pool)
        winners = db.execute(text("SELECT name FROM players WHERE id = ANY(:ids)"), {"ids": list(winner_ids)}).fetchall()
        winner_names = [w[0] for w in winners]
        print(f"\nFinal Engine Output Candidates: {winner_names}")
        if name in winner_names:
            print("SUCCESS! The candidate engine successfully identified/contained the hidden player!")
        else:
            print("ERROR: Hidden player was incorrectly filtered out!")
    else:
        print("ERROR: Candidate pool is empty!")

if __name__ == "__main__":
    run_simulation()
