# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. Get the Database URL from environment variables (.env)
# Default to a local SQLite file if no URL is found (Safety fallback)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# 2. SUPABASE:
# SQLAlchemy recently deprecated 'postgres://'. We must convert it to 'postgresql://'.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Create the Engine with correct settings
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # SQLite Specific: "check_same_thread" is needed for multithreaded apps like FastAPI
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Postgres/Supabase Specific: "pool_pre_ping" prevents the database connection
    # from "going stale" and crashing the app after a few hours of inactivity.
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 4. Create Session Class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Create Base Class
Base = declarative_base()

# 6. Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()