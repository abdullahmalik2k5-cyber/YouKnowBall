"""Validation pipeline to ensure database integrity."""
from sqlalchemy import text
from app.db.database import SessionLocal

def run_validations():
    db = SessionLocal()
    errors = []

    print("Running database validations...")

    # 1. Null Critical Fields
    res = db.execute(text("SELECT count(*) FROM players WHERE name IS NULL OR position IS NULL")).scalar()
    if res > 0:
        errors.append(f"Found {res} players missing critical fields (name, position).")

    # 2. Foreign Key Integrity (Clubs in Players)
    res = db.execute(text("SELECT count(*) FROM players WHERE current_club_id IS NOT NULL AND current_club_id NOT IN (SELECT id FROM clubs)")).scalar()
    if res > 0:
        errors.append(f"Found {res} players with invalid current_club_id.")

    # 3. Missing clubs referenced in transfers
    res = db.execute(text("SELECT count(*) FROM transfers WHERE to_club_id IS NOT NULL AND to_club_id NOT IN (SELECT id FROM clubs)")).scalar()
    if res > 0:
        errors.append(f"Found {res} transfers with invalid to_club_id.")

    # 4. Appearances refer to valid games
    res = db.execute(text("SELECT count(*) FROM appearances WHERE game_id NOT IN (SELECT id FROM games)")).scalar()
    if res > 0:
        errors.append(f"Found {res} appearances referencing missing games.")

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"- {error}")
    else:
        print("All validations passed. Database integrity is solid.")
        
    db.close()

if __name__ == "__main__":
    run_validations()
