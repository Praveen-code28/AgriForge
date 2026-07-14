import torch
import torch.nn as nn
import torch.nn.functional as F
import config
from dataset import compute_class_weights

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, target):
        ce_loss = F.cross_entropy(logits, target, reduction='none')
        pt = torch.exp(-ce_loss)
        loss = (self.alpha * (1 - pt)**self.gamma * ce_loss).mean()
        return loss

def get_loss_function(train_dataset, mode=config.CLASS_WEIGHT_MODE):
    if mode == "balanced":
        weights = compute_class_weights(train_dataset).to(config.DEVICE)
        return nn.CrossEntropyLoss(weight=weights)
    elif mode == "focal":
        return FocalLoss()
    else:
        return nn.CrossEntropyLoss()
