"""
One-time migration: backfill position_group for all players where it is NULL or 'UNKNOWN'.
Uses the `position` column (Transfermarkt broad category: Goalkeeper/Defender/Midfield/Attack).
"""
import sys, os
# Make both the backend root and the migrations dir importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from verify_database import _load_env
_load_env()

from app.db.database import engine
from sqlalchemy import text

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Defender":   "DEF",
    "Midfield":   "MID",
    "Attack":     "ATK",
    # sub-positions as fallback
    "Centre-Back":          "DEF",
    "Left-Back":            "DEF",
    "Right-Back":           "DEF",
    "Wing-Back":            "DEF",
    "Left Wing-Back":       "DEF",
    "Right Wing-Back":      "DEF",
    "Defensive Midfield":   "MID",
    "Central Midfield":     "MID",
    "Attacking Midfield":   "MID",
    "Right Midfield":       "MID",
    "Left Midfield":        "MID",
    "Left Winger":          "ATK",
    "Right Winger":         "ATK",
    "Centre-Forward":       "ATK",
    "Second Striker":       "ATK",
    "Striker":              "ATK",
}

def run():
    updated = 0
    skipped = 0
    with engine.begin() as conn:
        # Fetch all players where position_group is bad
        rows = conn.execute(text(
            "SELECT id, position, sub_position FROM players "
            "WHERE position_group IS NULL OR UPPER(position_group) = 'UNKNOWN'"
        )).fetchall()

        print(f"Found {len(rows)} players with UNKNOWN/NULL position_group.")

        for player_id, position, sub_position in rows:
            group = POSITION_MAP.get(position) or POSITION_MAP.get(sub_position)
            if group:
                conn.execute(text(
                    "UPDATE players SET position_group = :grp WHERE id = :pid"
                ), {"grp": group, "pid": player_id})
                updated += 1
            else:
                skipped += 1

    print(f"  Updated: {updated}")
    print(f"  Skipped (no mapping found): {skipped}")
    print("Done.")

if __name__ == "__main__":
    run()
