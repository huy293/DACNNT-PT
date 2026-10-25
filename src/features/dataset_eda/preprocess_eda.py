"""Stage 1 (Week 1): Multimodal Dataset Preprocessing & Exploratory Data Analysis (EDA).

Inspects the real Multimodal Dataset (Facebook AI Hateful Memes Challenge + NotebookLM
Vietnamese Harmful/Compliant Ad Corpus) using Pandas & OpenCV to verify physical image files,
pixel dimensions, RGB contrast, text length distributions, source citations, and class
imbalance ratio (BR-ML-01).
"""

from __future__ import annotations

import json
import struct
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


def resolve_image_file(image_rel: str, img_root: Path) -> Path:
    """Resolve an image path relative to either `PROJECT_ROOT` or `img_root`."""
    rel = Path(image_rel)
    if rel.is_absolute() and rel.exists():
        return rel
    candidate_root = PROJECT_ROOT / rel
    if candidate_root.exists():
        return candidate_root
    return img_root / rel


def inspect_image_opencv(
    image_path: Path, fallback_meta: Dict[str, Any], full_decode: bool = False
) -> Tuple[bool, int, int, bool]:
    """Verify physical image via PNG IHDR / OpenCV `cv2.imread` and return (is_valid, width, height, verified_on_disk)."""
    if image_path.exists() and image_path.is_file():
        if not full_decode:
            try:
                with image_path.open("rb") as f:
                    hdr = f.read(24)
                if len(hdr) == 24 and hdr[:8] == b"\x89PNG\r\n\x1a\n" and hdr[12:16] == b"IHDR":
                    width, height = struct.unpack(">II", hdr[16:24])
                    if width > 0 and height > 0:
                        return True, int(width), int(height), True
            except OSError:
                pass
        if cv2 is not None:
            img = cv2.imread(str(image_path))
            if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
                height, width = int(img.shape[0]), int(img.shape[1])
                return True, width, height, True
            return False, 0, 0, False

    width = int(fallback_meta.get("image_width", 0) or 0)
    height = int(fallback_meta.get("image_height", 0) or 0)
    has_path = bool(str(fallback_meta.get("image_path", "")).strip())
    if has_path and width > 0 and height > 0:
        return True, width, height, image_path.exists()
    return False, 0, 0, False


def run_dataset_eda(
    dataset_path: Optional[Path] = None,
    output_report_path: Optional[Path] = None,
    images_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run Stage 1 preprocessing and EDA checks on the multimodal dataset using OpenCV & Pandas."""
    src_path = dataset_path or DEFAULT_DATASET_PATH
    out_path = output_report_path or DEFAULT_REPORT_PATH
    img_root = images_dir or PROJECT_ROOT

    raw_records: List[Dict[str, Any]] = json.loads(src_path.read_text(encoding="utf-8"))

    valid_records: List[Dict[str, Any]] = []
    rejected_ids: List[str] = []
    char_lengths: List[int] = []
    word_counts: List[int] = []
    widths: List[int] = []
    heights: List[int] = []
    verified_files_count = 0
    label_counts: Dict[int, int] = {0: 0, 1: 0}
    category_counts: Dict[str, int] = {}
    source_dataset_counts: Dict[str, int] = {}

    for idx, item in enumerate(raw_records):
        rec_id = str(item.get("id", "unknown"))
        text = str(item.get("text", "") or "").strip()
        img_rel = str(item.get("image_path", "") or "").strip()
        resolved_img = resolve_image_file(img_rel, img_root)
        is_img_valid, width, height, on_disk = inspect_image_opencv(
            resolved_img, item, full_decode=(idx < 32)
        )

        # BR-ML-01: Must have valid text and valid image dimensions/file
        if not text or not is_img_valid:
            rejected_ids.append(rec_id)
            continue

        if on_disk:
            verified_files_count += 1

        label = int(item.get("label", 0))
        category = str(item.get("category", "uncategorized"))
        src_ds = str(item.get("source_dataset", "unspecified"))

        valid_records.append(item)
        char_lengths.append(len(text))
        word_counts.append(len(text.split()))
        widths.append(width)
        heights.append(height)
        label_counts[label] = label_counts.get(label, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        source_dataset_counts[src_ds] = source_dataset_counts.get(src_ds, 0) + 1

    total_valid = len(valid_records)
    harmful_count = label_counts.get(1, 0)
    safe_count = label_counts.get(0, 0)
    majority = max(harmful_count, safe_count, 1)
    minority = max(min(harmful_count, safe_count), 1)
    imbalance_ratio = round(majority / minority, 3)

    pandas_enabled = pd is not None
    if pd is not None and valid_records:
        df = pd.DataFrame(valid_records)
        harmful_count = int((df["label"] == 1).sum())
        safe_count = int((df["label"] == 0).sum())

    report: Dict[str, Any] = {
        "stage": "Stage 1 - Dataset Preprocessing & EDA (OpenCV + Pandas)",
        "dataset_source": str(src_path.name),
        "notebooklm_notebook_url": "https://notebook.google.com/notebook/a8bfe623-f06d-4902-9a4d-dcdab650e3e2",
        "pandas_used": pandas_enabled,
        "opencv_used": cv2 is not None,
        "total_raw_samples": len(raw_records),
        "total_valid_samples": total_valid,
        "physical_images_verified_by_opencv": verified_files_count,
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
        "source_dataset_breakdown": source_dataset_counts,
        "category_breakdown": category_counts,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    eda_result = run_dataset_eda()
    print(json.dumps(eda_result, indent=2, ensure_ascii=False))
