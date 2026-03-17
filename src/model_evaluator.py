from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import logging

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


@dataclass
class ModelEvaluator:
    """Evaluate fitted models and store the resulting metrics."""

    model: Any
    evaluation_results: dict[str, Any] = field(default_factory=dict, init=False)

    def _unwrap_model(self) -> Any:
        """Return the final estimator when a scikit-learn Pipeline is supplied."""
        if hasattr(self.model, "named_steps") and "model" in self.model.named_steps:
            return self.model.named_steps["model"]
        return self.model

    def regression(self, y_true: Any, y_pred: Any) -> dict[str, float]:
        """Compute standard regression metrics."""
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        non_zero_mask = y_true != 0
        mape = (
            float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
            if np.any(non_zero_mask)
            else float("nan")
        )

        metrics = {
            "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "MAE": float(mean_absolute_error(y_true, y_pred)),
            "R2 Score": float(r2_score(y_true, y_pred)),
            "MAPE": mape,
        }
        self.evaluation_results["regression"] = metrics
        return metrics

    def classification(
        self,
        y_true: Any,
        y_pred: Any,
        y_score: Any = None,
    ) -> dict[str, float]:
        """Compute common binary classification metrics."""
        metrics = {
            "Accuracy": float(accuracy_score(y_true, y_pred)),
            "Precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "Recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "F1 Score": float(f1_score(y_true, y_pred, zero_division=0)),
        }
        if y_score is not None:
            metrics["ROC AUC"] = float(roc_auc_score(y_true, y_score))

        self.evaluation_results["classification"] = metrics
        return metrics

    def cross_val(self, X: Any, y: Any, cv: int = 5, scoring: str = "r2") -> tuple[float, float]:
        """Run cross-validation for the supplied model and scoring metric."""
        scores = cross_val_score(self.model, X, y, cv=cv, scoring=scoring)
        mean_score = float(scores.mean())
        std_score = float(scores.std())
        self.evaluation_results["cross_val"] = {
            "scoring": scoring,
            "cv_folds": cv,
            "mean": mean_score,
            "std": std_score,
            "all_scores": scores,
        }
        return mean_score, std_score

    def get_feature_importance(self, feature_names: list[str] | None = None) -> pd.DataFrame | None:
        """Return feature importance for compatible models."""
        estimator = self._unwrap_model()
        if hasattr(estimator, "feature_importances_"):
            importances = np.asarray(estimator.feature_importances_)
        elif hasattr(estimator, "coef_"):
            importances = np.abs(np.asarray(estimator.coef_)).ravel()
        else:
            return None

        if feature_names is None:
            feature_names = [f"feature_{index}" for index in range(len(importances))]

        return (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

    def compare_models(self, models_dict: dict[str, Any], X_test: Any, y_test: Any, problem_type: str) -> pd.DataFrame:
        """Compare multiple fitted models against the same holdout set."""
        comparison_results: list[dict[str, Any]] = []

        for model_name, model in models_dict.items():
            y_pred = model.predict(X_test)
            if problem_type == "classification":
                row = {"Model": model_name, **self.classification(y_test, y_pred)}
            else:
                row = {"Model": model_name, **self.regression(y_test, y_pred)}
            comparison_results.append(row)

        return pd.DataFrame(comparison_results)

    @staticmethod
    def get_confusion_matrix(y_true: Any, y_pred: Any) -> Any:
        """Compute a confusion matrix for classification tasks."""
        return confusion_matrix(y_true, y_pred)

    def get_evaluation_summary(self) -> dict[str, Any]:
        """Return all metrics computed by this evaluator instance."""
        return dict(self.evaluation_results)
