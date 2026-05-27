from sqlalchemy import create_engine, text
import os

def _load_env():
    paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.getcwd()), ".env"),
        ".env",
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, val = line.split("=", 1)
                            os.environ[key.strip()] = val.strip("'\"")
                        except ValueError:
                            pass
            break

_load_env()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL set.")
    exit(1)

# Ensure correct driver for sqlalchemy
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

engine = create_engine(db_url)

tables = [
    "countries",
    "competitions",
    "clubs",
    "national_teams",
    "players",
    "player_club_history",
    "transfers",
    "games",
    "appearances",
    "game_lineups",
    "game_events",
    "club_games",
    "player_valuations"
]

print("=== YOU KNOW BALL DATABASE STATUS ===")
try:
    with engine.connect() as conn:
        for table in tables:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                print(f"Table '{table}': {count:,} rows")
            except Exception as e:
                print(f"Table '{table}': ERROR ({e})")
except Exception as e:
    print(f"Failed to connect to database: {e}")
