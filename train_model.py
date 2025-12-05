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

# --- 1. Configuration ---
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "dataset"
PROCESSED_IMAGE_DIR = DATA_DIR / "processed_images"
LABEL_FILE = DATA_DIR / "final_labels_for_training.csv"
MODEL_SAVE_PATH = ROOT_DIR / "backend" / "pancreas_model.pth"

# Hyperparameters
BATCH_SIZE = 8
NUM_EPOCHS = 20
LEARNING_RATE = 0.001
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

def collate_fn(batch):
    batch = [item for item in batch if item is not None]
    if not batch: return None, None
    return torch.utils.data.dataloader.default_collate(batch)

# --- 4. Training Loop ---
def train_model():
    print(f"--- Starting Training on {torch.cuda.device_count()} GPUs (or CPU) ---")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if str(device) == 'cpu':
        print("NOTE: Training on CPU is slow. Expect 10-20 mins.")

    # Prepare Data
    df = pd.read_csv(LABEL_FILE)
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Standard ResNet Transforms
    data_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    train_dataset = HistologyDataset(train_df, PROCESSED_IMAGE_DIR, data_transforms)
    val_dataset = HistologyDataset(val_df, PROCESSED_IMAGE_DIR, data_transforms)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

    # Setup Model
    model = get_model().to(device)
    criterion = nn.MSELoss() # Mean Squared Error for Regression
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=LEARNING_RATE)

    # Loop
    best_loss = float('inf')
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        running_loss = 0.0
        
        for inputs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS}"):
            if inputs is None: continue
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(train_dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for inputs, labels in val_loader:
                if inputs is None: continue
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                
        val_loss = val_loss / len(val_dataset)
        
        print(f"Loss: Train {epoch_loss:.4f} | Val {val_loss:.4f}")

        # Save Best Model
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"--> Saved Model (Val Loss: {val_loss:.4f})")

    print(f"\nTraining Complete. Model saved to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()