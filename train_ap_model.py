# train_model.py

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from sklearn.model_selection import train_test_split
import pandas as pd
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import numpy as np
import json
import matplotlib.pyplot as plt
import wandb

# --- 1. Configuration ---
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "dataset"
PROCESSED_IMAGE_DIR = DATA_DIR / "processed_images"
LABEL_FILE = DATA_DIR / "final_labels_for_training.csv"
MODEL_SAVE_PATH = ROOT_DIR / "backend" / "ap_model.pth"
METRICS_SAVE_PATH = ROOT_DIR / "training_metrics.json"
PLOT_SAVE_PATH = ROOT_DIR / "loss_curves.png"

# Hyperparameters
BATCH_SIZE = 8
NUM_EPOCHS = 35
LEARNING_RATE = 0.0001
NUM_CLASSES = 4 # The 4 scores

# Max scores for normalization (Architecture, Atrophy, Complexes, Fibrosis)
# We normalize targets to 0-1 range for better training stability
MAX_SCORES = np.array([4.0, 3.0, 3.0, 4.0], dtype=np.float32)

# --- 2. Custom Dataset Loader ---
class HistologyDataset(Dataset):
    def __init__(self, df, img_dir, transform=None):
        self.labels_frame = df
        self.img_dir = img_dir
        self.transform = transform

    def __len__(self):
        return len(self.labels_frame)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        # Get filename
        img_name = self.labels_frame.iloc[idx, 0]
        img_path = self.img_dir / img_name
        
        # Load Image
        try:
            image = Image.open(img_path).convert('RGB')
        except FileNotFoundError:
            return None # Skip missing files

        # Get Scores (Columns 1-4)
        scores = self.labels_frame.iloc[idx, 1:NUM_CLASSES+1].values.astype('float32')
        
        # NORMALIZE SCORES (0 to 1 range)
        # This helps the neural network converge much faster
        scores = scores / MAX_SCORES
        
        labels = torch.from_numpy(scores)

        if self.transform:
            image = self.transform(image)
            
        return image, labels

# --- 3. Model Definition ---
def get_model():
    # Load ResNet18 pre-trained on ImageNet
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    
    # 1. Freeze early layers (Keep the generic vision features)
    for param in model.parameters():
        param.requires_grad = False
        
    # 2. Unfreeze the last two blocks (Let it learn tissue texture)
    for param in model.layer4.parameters():
        param.requires_grad = True
    for param in model.layer3.parameters():
        param.requires_grad = True

    # 3. Replace the Head (Classification) with Regression (4 numbers)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, NUM_CLASSES)
    
    return model

# This helper function handles missing images gracefully.
# When the DataLoader grabs a batch of 8 images, some might be None
# (because the file was missing in __getitem__). This function filters
# those out so training doesn't crash on a bad image.
def collate_fn(batch):
    batch = [item for item in batch if item is not None]
    if not batch: return None, None
    return torch.utils.data.dataloader.default_collate(batch)

