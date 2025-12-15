import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import torch
import uvicorn

# --- APP IMPORTS ---
from app import models, database
from app.utils import extract_and_process_image, get_model, MAX_SCORES

# --- DATABASE INIT ---
models.Base.metadata.create_all(bind=database.engine)


app = FastAPI()

# --- CORS ---
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "https://harshsonii-histopathology-scoring.hf.space"]
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
        model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=False))
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
        # 2. READ INTO MEMORY (No saving to disk!)
        file_bytes = await file.read()
        
        # 3. PROCESS DIRECTLY
        result = extract_and_process_image(
            file_stream=file_bytes,  # Pass bytes
            filename=safe_filename,  # Pass name
            model=model, 
            max_scores=MAX_SCORES
        )

        # 4. DATABASE LOGIC (Stays the same - Upsert)
        existing_record = db.query(models.ImageScore).filter(
            models.ImageScore.filename == result["filename"]
        ).first()

        if existing_record:
            print(f"✅ Found existing history for {result['filename']}")
            result["scores"]["Pancreatic Architecture"] = existing_record.score_architecture
            # ... (rest of score loading) ...
            result["scores"]["Fibrosis"] = existing_record.score_fibrosis
            result["scores"]["Total"] = existing_record.score_total
            
            result["db_id"] = existing_record.id
            
            from datetime import datetime
            existing_record.timestamp = datetime.now()
            db.commit()
            
        else:
            print(f"🆕 New file. Saving AI scores.")
            new_record = models.ImageScore(
                filename=result["filename"],
                serial_number=result["serial_number"],
                sample_id=result["sample_id"],
                score_architecture=result["scores"]["Pancreatic Architecture"],
                # ... (rest of score mapping) ...
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