"""
Integration Pipeline for HuggingFace neuralchemy/Prompt-injection-dataset ("core").
File Location: data/integrate_Prompt_dataset.py
"""

import sys
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import kagglehub

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CSV_PATH = PROJECT_ROOT / "data" / "unified_privacy_dataset.csv"
JSON_PATH = PROJECT_ROOT / "data" / "unified_privacy_dataset.json"
EXCEL_PATH = PROJECT_ROOT / "data" / "unified_privacy_dataset.xlsx"

CANONICAL_CLASSES = [
    "SAFE",
    "PERSONAL_CONTEXT",
    "IDENTITY_INFORMATION",
    "CONTACT_INFORMATION",
    "FINANCIAL_INFORMATION",
    "CREDENTIAL",
    "GOVERNMENT_ID",
    "AUTHENTICATION_SECRET",
    "PROMPT_INJECTION",
    "OTHER_SENSITIVE",
]

CLASS_TO_ID = {c: i for i, c in enumerate(CANONICAL_CLASSES)}
THREE_CLASS_NAMES = ["SAFE", "PII_PRESENT", "HIGH_RISK"]


def download_cybersecurity_imagery_dataset():
    """Download latest version of daylight-lab/cybersecurity-imagery-dataset via kagglehub."""
    print("=== Downloading Kagglehub Dataset: daylight-lab/cybersecurity-imagery-dataset ===")
    path = kagglehub.dataset_download("daylight-lab/cybersecurity-imagery-dataset")
    print("Path to dataset files:", path)
    return path



def integrate_neuralchemy_dataset():
    print("=== Loading HuggingFace Dataset: neuralchemy/Prompt-injection-dataset (core) ===")
    from datasets import load_dataset

    ds = load_dataset("neuralchemy/Prompt-injection-dataset", "core")
    print(f"Dataset Loaded Successfully: {ds}")

    # Inspect splits
    new_rows = []

    for split_name in ds.keys():
        split_data = ds[split_name]
        print(f"Processing split '{split_name}' with {len(split_data)} records...")
        
        for sample in split_data:
            # Common column names in prompt injection datasets: 'prompt', 'text', 'label', 'is_injection'
            prompt_val = sample.get("prompt", sample.get("text", sample.get("instruction", "")))
            if not prompt_val:
                continue

            prompt_clean = " ".join(str(prompt_val).split())
            if len(prompt_clean) < 8:
                continue

            # Determine label
            lbl = sample.get("label", sample.get("is_injection", sample.get("target", 1)))
            # Label 1 / True / 'injection' -> PROMPT_INJECTION
            # Label 0 / False / 'benign' -> SAFE
            is_inj = bool(lbl == 1 or lbl == "1" or str(lbl).lower() in ("injection", "true", "jailbreak", "adversarial"))

            if is_inj:
                cls_name = "PROMPT_INJECTION"
                cid = 8
                is_risk = True
                dec = "BLOCK"
                three_id = 2
                three_name = "HIGH_RISK"
                sub_cat = "Neuralchemy Prompt Injection"
            else:
                cls_name = "SAFE"
                cid = 0
                is_risk = False
                dec = "ALLOW"
                three_id = 0
                three_name = "SAFE"
                sub_cat = "Neuralchemy Benign Prompt"

            new_rows.append({
                "prompt": prompt_clean,
                "canonical_class": cls_name,
                "canonical_id": cid,
                "sub_category": sub_cat,
                "is_risk": is_risk,
                "decision": dec,
                "three_class_id": three_id,
                "three_class_name": three_name,
            })

    print(f"Extracted {len(new_rows)} processed samples from neuralchemy/Prompt-injection-dataset.")

    # Merge with existing CSV dataset
    df_existing = pd.read_csv(CSV_PATH) if CSV_PATH.exists() else pd.DataFrame()
    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.drop_duplicates(subset=["prompt"], inplace=True)

    print("\n=== Integrated Dataset Summary ===")
    print(f"Total Unified Samples: {len(df_combined)}")
    print(df_combined["canonical_class"].value_counts())

    # Export CSV
    df_combined.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"Saved CSV: {CSV_PATH}")

    # Export JSON
    json_records = df_combined.to_dict(orient="records")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_records, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON: {JSON_PATH}")

    # Export Excel
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_combined.to_excel(writer, sheet_name="Unified Privacy Dataset", index=False)
    print(f"Saved Excel: {EXCEL_PATH}")

    return df_combined


if __name__ == "__main__":
    download_cybersecurity_imagery_dataset()
    integrate_neuralchemy_dataset()

