import os
import csv
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.amp import autocast, GradScaler  # FIX: Updated import for PyTorch 2.0+
from tqdm import tqdm
from sklearn.metrics import f1_score

import config
from dataset import get_loaders
from transforms import get_train_transforms, get_val_transforms
from model import build_model
from losses import get_loss_function
from utils import set_seed, EarlyStopping, save_checkpoint

def train_one_epoch(model, loader, criterion, optimizer, device, scaler):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    
    for images, labels in tqdm(loader, desc="Training", leave=False):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        
        # MIXED PRECISION FORWARD PASS - FIX: Added device_type='cuda'
        with autocast(device_type='cuda', enabled=config.USE_AMP):
            outputs = model(images)
            loss = criterion(outputs, labels)
            
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        
    return running_loss / total, correct / total, f1_score(all_labels, all_preds, average='macro')

def validate_one_epoch(model, loader, criterion, device):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    
    with torch.no_grad():
        for images, labels in tqdm(loader, desc="Validating", leave=False):
            images, labels = images.to(device), labels.to(device)
            
            # FIX: Added device_type='cuda'
            with autocast(device_type='cuda', enabled=config.USE_AMP):
                outputs = model(images)
                loss = criterion(outputs, labels)
                
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
    return running_loss / total, correct / total, f1_score(all_labels, all_preds, average='macro')

def main():
    set_seed()
    os.makedirs(config.CHECKPOINT_DIR, exist_ok=True)
    device = torch.device(config.DEVICE)
    
    train_transform = get_train_transforms()
    val_transform = get_val_transforms()
    train_loader, val_loader, classes, _ = get_loaders(
        config.DATASET_PATH, train_transform, val_transform, config.BATCH_SIZE
    )

    model = build_model()
    criterion = get_loss_function(train_loader.dataset)
    optimizer = optim.AdamW(model.parameters(), lr=config.LEARNING_RATE, weight_decay=config.WEIGHT_DECAY)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=config.SCHEDULER_FACTOR, patience=config.SCHEDULER_PATIENCE)
    
    early_stopping = EarlyStopping(patience=config.EARLY_STOP_PATIENCE)
    
    # FIX: Updated GradScaler initialization
    scaler = GradScaler('cuda', enabled=config.USE_AMP)  
    
    best_val_acc = 0.0
    checkpoint_path = os.path.join(config.CHECKPOINT_DIR, config.CHECKPOINT_NAME)

    # CSV Logging setup
    with open(config.LOG_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Epoch', 'Train Loss', 'Train Acc', 'Train F1', 'Val Loss', 'Val Acc', 'Val F1'])

    # Training Loop
    for epoch in range(config.EPOCHS):
        print(f"\nEpoch {epoch+1}/{config.EPOCHS}")
        
        train_loss, train_acc, train_f1 = train_one_epoch(model, train_loader, criterion, optimizer, device, scaler)
        val_loss, val_acc, val_f1 = validate_one_epoch(model, val_loader, criterion, device)
        
        scheduler.step(val_loss)
        early_stopping(val_loss)

        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | Train F1: {train_f1:.4f}")
        print(f"Val Loss: {val_loss:.4f}   | Val Acc: {val_acc:.4f}   | Val F1: {val_f1:.4f}")
        
        # Log to CSV
        with open(config.LOG_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([epoch+1, train_loss, train_acc, train_f1, val_loss, val_acc, val_f1])

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print(f"🔥 Validation accuracy improved! Saving model to {checkpoint_path}")
            save_checkpoint(model, optimizer, epoch, val_acc, classes, checkpoint_path)

        # Early stopping check
        if early_stopping.early_stop:
            print("Early stopping triggered. Training stopped.")
            break

    print(f"\nTraining complete. Best Validation Accuracy: {best_val_acc:.4f}")

if __name__ == "__main__":
    main()
