# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import torch
import torch.nn as nn

from main import app
from app.database import Base, get_db
from app.utils import get_model

# --- DATABASE FIXTURE ---
@pytest.fixture(scope="function")
def test_db():
    """
    Creates a fresh in-memory SQLite database for each test.
    This ensures tests don't interfere with each other.
    """
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# --- API CLIENT FIXTURE ---
@pytest.fixture(scope="function")
def client(test_db):
    """
    Creates a TestClient with dependency override for the database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# --- MOCK MODEL FIXTURE ---
@pytest.fixture(scope="session")
def mock_model():
    """
    Creates a dummy PyTorch model for testing (no real weights needed).
    """
    model = get_model()
    model.eval()
    return model


# --- MOCK APP STATE FIXTURE ---
@pytest.fixture(scope="function")
def client_with_model(client, mock_model):
    """
    Injects the mock model into app.state for testing upload endpoints.
    """
    app.state.model = mock_model
    yield client
    app.state.model = None


# --- NEW: CLIENT WITHOUT MODEL FIXTURE ---
@pytest.fixture(scope="function")
def client_without_model(client):
    """
    Ensures app.state.model is None for testing error handling.
    """
    # Save original model
    original_model = getattr(app.state, 'model', None)
    
    # Set to None
    app.state.model = None
    
    yield client
    
    # Restore original
    app.state.model = original_model