import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assuming local postgres or Supabase URI from .env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://you_know_ball:you_know_ball@localhost:5432/you_know_ball")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
