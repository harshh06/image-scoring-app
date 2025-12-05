# backend/app/utils.py

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from pathlib import Path
from typing import Dict, Any
import numpy as np

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
    
    scores = {
        "Pancreatic Architecture": round(float(actual_scores[0]), 2),
        "Glandular Atrophy": round(float(actual_scores[1]), 2),
        "Pseudotubular Complexes": round(float(actual_scores[2]), 2),
        "Fibrosis": round(float(actual_scores[3]), 2),
    }
    scores['Total'] = round(sum(scores.values()), 2)
    
    return scores

def extract_and_process_image(file_path: Path, thumbnail_dir: Path, model: nn.Module, max_scores: np.ndarray) -> Dict[str, Any]:
    """Main pipeline."""
    filename = file_path.name
    parts = filename.split("-")
    serial = f"{parts[0]}-{parts[1]}" if len(parts) > 1 else "UNKNOWN"

    try:
        with Image.open(file_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save Thumbnail
            img_thumb = img.copy()
            img_thumb.thumbnail((800, 800))
            thumb_filename = f"{file_path.stem}.png"
            img_thumb.save(thumbnail_dir / thumb_filename, "PNG")
            
            # Predict
            scores = predict_scores(img, model)
            
            return {
                "status": "success",
                "filename": filename,
                "serial_number": serial,
                "scores": scores,
                "display_url": f"http://localhost:8000/static/{thumb_filename}"
            }
            
    except Exception as e:
        print(f"Error processing: {e}")
        raise e