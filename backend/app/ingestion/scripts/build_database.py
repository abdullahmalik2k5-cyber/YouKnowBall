import os
import sys
import psycopg
from sqlalchemy import text
from app.db.database import engine, Base
from app.db.models import models

# Cleaned data folder
CLEANED_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "cleaned")

def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def load_csv(table_name, csv_filename):
    """Load a CSV file into a Postgres table using COPY for maximum speed."""
    csv_path = os.path.join(CLEANED_DATA_DIR, csv_filename)
    if not os.path.exists(csv_path):
        print(f"Skipping {table_name}: {csv_filename} not found.")
        return

    # Extract DB URL for psycopg3 connection
    db_url = os.getenv("DATABASE_URL", "postgresql://you_know_ball:you_know_ball@localhost:5432/you_know_ball")
    # Replace +psycopg if present since psycopg3 connects with postgresql://
    db_url = db_url.replace("postgresql+psycopg://", "postgresql://")

    print(f"Loading {csv_filename} into {table_name}...")
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                with cur.copy(f"COPY {table_name} FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        while data := f.read(8192):
                            copy.write(data)
            conn.commit()
        print(f"Successfully loaded {table_name}.")
    except Exception as e:
        print(f"Failed to load {table_name}: {e}")

if __name__ == "__main__":
    create_tables()
    # Ordered by dependencies
    load_csv("countries", "countries.csv")
    load_csv("competitions", "competitions.csv")
    load_csv("clubs", "clubs.csv")
    load_csv("national_teams", "national_teams.csv")
    load_csv("players", "players.csv")
    load_csv("player_club_history", "player_club_history.csv")
    load_csv("transfers", "transfers.csv")
    load_csv("games", "games.csv")
    load_csv("appearances", "appearances.csv")
    load_csv("game_lineups", "game_lineups.csv")
    load_csv("game_events", "game_events.csv")
    load_csv("club_games", "club_games.csv")
    load_csv("player_valuations", "player_valuations.csv")
