from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import logging

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data_processor import DataProcessor
from .feature_engineer import FeatureEngineer
from .model_evaluator import ModelEvaluator
from .utils import ensure_directory

logger = logging.getLogger(__name__)


@dataclass
class AnalysisPipeline:
    """Run the full energy analysis workflow with reproducible holdout evaluation."""

    data_url: str | None = None
    output_dir: str | Path = "results"
    random_state: int = 42

    def load_modeling_frame(self) -> tuple[pd.DataFrame, dict[str, str], str | None]:
        """Load the dataset, clean it, and derive project features."""
        processor = DataProcessor(self.data_url)
        processor.load_data()
        wide_df = processor.clean()

        engineer = FeatureEngineer(wide_df)
        features_df = engineer.create_features()
        columns = engineer._detect_columns()
        missing = [name for name, column in columns.items() if name != "stock" and column is None]
        if missing:
            raise ValueError(f"Required project columns could not be detected: {', '.join(missing)}")

        return features_df, {key: value for key, value in columns.items() if value is not None}, processor.resolved_source_url

    def run(self) -> dict[str, Any]:
        """Execute all hypotheses and write a machine-readable summary to disk."""
        df, columns, resolved_source_url = self.load_modeling_frame()
        output_dir = ensure_directory(self.output_dir)

        results = {
            "metadata": {
                "rows": len(df),
                "columns": list(df.columns),
                "random_state": self.random_state,
                "data_url": resolved_source_url,
            },
            "hypothesis_1": self._run_h1(df, columns),
            "hypothesis_2": self._run_h2(df, columns),
            "hypothesis_3": self._run_h3(df, columns),
        }

        summary_path = output_dir / "analysis_summary.json"
        summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info("Wrote analysis summary to %s", summary_path)
        return results

    def _evaluate_regressors(self, df: pd.DataFrame, features: list[str], target: str) -> dict[str, Any]:
        dataset = df.dropna(subset=features + [target]).copy()
        X = dataset[features]
        y = dataset[target]
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=self.random_state,
        )

        candidate_models = {
            "Random Forest Regressor": RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=2,
                random_state=self.random_state,
            ),
            "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=self.random_state),
            "Linear Regression": LinearRegression(),
        }

        comparison_rows: list[dict[str, Any]] = []
        feature_importance: dict[str, Any] = {}
        for model_name, estimator in candidate_models.items():
            pipeline = Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    ("model", clone(estimator)),
                ]
            )
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            evaluator = ModelEvaluator(pipeline)
            metrics = evaluator.regression(y_test, predictions)
            cv_mean, cv_std = evaluator.cross_val(X, y, scoring="r2")
            comparison_rows.append(
                {"Model": model_name, **metrics, "CV Mean": cv_mean, "CV Std": cv_std}
            )

            importance = evaluator.get_feature_importance(features)
            if importance is not None:
                feature_importance[model_name] = importance.to_dict(orient="records")

        comparison_df = pd.DataFrame(comparison_rows).sort_values("R2 Score", ascending=False)
        best_row = comparison_df.iloc[0].to_dict()
        return {
            "features": features,
            "target": target,
            "sample_size": len(dataset),
            "best_model": best_row["Model"],
            "comparison": comparison_df.to_dict(orient="records"),
            "feature_importance": feature_importance,
        }

    def _run_h1(self, df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
        features = [columns["prod"], columns["netimp"], columns.get("stock", columns["netimp"])]
        target = columns["supply"]
        result = self._evaluate_regressors(df, features, target)
        result["decision_threshold"] = 0.8
        result["decision"] = "accept" if result["comparison"][0]["R2 Score"] >= 0.8 else "reject"
        return result

    def _run_h2(self, df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
        features = [columns["prod"], columns["netimp"], columns.get("stock", columns["netimp"]), columns["supply"]]
        target = "is_importer"
        dataset = df.dropna(subset=features + [target]).copy()
        X = dataset[features]
        y = dataset[target].astype(int)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=self.random_state,
            stratify=y,
        )

        candidate_models = {
            "Random Forest Classifier": RandomForestClassifier(
                n_estimators=300,
                min_samples_leaf=2,
                random_state=self.random_state,
            ),
            "Logistic Regression": LogisticRegression(max_iter=2000, random_state=self.random_state),
        }

        comparison_rows: list[dict[str, Any]] = []
        reports: dict[str, str] = {}
        for model_name, estimator in candidate_models.items():
            pipeline = Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    ("model", clone(estimator)),
                ]
            )
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            probabilities = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None

            evaluator = ModelEvaluator(pipeline)
            metrics = evaluator.classification(y_test, predictions, probabilities)
            cv_mean, cv_std = evaluator.cross_val(X, y, scoring="f1")
            comparison_rows.append(
                {"Model": model_name, **metrics, "F1 CV Mean": cv_mean, "F1 CV Std": cv_std}
            )
            reports[model_name] = classification_report(y_test, predictions, zero_division=0)

        comparison_df = pd.DataFrame(comparison_rows).sort_values("Accuracy", ascending=False)
        return {
            "features": features,
            "target": target,
            "sample_size": len(dataset),
            "best_model": comparison_df.iloc[0]["Model"],
            "comparison": comparison_df.to_dict(orient="records"),
            "classification_reports": reports,
            "decision_threshold": 0.85,
            "decision": "accept" if comparison_df.iloc[0]["Accuracy"] >= 0.85 else "reject",
        }

    def _run_h3(self, df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
        features = [columns["supply"], columns["prod"], columns["netimp"]]
        target = columns["percap"]
        result = self._evaluate_regressors(df, features, target)
        result["decision_threshold"] = 0.75
        result["decision"] = "accept" if result["comparison"][0]["R2 Score"] >= 0.75 else "reject"
        return result
