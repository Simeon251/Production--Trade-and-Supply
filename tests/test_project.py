from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from src.analysis_pipeline import AnalysisPipeline
from src.data_processor import DataProcessor
from src.feature_engineer import FeatureEngineer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "dataset" / "Production,Trade and Supply of Energy.csv"


class DataProcessorTests(unittest.TestCase):
    def test_load_and_clean_returns_expected_shape(self) -> None:
        processor = DataProcessor(DATASET_PATH)
        loaded = processor.load_data()
        cleaned = processor.clean()

        self.assertFalse(loaded.empty)
        self.assertIn("Region", loaded.columns)
        self.assertGreaterEqual(cleaned.shape[1], 7)
        self.assertIn("Total supply (petajoules)", cleaned.columns)

    def test_feature_engineering_creates_importer_flag(self) -> None:
        processor = DataProcessor(DATASET_PATH)
        processor.load_data()
        cleaned = processor.clean()

        engineered = FeatureEngineer(cleaned).create_features()
        self.assertIn("is_importer", engineered.columns)
        self.assertTrue(set(engineered["is_importer"].dropna().unique()).issubset({0, 1}))


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_summary_report(self) -> None:
        output_dir = PROJECT_ROOT / "results" / "test-output"
        if output_dir.exists():
            shutil.rmtree(output_dir)

        pipeline = AnalysisPipeline(DATASET_PATH, output_dir=output_dir, random_state=42)
        results = pipeline.run()

        summary_path = output_dir / "analysis_summary.json"
        self.assertTrue(summary_path.exists())
        self.assertIn("hypothesis_1", results)
        self.assertIn("comparison", results["hypothesis_2"])

        shutil.rmtree(output_dir)


if __name__ == "__main__":
    unittest.main()
