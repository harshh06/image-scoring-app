# backend/main.py

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn
import torch # Need torch to load the file

# Import our custom logic
from app.utils import extract_and_process_image, get_model, MAX_SCORES

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
UPLOAD_DIR = Path("uploads")
RAW_DIR = UPLOAD_DIR / "raw"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
RAW_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# --- Static Files ---
app.mount("/static", StaticFiles(directory=THUMBNAIL_DIR), name="static")

# --- GLOBAL MODEL STATE ---
model = None
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
async def upload_image(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(400, "Only .tif files supported")
    
    global model
    if model is None:
        raise HTTPException(503, "AI Model not loaded")

    try:
        # Save Raw
        file_path = RAW_DIR / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process & Predict
        result = extract_and_process_image(file_path, THUMBNAIL_DIR, model, MAX_SCORES)
        return result

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")
    finally:
        await file.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)