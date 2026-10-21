"""Kaggle Notebook Reference Script (Stages 1 & 2): OpenAI CLIP + Classifier Pipeline.

Can be uploaded directly to Kaggle Notebook (supports `# %%` cell markers) to run on
the Facebook Hateful Memes Challenge dataset (`/kaggle/input/hateful-memes/...`).
"""

from __future__ import annotations

# %% [markdown]
# # Đề tài: Xây dựng mô hình đa phương thức nhằm phát hiện quảng cáo số gây hại dựa trên văn bản – hình ảnh
# - **Giai đoạn 1:** Tiền xử lý & Thống kê dữ liệu (Pandas + OpenCV)
# - **Giai đoạn 2:** Trích xuất đặc trưng bằng Transfer Learning (`openai/clip-vit-base-patch32`) & Huấn luyện Classifier (`MLP`, `SVM`, `LightGBM`)

# %%
import os
from pathlib import Path
from typing import List, Tuple


def run_kaggle_clip_pipeline(
    jsonl_path: str = "/kaggle/input/hateful-memes/train.jsonl",
    img_dir: str = "/kaggle/input/hateful-memes",
    output_features_csv: str = "features.csv",
    output_model_pkl: str = "harmful_ad_classifier.pkl",
    max_samples: int = 2000,
) -> None:
    """Full Kaggle GPU/CPU pipeline using HuggingFace CLIP & Scikit-Learn MLPClassifier."""
    import cv2  # type: ignore
    import joblib  # type: ignore
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore
    import torch  # type: ignore
    from PIL import Image  # type: ignore
    from sklearn.metrics import accuracy_score, classification_report, roc_auc_score  # type: ignore
    from sklearn.model_selection import train_test_split  # type: ignore
    from sklearn.neural_network import MLPClassifier  # type: ignore
    from transformers import CLIPModel, CLIPProcessor  # type: ignore

    # 1. Stage 1: Load dataset & EDA with Pandas + OpenCV
    df = pd.read_json(jsonl_path, lines=True)
    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42).reset_index(drop=True)

    df["text_len"] = df["text"].astype(str).str.len()
    print(f"Total samples: {len(df)}")
    print("Label distribution:\n", df["label"].value_counts(normalize=True))

    # 2. Stage 2 (Week 2): Load pre-trained OpenAI CLIP
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_id)
    clip_model = CLIPModel.from_pretrained(model_id).to(device)
    clip_model.eval()

    fused_vectors: List[np.ndarray] = []
    valid_labels: List[int] = []

    for _, row in df.iterrows():
        full_img_path = os.path.join(img_dir, str(row["img"]))
        img_bgr = cv2.imread(full_img_path)
        if img_bgr is None:
            continue
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        text_str = str(row["text"])

        inputs = processor(
            text=[text_str],
            images=pil_img,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77,
        ).to(device)

        with torch.no_grad():
            img_emb = clip_model.get_image_features(pixel_values=inputs["pixel_values"])
            txt_emb = clip_model.get_text_features(
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"]
            )
            img_emb = img_emb / img_emb.norm(p=2, dim=-1, keepdim=True)
            txt_emb = txt_emb / txt_emb.norm(p=2, dim=-1, keepdim=True)
            # Concatenate 512-d image vector + 512-d text vector -> 1024-d vector
            concat_vec = torch.cat([img_emb, txt_emb], dim=-1).cpu().numpy().flatten()

        fused_vectors.append(concat_vec)
        valid_labels.append(int(row["label"]))

    X = np.vstack(fused_vectors)
    y = np.array(valid_labels)
    feat_df = pd.DataFrame(X, columns=[f"feat_{i:04d}" for i in range(X.shape[1])])
    feat_df.insert(0, "label", y)
    feat_df.to_csv(output_features_csv, index=False)
    print(f"Saved {X.shape[0]} concatenated vectors ({X.shape[1]} dims) to {output_features_csv}")

    # 3. Stage 2 (Week 3): Train MLPClassifier (2 hidden layers)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    clf = MLPClassifier(
        hidden_layer_sizes=(256, 64),
        activation="relu",
        max_iter=300,
        early_stopping=True,
        random_state=42,
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    print(f"Test Accuracy: {acc:.4f} | ROC-AUC: {auc:.4f}")
    print(classification_report(y_test, y_pred))
    joblib.dump(clf, output_model_pkl)
    print(f"Saved best model to {output_model_pkl}")
