import sys, os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.db.database import SessionLocal

db = SessionLocal()

# Get top 5 competition IDs
comp_ids = db.execute(text("""
    SELECT id FROM competitions 
    WHERE LOWER(name) IN ('premier-league', 'la-liga', 'bundesliga', 'serie-a', 'ligue-1')
""")).fetchall()
comp_uuid_strings = [str(r[0]) for r in comp_ids]

# Get clubs in top 5
club_ids = db.execute(text("""
    SELECT id FROM clubs 
    WHERE domestic_competition_id = ANY(:ids)
"""), {"ids": comp_uuid_strings}).fetchall()
club_uuid_strings = [str(r[0]) for r in club_ids]

print(f"Top 5 competitions count: {len(comp_uuid_strings)}")
print(f"Clubs in top-5 leagues: {len(club_uuid_strings)}")

# Count players in top-5 vs others
total_players = db.execute(text("SELECT count(*) FROM players")).scalar()
top5_players_count = db.execute(text("""
    SELECT count(*) FROM players 
    WHERE current_club_id = ANY(:club_ids)
"""), {"club_ids": club_uuid_strings}).scalar()

non_top5_count = total_players - top5_players_count

print(f"Total players: {total_players}")
print(f"Players in top-5 clubs: {top5_players_count}")
print(f"Players NOT in top-5 clubs (to delete): {non_top5_count}")

# Check dependent table counts for non-top5 players
# We will select non-top5 player IDs
non_top5_ids = db.execute(text("""
    SELECT id FROM players 
    WHERE current_club_id IS NULL OR NOT (current_club_id = ANY(:club_ids))
"""), {"club_ids": club_uuid_strings}).fetchall()
non_top5_uuid_strings = [str(r[0]) for r in non_top5_ids]

print(f"Non-top5 UUID count resolved: {len(non_top5_uuid_strings)}")

tables_to_check = [
    "player_club_history",
    "transfers",
    "appearances",
    "game_lineups",
    "game_events",
    "player_valuations",
    "guesses",
    "game_sessions"
]

print("\n=== DEPENDENT RECORDS TO BE DELETED ===")
for t in tables_to_check:
    # Check if table has player_id or another foreign key to players
    # We will query records where player_id = ANY(...)
    try:
        count = db.execute(text(f"SELECT count(*) FROM {t} WHERE player_id = ANY(:ids)"), {"ids": non_top5_uuid_strings}).scalar()
        print(f"- Table '{t}': {count} records")
    except Exception as e:
        print(f"- Table '{t}' check failed: {e}")
