from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis_pipeline import AnalysisPipeline
from src.business_dashboard import BusinessDashboardService
from src.data_processor import DataProcessor
from src.feature_engineer import FeatureEngineer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_sample_raw_csv() -> str:
    rows = [
        'T23,Production, , , , ,',
        'Region/Country/Area,,Year,Series,Value,Footnotes,Source',
    ]

    afghanistan = {
        1995: (16, 17, 0, 2, 33),
        2000: (18, 14, 0, 2, 31),
        2005: (23, 22, -2, 2, 46),
        2010: (41, 99, 0, 5, 141),
        2015: (61, 111, 4, 5, 167),
    }
    albania = {
        1995: (30, -5, 1, 6, 24),
        2000: (28, -3, 0, 5, 25),
        2005: (27, -4, 1, 5, 24),
        2010: (25, -2, 0, 4, 23),
        2015: (26, -1, -1, 4, 24),
    }

    for region_code, region_name, values in [
        (4, 'Afghanistan', afghanistan),
        (8, 'Albania', albania),
    ]:
        for year, (prod, netimp, stock, percap, supply) in values.items():
            rows.extend([
                f'{region_code},{region_name},{year},Primary energy production (petajoules),{prod},,UN',
                f'{region_code},{region_name},{year},Net imports [Imports - Exports - Bunkers] (petajoules),{netimp},,UN',
                f'{region_code},{region_name},{year},Changes in stocks (petajoules),{stock},,UN',
                f'{region_code},{region_name},{year},Supply per capita (gigajoules),{percap},,UN',
                f'{region_code},{region_name},{year},Total supply (petajoules),{supply},,UN',
            ])

    return '\n'.join(rows) + '\n'


SAMPLE_RAW_CSV = build_sample_raw_csv()


class MockHttpResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def read(self) -> bytes:
        return self.text.encode('utf-8')

    def __enter__(self) -> 'MockHttpResponse':
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class DataProcessorTests(unittest.TestCase):
    @patch('src.data_processor.urlopen')
    def test_load_and_clean_returns_expected_shape(self, mock_urlopen) -> None:
        mock_urlopen.return_value = MockHttpResponse(SAMPLE_RAW_CSV)
        processor = DataProcessor('https://example.com/energy.csv')
        loaded = processor.load_data()
        cleaned = processor.clean()

        self.assertFalse(loaded.empty)
        self.assertIn('Region', loaded.columns)
        self.assertGreaterEqual(cleaned.shape[1], 7)
        self.assertIn('Total supply (petajoules)', cleaned.columns)

    @patch('src.data_processor.urlopen')
    def test_feature_engineering_creates_importer_flag(self, mock_urlopen) -> None:
        mock_urlopen.return_value = MockHttpResponse(SAMPLE_RAW_CSV)
        processor = DataProcessor('https://example.com/energy.csv')
        processor.load_data()
        cleaned = processor.clean()

        engineered = FeatureEngineer(cleaned).create_features()
        self.assertIn('is_importer', engineered.columns)
        self.assertTrue(set(engineered['is_importer'].dropna().unique()).issubset({0, 1}))


class PipelineTests(unittest.TestCase):
    @patch('src.data_processor.urlopen')
    def test_pipeline_writes_summary_report(self, mock_urlopen) -> None:
        mock_urlopen.return_value = MockHttpResponse(SAMPLE_RAW_CSV)
        output_dir = PROJECT_ROOT / 'results' / 'test-output'
        if output_dir.exists():
            shutil.rmtree(output_dir)

        pipeline = AnalysisPipeline('https://example.com/energy.csv', output_dir=output_dir, random_state=42)
        results = pipeline.run()

        summary_path = output_dir / 'analysis_summary.json'
        self.assertTrue(summary_path.exists())
        self.assertIn('hypothesis_1', results)
        self.assertIn('comparison', results['hypothesis_2'])

        shutil.rmtree(output_dir)


class DashboardServiceTests(unittest.TestCase):
    @patch('src.data_processor.urlopen')
    def test_dashboard_forecast_and_snapshot(self, mock_urlopen) -> None:
        mock_urlopen.return_value = MockHttpResponse(SAMPLE_RAW_CSV)
        service = BusinessDashboardService('https://example.com/energy.csv')
        df, columns, _ = service.load_data()
        snapshot = service.build_country_snapshot(df, columns, 'Afghanistan')
        forecast = service.forecast_country_metric(df, 'Afghanistan', 'Total Supply', columns['supply'], horizon=3)
        world = service.build_world_snapshot(df, columns)

        self.assertEqual(snapshot['country'], 'Afghanistan')
        self.assertIn('Forecast', forecast['Type'].values)
        self.assertEqual(world['countries_covered'], 2)
