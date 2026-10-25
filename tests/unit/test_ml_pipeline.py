"""Layer 1 & Layer 3 Tests: Stage 1 EDA & Stage 2 OpenAI CLIP + Classifier Pipeline."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from src.features.classifier.train_classifier import run_training_pipeline
from src.features.clip_extractor.extract_features import (
    DEFAULT_FEATURES_CSV,
    MultimodalCLIPExtractor,
    build_features_csv,
    deobfuscate_ad_text,
)
from src.features.dataset_eda.preprocess_eda import run_dataset_eda


class TestMultimodalMLPipeline(unittest.TestCase):
    """Unit and Business Flow tests for Stage 1 and Stage 2."""

    def test_stage1_eda_report_and_corrupted_rejection(self) -> None:
        """BR-ML-01: EDA verifies all 8,560 physical PNG images via OpenCV and checks class distribution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "eda_report.json"
            report = run_dataset_eda(output_report_path=report_path)
            self.assertTrue(report_path.exists())
            self.assertEqual(report["total_valid_samples"], 8560)
            self.assertEqual(report["physical_images_verified_by_opencv"], 8560)
            self.assertEqual(report["class_distribution"]["harmful_ads_label_1"], 3049)
            self.assertEqual(report["class_distribution"]["safe_ads_label_0"], 5511)
            self.assertTrue(report["class_distribution"]["is_imbalanced"])

    def test_adversarial_text_deobfuscation(self) -> None:
        """Verify adversarial text obfuscation normalization (8.x.b.e.t, n.ổ h.ũ, L.o.r.a.m.e.n)."""
        self.assertIn(
            "8xbet nổ hũ",
            deobfuscate_ad_text("Khuyến mãi 8.x.b.e.t\u200b n.ổ h.ũ tặng 888k").lower(),
        )
        self.assertIn(
            "sunwin",
            deobfuscate_ad_text("Cổng game S-u-n-w-i-n chính thức").lower(),
        )
        self.assertIn(
            "6.000.000",
            deobfuscate_ad_text("Thưởng nạp 6.000.000 VNĐ"),
        )

    def test_stage2_concatenated_vector_dimension_and_l2_norm(self) -> None:
        """BR-ML-02: Concatenated [v_img || v_txt] vector has 1024 dims (CLIP ViT-B/32) and unit L2 norm."""
        clip_extractor = MultimodalCLIPExtractor(prefer_clip=True)
        vec_1024 = clip_extractor.extract_concatenated_vector(
            text="Nạp 100k nhận ngay 10 triệu tại Casino VIP!",
            image_hint="data/images/vn_harm_011.png",
        )
        self.assertEqual(len(vec_1024), 1024)
        l2_norm_1024 = math.sqrt(sum(v * v for v in vec_1024))
        self.assertAlmostEqual(l2_norm_1024, 1.0, places=3)

        fallback_extractor = MultimodalCLIPExtractor(prefer_clip=False)
        vec_64 = fallback_extractor.extract_concatenated_vector(
            text="Nạp 100k nhận ngay 10 triệu tại Casino VIP!",
            image_bytes=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\x00\x00\xff",
            image_hint="banner_casino_vip.png",
        )
        self.assertEqual(len(vec_64), 64)
        l2_norm_64 = math.sqrt(sum(v * v for v in vec_64))
        self.assertAlmostEqual(l2_norm_64, 1.0, places=3)

    def test_stage2_edge_cases_and_malicious_payloads(self) -> None:
        """Layer 1 Google Testing: empty text, special chars, SQLi/XSS strings do not crash."""
        extractor = MultimodalCLIPExtractor(prefer_clip=False)
        for text_case in ["", "   ", "<script>alert(1)</script>", "' OR 1=1 --", "../../etc/passwd"]:
            vec = extractor.extract_concatenated_vector(text=text_case, image_bytes=None)
            self.assertEqual(len(vec), 64)

    def test_stage2_classifier_meets_75_percent_accuracy_target(self) -> None:
        """BR-ML-03: Trained classifier achieves Accuracy >= 75% on 1024-d CLIP features and saves .pkl."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pkl_path = tmp_path / "model.pkl"
            json_path = tmp_path / "weights.json"
            metrics_path = tmp_path / "metrics.json"

            if not DEFAULT_FEATURES_CSV.exists():
                build_features_csv(output_csv_path=DEFAULT_FEATURES_CSV, prefer_clip=True)

            summary = run_training_pipeline(
                features_csv_path=DEFAULT_FEATURES_CSV,
                output_pkl_path=pkl_path,
                output_json_path=json_path,
                output_metrics_path=metrics_path,
            )

            self.assertTrue(pkl_path.exists())
            self.assertTrue(json_path.exists())
            self.assertTrue(summary["meets_stage2_target"])
            self.assertGreaterEqual(summary["validation_metrics"]["accuracy"], 0.75)


if __name__ == "__main__":
    unittest.main()
