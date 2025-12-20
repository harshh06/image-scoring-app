import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
import torch
import uvicorn

# --- APP IMPORTS ---
from app import models, database
from app.utils import (
    extract_and_process_image, 
    get_model, 
    MAX_SCORES, 
    generate_thumbnail_and_metadata, 
    MAX_FILE_SIZE, 
    SCORE_FIELDS
)

MODEL_PATH = Path("pancreas_model.pth")

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT ---
models.Base.metadata.create_all(bind=database.engine)

# --- LIFESPAN CONTEXT MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    # Startup: Load model
    logger.info("Loading AI model...")
    try:
        app.state.model = get_model()
        app.state.model.load_state_dict(
            torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=False)
        )
        app.state.model.eval()
        logger.info(f" Model loaded successfully from {MODEL_PATH}")
    except FileNotFoundError:
        logger.error(f"!!! Model file not found at {MODEL_PATH}")
        app.state.model = None
    except Exception as e:
        logger.error(f"!!! Error loading model: {e}", exc_info=True)
        app.state.model = None
    
    yield  # App runs here
    
    # Shutdown: Clean up
    logger.info("Shutting down...")

# --- APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)

# --- CORS ---
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    origins = [origin.strip() for origin in env_origins.split(",")]
else:
    origins = ["http://localhost:3000"]

logger.info(f" CORS Allowed Origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES ---

@app.get("/")
async def read_root():
    return {"message": "AI Scoring API Ready"}

@app.get("/health")
async def health_check(request: Request, db: Session = Depends(database.get_db)):
    """Health check for load balancers."""
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        
        # Check model loaded
        if not hasattr(request.app.state, 'model') or request.app.state.model is None:
            raise HTTPException(503, "Model not loaded")
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(503, f"Unhealthy: {str(e)}")

@app.post("/api/upload-image/")
async def upload_image(
    request: Request,  
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    safe_filename = file.filename or "unknown_file.tif"

    # 1. Validation - File type
    if not safe_filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(400, "Only .tif files supported")
    
    # 2. Validation - File size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            413, 
            f"File too large ({file_size / 1024 / 1024:.1f} MB). Max: {MAX_FILE_SIZE / 1024 / 1024:.1f} MB"
        )
    
    # 3. Validation - Model loaded
    if request.app.state.model is None:
        raise HTTPException(503, "AI Model not loaded")

    try:
        # 4. CHECK DATABASE FIRST
        existing_record = db.query(models.ImageScore).filter(
            models.ImageScore.filename == safe_filename
        ).first()

        if existing_record:
            logger.info(f" Found existing record for {safe_filename}. Skipping AI inference.")
            
            # Read file and generate thumbnail + metadata
            file_bytes = await file.read()
            metadata = generate_thumbnail_and_metadata(file_bytes, safe_filename)
            
            # Build result from existing DB record
            result = {
                "status": "success",
                "filename": existing_record.filename,
                "serial_number": metadata["serial_number"],
                "sample_id": metadata["sample_id"],
                "scores": {
                    "Pancreatic Architecture": existing_record.score_architecture,
                    "Glandular Atrophy": existing_record.score_atrophy,
                    "Pseudotubular Complexes": existing_record.score_complexes,
                    "Fibrosis": existing_record.score_fibrosis,
                    "Total": existing_record.score_total
                },
                "display_url": metadata["display_url"],
                "db_id": existing_record.id
            }
            
            # Update timestamp
            existing_record.timestamp = datetime.now()
            db.commit()
            
            return result

        # 5. ⚡ NEW FILE: Run AI inference
        logger.info(f"New file {safe_filename}. Running AI inference...")
        file_bytes = await file.read()
        
        result = extract_and_process_image(
            file_stream=file_bytes,
            filename=safe_filename,
            model=request.app.state.model,  #  Use app.state.model
            max_scores=MAX_SCORES
        )

        # 6. ATOMIC UPSERT: Save new AI predictions to DB
        stmt = insert(models.ImageScore).values(
            filename=result["filename"],
            serial_number=result["serial_number"],
            sample_id=result["sample_id"],
            score_architecture=result["scores"]["Pancreatic Architecture"],
            score_atrophy=result["scores"]["Glandular Atrophy"],
            score_complexes=result["scores"]["Pseudotubular Complexes"],
            score_fibrosis=result["scores"]["Fibrosis"],
            score_total=result["scores"]["Total"]
        ).on_conflict_do_nothing(
            index_elements=['filename']
        )
        
        db.execute(stmt)
        db.commit()

        # 7. Retrieve the record (guaranteed to exist after upsert)
        final_record = db.query(models.ImageScore).filter(
            models.ImageScore.filename == result["filename"]
        ).first()
        
        if not final_record:
            # This should never happen with on_conflict_do_nothing, but safety check
            raise HTTPException(500, "Failed to create database record")
        
        result["db_id"] = final_record.id
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Upload failed for {safe_filename}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(500, "Internal server error during image processing")
    finally:
        await file.close()

@app.put("/api/scores/{db_id}")
async def update_score(
    db_id: int, 
    payload: dict = Body(...), 
    db: Session = Depends(database.get_db)
):
    """Update pathologist-corrected scores."""
    record = db.query(models.ImageScore).filter(models.ImageScore.id == db_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Score record not found")
    
    # Update fields if present in payload
    for field_name, db_column in SCORE_FIELDS.items():
        if field_name in payload:
            setattr(record, db_column, payload[field_name])
    
    # Recalculate Total - HANDLE NONE VALUES
    record.score_total = (
        (record.score_architecture or 0.0) + 
        (record.score_atrophy or 0.0) + 
        (record.score_complexes or 0.0) + 
        (record.score_fibrosis or 0.0)
    )
    
    db.commit()
    db.refresh(record)
    
    return {"status": "updated", "new_total": record.score_total}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)