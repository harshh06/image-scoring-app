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

# --- CONFIGURATION ---
# Must match training script exactly
NUM_CLASSES = 4
MAX_SCORES = np.array([4.0, 3.0, 3.0, 4.0], dtype=np.float32)

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
    # This prevents the "Zoomed In" bug.
    image = image.resize((512, 512))
    
    # 2. Transform for PyTorch
    input_tensor = MODEL_TRANSFORMS(image)
    input_batch = input_tensor.unsqueeze(0) # Add batch dimension
    
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

def extract_and_process_image(file_path: Path, thumbnail_dir: Path, model: nn.Module, max_scores: np.ndarray) -> Dict[str, Any]:
    """Main pipeline."""
    filename = file_path.name
    
    # --- START OF NEW PARSING LOGIC ---
    # 1. Default fallback
    sample_id = "UNKNOWN"
    image_suffix = "00"
    
    # 2. Extract Sample ID (e.g., "S-3349")
    parts = filename.split("-")
    if len(parts) >= 2:
        sample_id = f"{parts[0]}-{parts[1]}"

    # 3. Extract Image Number (e.g., "001" from "Image001")
    # This regex looks for "Image" followed by numbers
    match = re.search(r"Image(\d+)", filename, re.IGNORECASE)
    if match:
        raw_num = match.group(1) # Gets "001"
        # Take the last 2 digits for cleaner ID (e.g. "01")
        image_suffix = raw_num[-2:] if len(raw_num) >= 2 else raw_num.zfill(2)

    # 4. Construct Unique Serial (e.g., "S-3349-01")
    full_serial = f"{sample_id}-{image_suffix}"
    # --- END OF NEW PARSING LOGIC ---

    try:
        with Image.open(file_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save Thumbnail
            img_thumb = img.copy()
            
            # CRITICAL OPTIMIZATION: Resize before converting to Base64
            # Your previous code skipped this, which would make the Base64 string HUGE (50MB+).
            # This keeps the response fast (approx 100KB).
            img_thumb.thumbnail((400, 400)) 
            
            buffered = BytesIO()
            img_thumb.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_url = f"data:image/png;base64,{img_str}"
            
            # Predict
            scores = predict_scores(img, model)
            
            return {
                "status": "success",
                "filename": filename,
                "serial_number": full_serial, # NEW: Unique ID (S-3602-01)
                "sample_id": sample_id,       # NEW: Group ID (S-3602)
                "scores": scores,
                "display_url": base64_url
            }
            
    except Exception as e:
        print(f"Error processing: {e}")
        raise e