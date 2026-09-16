"""
Integration / Downloader Pipeline for Kaggle dataset: daylight-lab/cybersecurity-imagery-dataset
File Location: data/integrate_cybersecurity_imagery_dataset.py
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def download_and_integrate():
    print("=== Downloading Kaggle Dataset: daylight-lab/cybersecurity-imagery-dataset ===")
    import kagglehub

    # Download latest version
    path = kagglehub.dataset_download("daylight-lab/cybersecurity-imagery-dataset")

    print("Path to dataset files:", path)
    
    # Inspect downloaded directory contents
    dataset_dir = Path(path)
    if dataset_dir.exists():
        files = list(dataset_dir.rglob("*"))
        print(f"Found {len(files)} total files/directories in dataset path.")
        for f in files[:10]:
            print(" -", f.relative_to(dataset_dir))
        if len(files) > 10:
            print(f" ... and {len(files) - 10} more files.")
    return path


if __name__ == "__main__":
    download_and_integrate()
