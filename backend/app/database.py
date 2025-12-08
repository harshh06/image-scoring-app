# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. Get the Database URL from docker-compose environment variables
# We provide a default for local testing outside docker
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://appuser:your_strong_dev_password@localhost:5432/image_scoring_db"
)

# 2. Create the SQLAlchemy Engine
# This opens the actual connection pool to Postgres
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Create a SessionLocal class
# Each instance of this class will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base class
# All our database models (tables) will inherit from this
Base = declarative_base()

# 5. Dependency Injection Utility
# This function is used by FastAPI to open a session for a request and close it afterwards
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()