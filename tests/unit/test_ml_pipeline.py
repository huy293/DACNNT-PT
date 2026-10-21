"""Layer 1 & Layer 3 Tests: Stage 1 EDA & Stage 2 CLIP + Classifier Pipeline."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from src.features.classifier.train_classifier import (
    predict_proba_with_weights,
    run_training_pipeline,
)
from src.features.clip_extractor.extract_features import (
    MultimodalCLIPExtractor,
    build_features_csv,
)
from src.features.dataset_eda.preprocess_eda import run_dataset_eda


class TestMultimodalMLPipeline(unittest.TestCase):
    """Unit and Business Flow tests for Stage 1 and Stage 2."""

    def test_stage1_eda_report_and_corrupted_rejection(self) -> None:
        """BR-ML-01: EDA accurately counts valid samples and class balance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "eda_report.json"
            report = run_dataset_eda(output_report_path=report_path)
            self.assertTrue(report_path.exists())
            self.assertEqual(report["total_valid_samples"], 20)
            self.assertEqual(report["class_distribution"]["harmful_ads_label_1"], 10)
            self.assertEqual(report["class_distribution"]["safe_ads_label_0"], 10)
            self.assertFalse(report["class_distribution"]["is_imbalanced"])

    def test_stage2_concatenated_vector_dimension_and_l2_norm(self) -> None:
        """BR-ML-02: Concatenated [v_img || v_txt] vector has fixed dimension and unit L2 norm."""
        extractor = MultimodalCLIPExtractor()
        vec = extractor.extract_concatenated_vector(
            text="Nạp 100k nhận ngay 10 triệu tại Casino VIP!",
            image_bytes=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\x00\x00\xff",
            image_hint="banner_casino_vip.png",
        )
        self.assertEqual(len(vec), 64)
        l2_norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(l2_norm, 1.0, places=3)

    def test_stage2_edge_cases_and_malicious_payloads(self) -> None:
        """Layer 1 Google Testing: empty text, special chars, SQLi/XSS strings do not crash."""
        extractor = MultimodalCLIPExtractor()
        for text_case in ["", "   ", "<script>alert(1)</script>", "' OR 1=1 --", "../../etc/passwd"]:
            vec = extractor.extract_concatenated_vector(text=text_case, image_bytes=None)
            self.assertEqual(len(vec), 64)

    def test_stage2_classifier_meets_75_percent_accuracy_target(self) -> None:
        """BR-ML-03: Trained classifier achieves Accuracy >= 75% and saves .pkl artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            csv_path = tmp_path / "features.csv"
            pkl_path = tmp_path / "model.pkl"
            json_path = tmp_path / "weights.json"
            metrics_path = tmp_path / "metrics.json"

            build_features_csv(output_csv_path=csv_path)
            summary = run_training_pipeline(
                features_csv_path=csv_path,
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
