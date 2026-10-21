"""Stage 1 (Week 1): Multimodal Dataset Preprocessing & Exploratory Data Analysis (EDA).

Inspects Hateful Memes / Multimodal Harmful Ad datasets using Pandas & OpenCV (with
standard-library fallback) to verify image counts, dimensions, text lengths, and
class imbalance ratio (BR-ML-01).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "src" / "mocks" / "sample_ads_dataset.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "src" / "mocks" / "eda_report.json"

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None


def inspect_image_opencv(image_path: Path, fallback_meta: Dict[str, Any]) -> Tuple[bool, int, int]:
    """Check if an image is valid and return (is_valid, width, height) using OpenCV or metadata."""
    if cv2 is not None and image_path.exists():
        img = cv2.imread(str(image_path))
        if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
            height, width = int(img.shape[0]), int(img.shape[1])
            return True, width, height
        return False, 0, 0

    width = int(fallback_meta.get("image_width", 0) or 0)
    height = int(fallback_meta.get("image_height", 0) or 0)
    has_path = bool(str(fallback_meta.get("image_path", "")).strip())
    if has_path and width > 0 and height > 0:
        return True, width, height
    return False, 0, 0


def run_dataset_eda(
    dataset_path: Optional[Path] = None,
    output_report_path: Optional[Path] = None,
    images_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run Stage 1 preprocessing and EDA checks on a multimodal ad dataset."""
    src_path = dataset_path or DEFAULT_DATASET_PATH
    out_path = output_report_path or DEFAULT_REPORT_PATH
    img_root = images_dir or src_path.parent

    raw_records: List[Dict[str, Any]] = json.loads(src_path.read_text(encoding="utf-8"))

    valid_records: List[Dict[str, Any]] = []
    rejected_ids: List[str] = []
    char_lengths: List[int] = []
    word_counts: List[int] = []
    widths: List[int] = []
    heights: List[int] = []
    label_counts: Dict[int, int] = {0: 0, 1: 0}
    category_counts: Dict[str, int] = {}

    for item in raw_records:
        rec_id = str(item.get("id", "unknown"))
        text = str(item.get("text", "") or "").strip()
        img_rel = str(item.get("image_path", "") or "").strip()
        is_img_valid, width, height = inspect_image_opencv(img_root / img_rel, item)

        # BR-ML-01: Must have valid text and valid image dimensions/file
        if not text or not is_img_valid:
            rejected_ids.append(rec_id)
            continue

        label = int(item.get("label", 0))
        category = str(item.get("category", "uncategorized"))

        valid_records.append(item)
        char_lengths.append(len(text))
        word_counts.append(len(text.split()))
        widths.append(width)
        heights.append(height)
        label_counts[label] = label_counts.get(label, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    total_valid = len(valid_records)
    harmful_count = label_counts.get(1, 0)
    safe_count = label_counts.get(0, 0)
    majority = max(harmful_count, safe_count, 1)
    minority = max(min(harmful_count, safe_count), 1)
    imbalance_ratio = round(majority / minority, 3)

    # Optional Pandas summary verification when pandas is installed on Kaggle
    pandas_enabled = pd is not None
    if pd is not None and valid_records:
        df = pd.DataFrame(valid_records)
        harmful_count = int((df["label"] == 1).sum())
        safe_count = int((df["label"] == 0).sum())

    report: Dict[str, Any] = {
        "stage": "Stage 1 - Dataset Preprocessing & EDA",
        "dataset_source": str(src_path.name),
        "pandas_used": pandas_enabled,
        "opencv_used": cv2 is not None,
        "total_raw_samples": len(raw_records),
        "total_valid_samples": total_valid,
        "rejected_corrupted_samples": len(rejected_ids),
        "rejected_sample_ids": rejected_ids,
        "image_statistics": {
            "min_width": min(widths) if widths else 0,
            "max_width": max(widths) if widths else 0,
            "avg_width": round(sum(widths) / total_valid, 1) if total_valid else 0.0,
            "min_height": min(heights) if heights else 0,
            "max_height": max(heights) if heights else 0,
            "avg_height": round(sum(heights) / total_valid, 1) if total_valid else 0.0,
        },
        "text_statistics": {
            "min_char_length": min(char_lengths) if char_lengths else 0,
            "max_char_length": max(char_lengths) if char_lengths else 0,
            "avg_char_length": round(sum(char_lengths) / total_valid, 1) if total_valid else 0.0,
            "min_word_count": min(word_counts) if word_counts else 0,
            "max_word_count": max(word_counts) if word_counts else 0,
            "avg_word_count": round(sum(word_counts) / total_valid, 1) if total_valid else 0.0,
        },
        "class_distribution": {
            "harmful_ads_label_1": harmful_count,
            "safe_ads_label_0": safe_count,
            "harmful_percentage": round((harmful_count / total_valid) * 100, 2) if total_valid else 0.0,
            "safe_percentage": round((safe_count / total_valid) * 100, 2) if total_valid else 0.0,
            "imbalance_ratio": imbalance_ratio,
            "is_imbalanced": imbalance_ratio > 1.5,
        },
        "category_breakdown": category_counts,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    eda_result = run_dataset_eda()
    print(json.dumps(eda_result, indent=2, ensure_ascii=False))
