import psycopg
import os

# Load .env manually
def _load_env():
    paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.getcwd()), ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
        ".env",
        "../.env"
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

db_url = db_url.replace("postgresql+psycopg://", "postgresql://")

try:
    with psycopg.connect(db_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            print("Attempting to disable read-only mode...")
            cur.execute("ALTER DATABASE postgres SET default_transaction_read_only = off;")
            print("SUCCESS! Read-only mode disabled.")
except Exception as e:
    print(f"FAILED: {e}")
