import os
import shutil
from pathlib import Path

# 1. FIX: Added 'Depends' and 'Body' to imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import torch
import uvicorn

# --- APP IMPORTS ---
# 2. FIX: Removed duplicate import lines
from app import models, database
from app.utils import extract_and_process_image, get_model, MAX_SCORES

# --- DATABASE INIT ---
models.Base.metadata.create_all(bind=database.engine)
# ---------------------

app = FastAPI()

# --- CORS ---
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Directories ---
# We unify everything to use 'static' to match your upload logic
UPLOAD_DIR = Path("static")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Static Files ---
# Even though we use Base64, keeping this mount is useful for debugging
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# --- GLOBAL MODEL STATE ---
model = None
# In Docker, workdir is /app, so this looks for /app/pancreas_model.pth
MODEL_PATH = Path("pancreas_model.pth") 

@app.on_event("startup")
async def load_model():
    """Load the trained model into memory on startup."""
    global model
    try:
        # Define architecture
        model = get_model()
        # Load weights
        model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
        model.eval() # Set to evaluation mode
        print(f"--- SUCCESS: Loaded AI Model from {MODEL_PATH} ---")
    except FileNotFoundError:
        print(f"!!! WARNING: Model not found at {MODEL_PATH}. Prediction will fail. !!!")
    except Exception as e:
        print(f"!!! ERROR loading model: {e} !!!")

@app.get("/")
async def read_root():
    return {"message": "AI Scoring API Ready"}

@app.post("/api/upload-image/")
async def upload_image(
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    safe_filename = file.filename or "unknown_file.tif"

    # 1. Validation
    if not safe_filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(400, "Only .tif files supported")
    
    global model
    if model is None:
        raise HTTPException(503, "AI Model not loaded")

    try:
        # 2. Save File & Generate Thumbnail
        # We ALWAYS do this so the frontend has a valid image/thumbnail to show
        UPLOAD_DIR = Path("static")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path = UPLOAD_DIR / safe_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run processing to get the Thumbnail (display_url) and Serial Numbers
        # We get fresh AI scores here, BUT we might discard them below.
        result = extract_and_process_image(file_path, UPLOAD_DIR, model, MAX_SCORES)

        # 3. CHECK DATABASE HISTORY
        existing_record = db.query(models.ImageScore).filter(
            models.ImageScore.filename == result["filename"]
        ).first()

        if existing_record:
            print(f"✅ Found existing history for {result['filename']}. Loading saved scores.")
            
            # --- PRESERVE HISTORY STRATEGY ---
            # Instead of overwriting the DB with new AI scores, 
            # we overwrite the RESULT with the saved DB scores.
            
            result["scores"]["Pancreatic Architecture"] = existing_record.score_architecture
            result["scores"]["Glandular Atrophy"] = existing_record.score_atrophy
            result["scores"]["Pseudotubular Complexes"] = existing_record.score_complexes
            result["scores"]["Fibrosis"] = existing_record.score_fibrosis
            result["scores"]["Total"] = existing_record.score_total
            
            # Attach DB ID
            result["db_id"] = existing_record.id
            
            # Update timestamp to show it was accessed just now (optional)
            from datetime import datetime
            existing_record.timestamp = datetime.now()
            db.commit()
            
        else:
            print(f"🆕 New file {result['filename']}. Saving AI scores.")
            
            # --- SAVE NEW RECORD ---
            new_record = models.ImageScore(
                filename=result["filename"],
                serial_number=result["serial_number"],
                sample_id=result["sample_id"],
                score_architecture=result["scores"]["Pancreatic Architecture"],
                score_atrophy=result["scores"]["Glandular Atrophy"],
                score_complexes=result["scores"]["Pseudotubular Complexes"],
                score_fibrosis=result["scores"]["Fibrosis"],
                score_total=result["scores"]["Total"]
            )
            
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            
            result["db_id"] = new_record.id

        return result

    except Exception as e:
        print(f"Error processing upload: {e}")
        db.rollback()
        raise HTTPException(500, f"Failed: {str(e)}")
    finally:
        await file.close()
        
# --- 5. NEW ENDPOINT: UPDATE SCORE (For Frontend Sidebar Edits) ---
@app.put("/api/scores/{db_id}")
async def update_score(
    db_id: int, 
    payload: dict = Body(...), 
    db: Session = Depends(database.get_db)
):
    # Find the record
    record = db.query(models.ImageScore).filter(models.ImageScore.id == db_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Score record not found")
    
    # Update fields if present in payload
    if "Pancreatic Architecture" in payload:
        record.score_architecture = payload["Pancreatic Architecture"]
    if "Glandular Atrophy" in payload:
        record.score_atrophy = payload["Glandular Atrophy"]
    if "Pseudotubular Complexes" in payload:
        record.score_complexes = payload["Pseudotubular Complexes"]
    if "Fibrosis" in payload:
        record.score_fibrosis = payload["Fibrosis"]
        
    # Recalculate Total
    record.score_total = (
        record.score_architecture + 
        record.score_atrophy + 
        record.score_complexes + 
        record.score_fibrosis
    ) 
    
    db.commit()
    db.refresh(record)
    return {"status": "updated", "new_total": record.score_total}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)