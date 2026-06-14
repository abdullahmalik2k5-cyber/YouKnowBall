import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env manually
def _load_env():
    # Try current working directory and parent paths to find .env
    paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.getcwd()), ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
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

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://you_know_ball:you_know_ball@localhost:5432/you_know_ball")

engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
