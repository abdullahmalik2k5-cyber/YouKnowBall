import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.db.database import SessionLocal

CSV_PATH = "backend/app/ingestion/raw/transfermarkt/players_enriched.csv"

def get_club_name_map(db):
    """Returns a dict of club_id -> club_name (lowercase)."""
    res = db.execute(text("SELECT id, name FROM clubs")).fetchall()
    return {r[0]: r[1].lower().strip() for r in res}

def run_update():
    db = SessionLocal()
    df = pd.read_csv(CSV_PATH)
    
    print(f"Loaded {len(df)} players from CSV.")
    club_names = get_club_name_map(db)

    # Cache all players to find matches quickly
    print("Fetching all active players from DB...")
    db_players = db.execute(text("""
        SELECT p.id, p.name, p.date_of_birth, p.current_club_id
        FROM players p
        WHERE p.active = true
    """)).fetchall()
    
    # Organize DB players by lowercase name
    db_players_by_name = {}
    for p in db_players:
        p_name = p[1].lower().strip()
        db_players_by_name.setdefault(p_name, []).append({
            "id": p[0],
            "name": p[1],
            "birth_year": p[2].year if p[2] else None,
            "club_id": p[3],
            "club_name": club_names.get(p[3], "")
        })

    matched_count = 0
    not_found_count = 0
    multiple_matches_count = 0
    updates_to_run = []

    print("Matching CSV players to DB players...")
    for idx, row in df.iterrows():
        csv_name = str(row['name']).lower().strip()
        csv_born = int(row['born']) if not pd.isna(row['born']) else None
        csv_club = str(row['club']).lower().strip() if not pd.isna(row['club']) else ""

        candidates = db_players_by_name.get(csv_name, [])
        if not candidates:
            # Try a fallback of name normalization or partial matches if needed, but exact is safer.
            not_found_count += 1
            continue

        matched_candidate = None

        if len(candidates) == 1:
            matched_candidate = candidates[0]
        else:
            # Resolve duplicate names using born year and club name
            filtered = []
            for c in candidates:
                # 1. Match by birth year if both available
                year_match = (csv_born is None) or (c["birth_year"] is None) or (c["birth_year"] == csv_born)
                # 2. Match by club name (sub-string match or exact)
                club_match = not csv_club or (csv_club in c["club_name"]) or (c["club_name"] in csv_club)
                
                if year_match and club_match:
                    filtered.append(c)

            if len(filtered) == 1:
                matched_candidate = filtered[0]
            elif len(filtered) > 1:
                # Still multiple candidates, pick the first one as fallback but track it
                matched_candidate = filtered[0]
                multiple_matches_count += 1
            else:
                # No candidates matched filters, default to first by name but track it
                matched_candidate = candidates[0]
                not_found_count += 1

        if matched_candidate:
            matched_count += 1
            
            # Helper to convert pandas types/NaNs to Python types
            def clean_val(val, val_type):
                if pd.isna(val):
                    return None
                if val_type == 'bool':
                    return bool(val)
                if val_type == 'int':
                    return int(val)
                if val_type == 'str':
                    return str(val)
                return val

            updates_to_run.append({
                "pid": matched_candidate["id"],
                "positions": clean_val(row.get("positions"), 'str'),
                "born": csv_born,
                "minutes": clean_val(row.get("minutes"), 'int'),
                "matches": clean_val(row.get("matches"), 'int'),
                "goals": clean_val(row.get("goals"), 'int'),
                "assists": clean_val(row.get("assists"), 'int'),
                "is_gk": clean_val(row.get("is_gk"), 'bool'),
                "difficulty": clean_val(row.get("difficulty"), 'str'),
                "eligible": clean_val(row.get("eligible"), 'bool'),
                "region": clean_val(row.get("region"), 'str'),
                "city": clean_val(row.get("city"), 'str'),
                "big_club": clean_val(row.get("big_club"), 'bool'),
                "is_starter": clean_val(row.get("is_starter"), 'bool'),
                "is_supersub": clean_val(row.get("is_supersub"), 'bool'),
                "is_everpresent": clean_val(row.get("is_everpresent"), 'bool'),
                "goals_bracket": clean_val(row.get("goals_bracket"), 'str'),
                "assists_bracket": clean_val(row.get("assists_bracket"), 'str'),
                "double_double": clean_val(row.get("double_double"), 'bool'),
                "penalty_taker": clean_val(row.get("penalty_taker"), 'bool'),
                "sent_off": clean_val(row.get("sent_off"), 'bool'),
                "scored_own_goal": clean_val(row.get("scored_own_goal"), 'bool'),
                "discipline": clean_val(row.get("discipline"), 'str'),
                "heavily_booked": clean_val(row.get("heavily_booked"), 'bool'),
                "big_crosser": clean_val(row.get("big_crosser"), 'bool'),
                "ball_winner": clean_val(row.get("ball_winner"), 'bool'),
                "gets_fouled": clean_val(row.get("gets_fouled"), 'bool'),
                "shoots_a_lot": clean_val(row.get("shoots_a_lot"), 'bool'),
                "gk_clean_sheets": clean_val(row.get("gk_clean_sheets"), 'int'),
                "gk_strong": clean_val(row.get("gk_strong"), 'bool'),
                "high_ppm": clean_val(row.get("high_ppm"), 'bool')
            })

    print(f"Total matched: {matched_count}")
    print(f"Ambiguous matches resolved: {multiple_matches_count}")
    print(f"Not matched/fallback count: {not_found_count}")

    print("Running batch update in database...")
    update_sql = """
        UPDATE players
        SET positions = :positions,
            born = :born,
            minutes = :minutes,
            matches = :matches,
            goals = :goals,
            assists = :assists,
            is_gk = :is_gk,
            difficulty = :difficulty,
            eligible = :eligible,
            region = :region,
            city = :city,
            big_club = :big_club,
            is_starter = :is_starter,
            is_supersub = :is_supersub,
            is_everpresent = :is_everpresent,
            goals_bracket = :goals_bracket,
            assists_bracket = :assists_bracket,
            double_double = :double_double,
            penalty_taker = :penalty_taker,
            sent_off = :sent_off,
            scored_own_goal = :scored_own_goal,
            discipline = :discipline,
            heavily_booked = :heavily_booked,
            big_crosser = :big_crosser,
            ball_winner = :ball_winner,
            gets_fouled = :gets_fouled,
            shoots_a_lot = :shoots_a_lot,
            gk_clean_sheets = :gk_clean_sheets,
            gk_strong = :gk_strong,
            high_ppm = :high_ppm
        WHERE id = :pid
    """
    
    # Run updates in batches of 500
    batch_size = 500
    for i in range(0, len(updates_to_run), batch_size):
        batch = updates_to_run[i:i+batch_size]
        for params in batch:
            db.execute(text(update_sql), params)
        db.commit()
        print(f"Updated {min(i + batch_size, len(updates_to_run))}/{len(updates_to_run)} players.")

    print("Data update completed successfully!")

if __name__ == "__main__":
    run_update()
