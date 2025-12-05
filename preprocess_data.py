# preprocess_data.py

import os
import pandas as pd
from PIL import Image
from pathlib import Path
from tqdm import tqdm # Import for progress bar

# --- Configuration ---
ROOT_DIR = Path(__file__).parent
RAW_IMAGE_DIR = ROOT_DIR / "dataset" / "raw_images"
PROCESSED_IMAGE_DIR = ROOT_DIR / "dataset" / "processed_images"
LABEL_FILE = ROOT_DIR / "dataset" / "labels.csv"

# Standard size for AI models
TARGET_SIZE = (512, 512) 

def preprocess_images():
    """Reads TIFFs, converts/resizes to PNG, and verifies label availability."""
    
    # 1. Setup
    PROCESSED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load labels and drop rows where any score is missing
    if not LABEL_FILE.exists():
        print(f"[ERROR] Label file not found at {LABEL_FILE}")
        return

    labels_df = pd.read_csv(LABEL_FILE)
    # The 'Total' column often contains summary math, so we check the actual score columns.
    score_cols = ['architecture', 'atrophy', 'complexes', 'fibrosis']
    labels_df = labels_df.dropna(subset=score_cols)
    
    print(f"Loaded {len(labels_df)} entries with complete scores from CSV.")
    
    processed_files = []

    # 2. Iterate through labels and process matching files
    # tqdm provides a neat progress bar in the terminal
    for index, row in tqdm(labels_df.iterrows(), total=len(labels_df), desc="Processing Images"):
        
        filename = row['filename']
        raw_path = RAW_IMAGE_DIR / filename
        
        # New filename for the processed output (e.g., S-3349...png)
        processed_filename = f"{Path(filename).stem}.png"
        processed_path = PROCESSED_IMAGE_DIR / processed_filename
        
        # --- ROBUST ERROR HANDLING FOR MISSING FILES ---
        try:
            # Check if the raw file exists
            if not raw_path.exists():
                # print(f"\n[WARNING] Missing file: {filename}. Skipping entry.")
                continue

            # Check if the processed file already exists (to save time)
            if processed_path.exists():
                # If file is already processed, skip PIL/resize step
                pass 
            else:
                # Open the TIFF image (SLOW STEP)
                img = Image.open(raw_path)
                
                # Convert to RGB and resize (CRUCIAL for CNN training)
                img = img.convert('RGB')
                img_resized = img.resize(TARGET_SIZE)
                
                # Save the lightweight PNG (FAST STEP)
                img_resized.save(processed_path, "PNG")
                
            # Add this successfully processed file to the list
            # We save the *new* PNG filename so the training script can find it easily
            row['filename'] = processed_filename
            processed_files.append(row.to_dict())

        except Exception as e:
            print(f"\n[ERROR] Could not process {filename}. Error: {e}. Skipping.")
            continue
            
    # 3. Create a final, clean CSV containing only successfully processed files
    if not processed_files:
        print("[ERROR] No images were processed successfully. Check your raw_images folder.")
        return

    final_df = pd.DataFrame(processed_files)
    final_labels_path = ROOT_DIR / "dataset" / "final_labels_for_training.csv"
    final_df.to_csv(final_labels_path, index=False)
    
    print("-" * 50)
    print(f"Preprocessing Complete. {len(final_df)} images processed successfully.")
    print(f"Final training CSV saved to: {final_labels_path}")


if __name__ == "__main__":
    # Ensure you install tqdm and pandas: pip install pandas tqdm
    preprocess_images()