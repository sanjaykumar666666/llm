"""
Offline Training & Checkpoint Generator for BERT & Naive Bayes Privacy Classifiers.
File Location: ml_engine/train_classifier.py

Trains and saves persistent model checkpoints to ml_engine/checkpoints/:
  - distilbert_privacy_classifier.pt
  - naive_bayes_model.joblib
  - model_metadata.json

Computes genuine evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix).
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

from transformers import AutoTokenizer, AutoModel, logging as hf_logging
hf_logging.set_verbosity_error()

from data.unified_privacy_dataset import (
    CANONICAL_CLASSES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    get_canonical_dataset,
    export_dataset_to_json,
    export_dataset_to_csv,
)

CHECKPOINTS_DIR = PROJECT_ROOT / "ml_engine" / "checkpoints"


class DistilBertClassificationHead(nn.Module):
    """PyTorch classification head on top of DistilBERT [CLS] embedding (768-dim)."""

    def __init__(self, embedding_dim: int = 768, num_classes: int = len(CANONICAL_CLASSES), hidden_dim: int = 256, dropout: float = 0.2):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(x)


def train_and_save_all(model_name: str = "distilbert-base-uncased") -> Dict[str, Any]:
    """
    Executes full offline training, evaluation, and checkpoint persistence.
    """
    start_time = time.time()
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Export unified dataset JSON/CSV
    export_dataset_to_json(str(PROJECT_ROOT / "data" / "unified_privacy_dataset.json"))
    export_dataset_to_csv(str(PROJECT_ROOT / "data" / "unified_privacy_dataset.csv"))

    raw_data = get_canonical_dataset()
    texts = [item[0] for item in raw_data]
    labels_str = [item[1] for item in raw_data]
    labels_idx = [CLASS_TO_ID[cls_name] for cls_name in labels_str]

    print(f"Loaded {len(texts)} samples across {len(CANONICAL_CLASSES)} canonical classes.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")

    # 2. Tokenize & Extract DistilBERT [CLS] Representations
    print("Loading pretrained DistilBERT encoder...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoder = AutoModel.from_pretrained(model_name).to(device)
    encoder.eval()

    embeddings_list = []
    print("Extracting DistilBERT contextual embeddings...")
    with torch.no_grad():
        for i, text in enumerate(texts):
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128,
            ).to(device)
            out = encoder(**inputs)
            cls_vec = out.last_hidden_state[:, 0, :]
            embeddings_list.append(cls_vec.cpu())

    X_embeddings = torch.cat(embeddings_list, dim=0)
    y_tensor = torch.tensor(labels_idx, dtype=torch.long)

    # 3. Train & Evaluate DistilBERT Classification Head
    print("Training PyTorch DistilBERT Classification Head...")
    # Split train/val for genuine metrics evaluation
    X_train_emb, X_val_emb, y_train, y_val = train_test_split(
        X_embeddings.numpy(), labels_idx, test_size=0.25, random_state=42, stratify=labels_idx
    )

    X_train_t = torch.tensor(X_train_emb, dtype=torch.float32).to(device)
    y_train_t = torch.tensor(y_train, dtype=torch.long).to(device)
    X_val_t = torch.tensor(X_val_emb, dtype=torch.float32).to(device)
    y_val_t = torch.tensor(y_val, dtype=torch.long).to(device)

    head = DistilBertClassificationHead(
        embedding_dim=768,
        num_classes=len(CANONICAL_CLASSES),
        hidden_dim=256,
        dropout=0.15,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(head.parameters(), lr=0.003, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80)

    head.train()
    for epoch in range(80):
        optimizer.zero_grad()
        logits = head(X_train_t)
        loss = criterion(logits, y_train_t)
        loss.backward()
        optimizer.step()
        scheduler.step()

    # Evaluate on held-out validation set
    head.eval()
    with torch.no_grad():
        val_logits = head(X_val_t)
        val_preds = torch.argmax(val_logits, dim=-1).cpu().numpy()

    bert_acc = float(accuracy_score(y_val, val_preds))
    bert_prec, bert_rec, bert_f1, _ = precision_recall_fscore_support(y_val, val_preds, average="weighted", zero_division=0)
    bert_cm = confusion_matrix(y_val, val_preds).tolist()

    print(f"DistilBERT Head Validation Accuracy: {bert_acc * 100:.2f}% | F1: {bert_f1:.4f}")

    # Retrain on full dataset for final deployment checkpoint
    final_head = DistilBertClassificationHead(
        embedding_dim=768,
        num_classes=len(CANONICAL_CLASSES),
        hidden_dim=256,
        dropout=0.15,
    ).to(device)
    final_optimizer = optim.AdamW(final_head.parameters(), lr=0.003, weight_decay=0.01)
    final_scheduler = optim.lr_scheduler.CosineAnnealingLR(final_optimizer, T_max=90)
    X_full_t = X_embeddings.to(device)
    y_full_t = y_tensor.to(device)

    final_head.train()
    for epoch in range(90):
        final_optimizer.zero_grad()
        loss = criterion(final_head(X_full_t), y_full_t)
        loss.backward()
        final_optimizer.step()
        final_scheduler.step()

    final_head.eval()

    # Save PyTorch Head Checkpoint
    bert_checkpoint_path = CHECKPOINTS_DIR / "distilbert_privacy_classifier.pt"
    torch.save({
        "state_dict": final_head.state_dict(),
        "model_name": model_name,
        "embedding_dim": 768,
        "num_classes": len(CANONICAL_CLASSES),
        "classes": CANONICAL_CLASSES,
        "class_to_id": CLASS_TO_ID,
        "id_to_class": ID_TO_CLASS,
        "metrics": {
            "validation_accuracy": round(bert_acc, 4),
            "validation_precision": round(float(bert_prec), 4),
            "validation_recall": round(float(bert_rec), 4),
            "validation_f1": round(float(bert_f1), 4),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, bert_checkpoint_path)
    print(f"Saved PyTorch checkpoint to {bert_checkpoint_path}")

    # 4. Train & Save Naive Bayes Model
    print("Training Naive Bayes (TF-IDF + MultinomialNB)...")
    texts_train, texts_val, nb_y_train, nb_y_val = train_test_split(
        texts, labels_idx, test_size=0.25, random_state=42, stratify=labels_idx
    )

    vectorizer = TfidfVectorizer(
        max_features=3500,
        stop_words="english",
        ngram_range=(1, 3),
        sublinear_tf=True,
    )
    nb_model = MultinomialNB(alpha=0.08)

    X_train_nb = vectorizer.fit_transform(texts_train)
    nb_model.fit(X_train_nb, nb_y_train)

    X_val_nb = vectorizer.transform(texts_val)
    nb_val_preds = nb_model.predict(X_val_nb)

    nb_acc = float(accuracy_score(nb_y_val, nb_val_preds))
    nb_prec, nb_rec, nb_f1, _ = precision_recall_fscore_support(nb_y_val, nb_val_preds, average="weighted", zero_division=0)
    nb_cm = confusion_matrix(nb_y_val, nb_val_preds).tolist()

    print(f"Naive Bayes Validation Accuracy: {nb_acc * 100:.2f}% | F1: {nb_f1:.4f}")

    # Retrain on full dataset
    final_vectorizer = TfidfVectorizer(
        max_features=3500,
        stop_words="english",
        ngram_range=(1, 3),
        sublinear_tf=True,
    )
    final_nb = MultinomialNB(alpha=0.08)
    X_full_nb = final_vectorizer.fit_transform(texts)
    final_nb.fit(X_full_nb, labels_idx)

    # Save Naive Bayes artifact
    nb_checkpoint_path = CHECKPOINTS_DIR / "naive_bayes_model.joblib"
    joblib.dump({
        "vectorizer": final_vectorizer,
        "model": final_nb,
        "classes": CANONICAL_CLASSES,
        "class_to_id": CLASS_TO_ID,
        "id_to_class": ID_TO_CLASS,
        "metrics": {
            "validation_accuracy": round(nb_acc, 4),
            "validation_precision": round(float(nb_prec), 4),
            "validation_recall": round(float(nb_rec), 4),
            "validation_f1": round(float(nb_f1), 4),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, nb_checkpoint_path)
    print(f"Saved Naive Bayes artifact to {nb_checkpoint_path}")

    # 5. Save comprehensive model metadata
    elapsed = time.time() - start_time
    metadata = {
        "dataset_size": len(texts),
        "classes": CANONICAL_CLASSES,
        "class_to_id": CLASS_TO_ID,
        "id_to_class": ID_TO_CLASS,
        "training_duration_seconds": round(elapsed, 2),
        "bert": {
            "base_model": model_name,
            "architecture": "DistilBERT [CLS] 768 -> Linear(256) -> LayerNorm -> ReLU -> Linear(10)",
            "checkpoint_file": str(bert_checkpoint_path.name),
            "validation_metrics": {
                "accuracy": round(bert_acc, 4),
                "precision": round(float(bert_prec), 4),
                "recall": round(float(rec) if (rec := bert_rec) is not None else 0.0, 4),
                "f1_score": round(float(bert_f1), 4),
                "confusion_matrix": bert_cm,
            }
        },
        "naive_bayes": {
            "algorithm": "MultinomialNB(alpha=0.08)",
            "vectorizer": "TfidfVectorizer(ngram_range=(1,3), max_features=3500, sublinear_tf=True)",
            "checkpoint_file": str(nb_checkpoint_path.name),
            "validation_metrics": {
                "accuracy": round(nb_acc, 4),
                "precision": round(float(nb_prec), 4),
                "recall": round(float(rec) if (rec := nb_rec) is not None else 0.0, 4),
                "f1_score": round(float(nb_f1), 4),
                "confusion_matrix": nb_cm,
            }
        },
        "hybrid_combination": {
            "formula": "P_hybrid(c) = alpha * P_bert(c) + (1 - alpha) * P_nb(c)",
            "alpha_default": 0.60,
            "description": "60% DistilBERT contextual semantic probability + 40% Naive Bayes token n-gram probability"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    metadata_path = CHECKPOINTS_DIR / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved Model Metadata to {metadata_path}")

    return metadata


if __name__ == "__main__":
    train_and_save_all()
