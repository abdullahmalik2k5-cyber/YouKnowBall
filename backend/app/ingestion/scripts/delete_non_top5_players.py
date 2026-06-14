import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.db.database import SessionLocal

def run_delete():
    db = SessionLocal()
    
    # Disable statement timeout for the session
    try:
        db.execute(text("SET statement_timeout = 0"))
        print("Disabled statement timeout for this session.")
    except Exception as e:
        print(f"Warning: Could not set statement timeout: {e}")

    print("Resolving top 5 competition IDs...")
    comp_ids = db.execute(text("""
        SELECT id FROM competitions 
        WHERE LOWER(name) IN ('premier-league', 'la-liga', 'bundesliga', 'serie-a', 'ligue-1')
    """)).fetchall()
    comp_uuid_strings = [str(r[0]) for r in comp_ids]

    print("Resolving clubs in top-5 leagues...")
    club_ids = db.execute(text("""
        SELECT id FROM clubs 
        WHERE domestic_competition_id = ANY(:ids)
    """), {"ids": comp_uuid_strings}).fetchall()
    club_uuid_strings = [str(r[0]) for r in club_ids]

    print("Resolving player IDs to delete...")
    non_top5_ids = db.execute(text("""
        SELECT id FROM players 
        WHERE current_club_id IS NULL OR NOT (current_club_id = ANY(:club_ids))
    """), {"club_ids": club_uuid_strings}).fetchall()
    non_top5_uuid_strings = [str(r[0]) for r in non_top5_ids]

    total_to_delete = len(non_top5_uuid_strings)
    print(f"Total players to delete: {total_to_delete}")

    if total_to_delete == 0:
        print("No players to delete. Database is already clean.")
        return

    # Delete in batches of 1000 players
    batch_size = 1000
    for i in range(0, total_to_delete, batch_size):
        batch_ids = non_top5_uuid_strings[i:i+batch_size]
        print(f"\nProcessing batch {i // batch_size + 1}: players {i} to {min(i + batch_size, total_to_delete)}...")
        
        try:
            db.execute(
                text("DELETE FROM guesses WHERE guessed_player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )
            
            db.execute(text("""
                DELETE FROM questions 
                WHERE session_id IN (SELECT id FROM game_sessions WHERE player_id = ANY(:ids))
            """), {"ids": batch_ids})

            db.execute(
                text("DELETE FROM game_sessions WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )
            
            db.execute(
                text("DELETE FROM player_club_history WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM transfers WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM appearances WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM game_lineups WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM game_events WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM player_valuations WHERE player_id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.execute(
                text("DELETE FROM players WHERE id = ANY(:ids)"), 
                {"ids": batch_ids}
            )

            db.commit()
            print(f"Committed batch {i // batch_size + 1}.")
        except Exception as e:
            print(f"Error occurred in batch {i // batch_size + 1}: {e}")
            db.rollback()
            print("Batch rolled back. Aborting.")
            break

    print("\nPurge process completed!")

if __name__ == "__main__":
    run_delete()