# --- 4. Training Loop ---
def train_model():

    # =========================================================
    # STEP 1: PICK THE DEVICE (GPU or CPU)
    # =========================================================
    # PyTorch can run math on either a GPU (very fast) or CPU (slow).
    # This checks if a GPU (CUDA) is available. On your M2 Mac, it
    # will fall back to CPU. Training ~400 images on CPU takes ~10-20 min.
    if torch.backends.mps.is_available():
        device = torch.device("mps")        # ← Apple Silicon GPU (your M2)
    elif torch.cuda.is_available():
        device = torch.device("cuda:0")      # ← NVIDIA GPU
    else:
        device = torch.device("cpu")    

    print(f"--- Training will run on: {device.type.upper()} ({device}) ---")
    if device.type == 'cpu':
        print("NOTE: Training on CPU is slow. Expect 10-20 mins.")

    # =========================================================
    # STEP 2: LOAD AND SPLIT THE DATA (Train / Val / Test)
    # =========================================================
    # Read the CSV that has columns: [filename, architecture, atrophy, complexes, fibrosis]
    df = pd.read_csv(LABEL_FILE)

    # 3-Way Split: 80% Train, 10% Validation, 10% Test
    # - First split: Hold out 10% of ALL data into a "vault" for the final Test Set
    train_val_df, test_df = train_test_split(df, test_size=0.10, random_state=42)

    # - Second split: Split remaining 90% into Train (80% of total) and Val (10% of total)
    #   0.1111 * 0.90 ≈ 0.10
    train_df, val_df = train_test_split(train_val_df, test_size=0.1111, random_state=42)

    print(f"Dataset Split: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")

    # =========================================================
    # STEP 3: DEFINE IMAGE TRANSFORMS & DATA AUGMENTATION
    # =========================================================
    # ResNet expects 224x224 input. Instead of CenterCrop (which cuts
    # off outer edges and loses lesion data), we use Resize((224, 224))
    # so the entire tissue section is visible to the model.
    #
    # We create TWO separate transform pipelines:
    # 1. train_transforms: Has DATA AUGMENTATION (flips, rotations, color jitter)
    #    to artificially expand our training dataset and prevent overfitting.
    # 2. val_transforms: NO augmentation — purely deterministic resize & normalize
    #    so validation & test evaluation is fair and consistent every time.

    train_transforms = transforms.Compose([
        # Direct resize to (224, 224): preserves 100% of the tissue (no edges chopped off)
        transforms.Resize((224, 224)),

        # --- DATA AUGMENTATION ---
        # 1. Flips: Tissues have no "up" or "down" under a microscope
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),

        # 2. Rotation: Slides can be placed on the microscope stage at any angle
        transforms.RandomRotation(degrees=45),

        # 3. Color variation: Simulates slight differences in staining or microscope lighting
        transforms.ColorJitter(brightness=0.1, contrast=0.1),

        # --- TENSOR CONVERSION & NORMALIZATION ---
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # =========================================================
    # STEP 4: CREATE DATASETS AND DATALOADERS
    # =========================================================
    # Notice: train_dataset gets train_transforms (with augmentation),
    # while val_dataset and test_dataset get val_transforms (clean/untouched).
    train_dataset = HistologyDataset(train_df, PROCESSED_IMAGE_DIR, train_transforms)
    val_dataset = HistologyDataset(val_df, PROCESSED_IMAGE_DIR, val_transforms)
    test_dataset = HistologyDataset(test_df, PROCESSED_IMAGE_DIR, val_transforms)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

    # =========================================================
    # STEP 5: SET UP MODEL, LOSS FUNCTION, AND OPTIMIZER
    # =========================================================

    # get_model() loads ResNet18, freezes layers, replaces the head → moves it to GPU/CPU
    model = get_model().to(device)

    # LOSS FUNCTION: MSE (Mean Squared Error)
    # This measures "how wrong" the model's predictions are.
    # Example: if the model predicts Fibrosis=0.7 but the real answer is 0.5,
    #   the error for that one value = (0.7 - 0.5)² = 0.04
    # MSE averages this across all 4 scores and all images in the batch.
    # Lower MSE = better predictions.
    criterion = nn.MSELoss()

    # OPTIMIZER: Adam
    # After we know HOW WRONG the model is (loss), the optimizer decides
    # HOW TO ADJUST the model's internal numbers to be less wrong next time.
    # Adam is the most popular optimizer — it adapts the learning speed for
    # each parameter individually.
    #
    # filter(lambda p: p.requires_grad, ...) → ONLY pass the unfrozen parameters.
    # We froze layers 1-2 earlier, so we don't want the optimizer wasting effort
    # trying to update those. It only updates layer3, layer4, and the fc head.
    #
    # lr=LEARNING_RATE (0.001) → how big each adjustment step is.
    #   Too high (0.1) = model overshoots and never converges
    #   Too low (0.00001) = model learns too slowly, might get stuck
    #   0.001 is a safe default for Adam.
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=LEARNING_RATE)

    # =========================================================
    # STEP 6: THE ACTUAL TRAINING LOOP (With W&B Tracking)
    # =========================================================
    # An "epoch" = one complete pass through ALL training images.
    # We do NUM_EPOCHS (35) passes. Each pass, the model gets slightly better.

    # Initialize Weights & Biases (W&B) for live cloud metric tracking
    wandb.init(
        project="ap-pancreatitis-scoring",
        name="resnet18-transfer-aug",
        config={
            "architecture": "ResNet18",
            "learning_rate": LEARNING_RATE,
            "epochs": NUM_EPOCHS,
            "batch_size": BATCH_SIZE,
            "loss_function": "MSE",
            "optimizer": "Adam",
            "unfrozen_layers": ["layer3", "layer4", "fc"],
            "augmentation": "RandomHorizontalFlip, RandomVerticalFlip, RandomRotation(45), ColorJitter"
        }
    )

    history = {
        "train_loss": [],
        "val_loss": []
    }

    best_loss = float('inf')  # Start with "infinitely bad" so any real loss beats it
    
    for epoch in range(NUM_EPOCHS):

        # --- TRAINING PHASE ---
        model.train()  # Tell PyTorch: "we're training" (enables dropout, batch norm updates)
        running_loss = 0.0
        
        # Loop through batches of 8 images at a time (BATCH_SIZE=8)
        # tqdm just shows a progress bar in the terminal
        for inputs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS}"):
            if inputs is None: continue

            # Move the images and labels to GPU/CPU (must be on same device as model)
            inputs, labels = inputs.to(device), labels.to(device)

            # THE 4 MAGIC LINES OF TRAINING:
            optimizer.zero_grad()        # 1. Clear old gradients (reset the "adjustment notes")
            outputs = model(inputs)      # 2. FORWARD PASS: feed images through model, get predictions
            loss = criterion(outputs, labels)  # 3. Calculate how wrong the predictions are (MSE)
            loss.backward()              # 4a. BACKWARD PASS: calculate which direction to adjust each parameter
            optimizer.step()             # 4b. Actually adjust the parameters by a small amount

            # Accumulate the loss for this batch (multiply by batch size to un-average it)
            running_loss += loss.item() * inputs.size(0)

        # Average loss across all training images for this epoch
        epoch_loss = running_loss / len(train_dataset)
        
        # --- VALIDATION PHASE ---
        # Now we check: "did the model actually get better, or did it just memorize?"
        model.eval()  # Tell PyTorch: "we're evaluating" (disables dropout, freezes batch norm)
        val_loss = 0.0

        # torch.no_grad() = "don't track gradients" — saves memory and speed
        # because we're NOT training here, just measuring performance.
        with torch.no_grad():
            for inputs, labels in val_loader:
                if inputs is None: continue
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                
        val_loss = val_loss / len(val_dataset)
        
        # Save metrics for plotting
        history["train_loss"].append(epoch_loss)
        history["val_loss"].append(val_loss)

        # Log metrics to Weights & Biases cloud dashboard
        wandb.log({
            "epoch": epoch + 1,
            "train_loss": epoch_loss,
            "val_loss": val_loss,
            "best_val_loss": best_loss
        })

        # Print both losses side by side so you can spot overfitting:
        # If train_loss keeps going down but val_loss goes UP → overfitting!
        # If both go down together → the model is genuinely learning.
        print(f"Loss: Train {epoch_loss:.4f} | Val {val_loss:.4f}")

        # =========================================================
        # STEP 7: SAVE THE BEST MODEL
        # =========================================================
        # Only save the model when it achieves a NEW BEST validation loss.
        # This way, even if later epochs overfit, we keep the best version.
        # This is like saving your game only when you beat your high score.
        if val_loss < best_loss:
            best_loss = val_loss
            # model.state_dict() = all the model's learned numbers (weights)
            # We save ONLY the weights, not the model architecture.
            # To use it later, you rebuild the architecture (get_model()) and
            # load these weights on top of it.
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"--> Saved Model (Val Loss: {val_loss:.4f})")

    print(f"\nTraining Complete. Best validation model saved to: {MODEL_SAVE_PATH}")

    # =========================================================
    # STEP 8: FINAL UNBIASED TEST EVALUATION & LOGGING
    # =========================================================
    # The test set was NEVER seen during training or validation selection.
    # We now reload the best saved checkpoint and measure its true
    # real-world generalization error.
    print("\n" + "="*50)
    print("STEP 8: FINAL UNBIASED EVALUATION ON TEST SET")
    print("="*50)
    model.load_state_dict(torch.load(MODEL_SAVE_PATH, map_location=device))
    model.eval()

    test_loss = 0.0
    with torch.no_grad():
        for inputs, labels in test_loader:
            if inputs is None: continue
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            test_loss += loss.item() * inputs.size(0)

    test_loss = test_loss / len(test_dataset)
    print(f"--> Final Test Set MSE Loss: {test_loss:.4f}")

    # 1. Log final test metric to W&B
    wandb.log({"test_mse_loss": test_loss})

    # 2. Save local training metrics JSON (backup copy)
    metrics_summary = {
        "best_val_loss": best_loss,
        "final_test_loss": test_loss,
        "epochs": NUM_EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "history": history
    }
    with open(METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics_summary, f, indent=4)
    print(f"--> Saved training metrics JSON to: {METRICS_SAVE_PATH}")

    # 3. Generate and save local loss curve plot (ready for README embedding)
    plt.figure(figsize=(8, 5))
    epochs_range = range(1, NUM_EPOCHS + 1)
    plt.plot(epochs_range, history["train_loss"], label="Train Loss", color="#1f77b4", linewidth=2)
    plt.plot(epochs_range, history["val_loss"], label="Validation Loss", color="#ff7f0e", linewidth=2)
    plt.title("ResNet-18 AP Tissue Scoring Loss Curve", fontsize=14, fontweight="bold")
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("MSE Loss", fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(PLOT_SAVE_PATH, dpi=300)
    plt.close()
    print(f"--> Saved loss curve plot to: {PLOT_SAVE_PATH}")

    # 4. Finish W&B run
    wandb.finish()

if __name__ == "__main__":
    train_model()