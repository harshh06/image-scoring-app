# backend/app/utils.py

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from pathlib import Path
from typing import Dict, Any
import numpy as np
import base64            
from io import BytesIO   
import re
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Must match training script exactly
NUM_CLASSES = 4
MAX_SCORES = np.array([4.0, 3.0, 3.0, 4.0], dtype=np.float32)
MAX_FILE_SIZE = 100 * 1024 * 1024

SCORE_FIELDS = {
    "Pancreatic Architecture": "score_architecture",
    "Glandular Atrophy": "score_atrophy",
    "Pseudotubular Complexes": "score_complexes",
    "Fibrosis": "score_fibrosis"
}

# Standard transforms (same as training)
MODEL_TRANSFORMS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def get_model():
    """Reconstructs the model architecture."""
    model = models.resnet18(weights=None) # Weights will be loaded later
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, NUM_CLASSES)
    return model

def predict_scores(image: Image.Image, model: nn.Module) -> Dict[str, float]:
    """Inference Logic."""
    
    # 1. Force Resize to 512x512 (Match Training Preprocessing)
    image = image.resize((512, 512))
    
    # 2. Transform for PyTorch
    input_tensor = MODEL_TRANSFORMS(image)
    input_batch = input_tensor.unsqueeze(0)  
    
    device = torch.device("cpu")
    
    with torch.no_grad():
        input_batch = input_batch.to(device)
        output = model(input_batch)
    
    # 3. Post-Process Output
    # Get raw 0-1 values
    normalized_scores = output.cpu().numpy().flatten()
    
    # Scale back to real range (e.g. 0-4)
    actual_scores = normalized_scores * MAX_SCORES
    
    # Clamp to be safe (no negatives or huge numbers)
    actual_scores = np.clip(actual_scores, 0, MAX_SCORES)
    
    def round_quarter(num):
        return round(num * 4) / 4

    scores = {
        "Pancreatic Architecture": round_quarter(float(actual_scores[0])),
        "Glandular Atrophy": round_quarter(float(actual_scores[1])),
        "Pseudotubular Complexes": round_quarter(float(actual_scores[2])),
        "Fibrosis": round_quarter(float(actual_scores[3])),
    }
    scores['Total'] = round(sum(scores.values()), 2)
    
    return scores

def extract_and_process_image(
    file_stream: bytes,          
    filename: str,             
    model: nn.Module, 
    max_scores: np.ndarray
) -> Dict[str, Any]:
    """Main pipeline - In-Memory Version"""
    
    # 1. Generate metadata and thumbnail (reuse helper)
    metadata = generate_thumbnail_and_metadata(file_stream, filename)
    
    try:
        # 2. Open image and run AI prediction
        with Image.open(BytesIO(file_stream)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Predict scores
            scores = predict_scores(img, model)
            
            return {
                "status": "success",
                "filename": filename,
                "serial_number": metadata["serial_number"],
                "sample_id": metadata["sample_id"],
                "scores": scores,
                "display_url": metadata["display_url"]
            }
            
    except Exception as e:
        print(f"Error processing: {e}")
        raise e
    

def generate_thumbnail_and_metadata(
    file_bytes: bytes,
    filename: str
) -> Dict[str, Any]:
    """
    Extracts metadata from filename and generates Base64 thumbnail.
    Used for both new uploads and existing DB records.
    """
    # --- PARSING LOGIC (Same as in extract_and_process_image) ---
    sample_id = "UNKNOWN"
    image_suffix = "00"
    
    parts = filename.split("-")
    if len(parts) >= 2:
        sample_id = f"{parts[0]}-{parts[1]}"

    match = re.search(r"Image(\d+)", filename, re.IGNORECASE)
    if match:
        raw_num = match.group(1)
        image_suffix = raw_num[-2:] if len(raw_num) >= 2 else raw_num.zfill(2)

    full_serial = f"{sample_id}-{image_suffix}"

    # --- THUMBNAIL GENERATION ---
    with Image.open(BytesIO(file_bytes)) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_thumb = img.copy()
        img_thumb.thumbnail((400, 400))
        
        buffered = BytesIO()
        img_thumb.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_url = f"data:image/png;base64,{img_str}"
    
    return {
        "serial_number": full_serial,
        "sample_id": sample_id,
        "display_url": base64_url
    }