from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging

import joblib
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split

logger = logging.getLogger(__name__)


@dataclass
class ModelTrainer:
    """Train, tune, split, and persist scikit-learn estimators safely."""

    X: Any
    y: Any
    model: Any
    best_model: Any = field(default=None, init=False)
    train_test_split_params: dict[str, Any] = field(default_factory=dict, init=False)
    split_data: tuple[Any, Any, Any, Any] | None = field(default=None, init=False)

    def split(
        self,
        test_size: float = 0.2,
        stratify: Any = None,
        random_state: int = 42,
    ) -> tuple[Any, Any, Any, Any]:
        """Create and cache a train/test split for later training."""
        split_data = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            stratify=stratify,
            random_state=random_state,
        )
        self.split_data = split_data
        X_train, X_test, y_train, y_test = split_data
        self.train_test_split_params = {
            "test_fraction": test_size,
            "random_state": random_state,
            "stratified": stratify is not None,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
        }
        logger.info("Created split with %s train rows and %s test rows", len(X_train), len(X_test))
        return split_data

    def train(self, X_train: Any = None, y_train: Any = None) -> Any:
        """Fit the model on explicit training data or the cached split training fold."""
        if X_train is None or y_train is None:
            if self.split_data is not None:
                X_train, _, y_train, _ = self.split_data
            else:
                X_train, y_train = self.X, self.y

        self.model.fit(X_train, y_train)
        logger.info("Trained model %s", type(self.model).__name__)
        return self.model

    def tune(
        self,
        param_grid: dict[str, Any],
        X_train: Any = None,
        y_train: Any = None,
        search_type: str = "grid",
        cv: int = 5,
        scoring: str | None = None,
        n_iter: int = 10,
    ) -> tuple[Any, dict[str, Any]]:
        """Run hyperparameter search on training data only."""
        if X_train is None or y_train is None:
            if self.split_data is not None:
                X_train, _, y_train, _ = self.split_data
            else:
                X_train, y_train = self.X, self.y

        estimator = clone(self.model)
        if search_type == "grid":
            search = GridSearchCV(
                estimator=estimator,
                param_grid=param_grid,
                cv=cv,
                scoring=scoring,
                n_jobs=-1,
            )
        elif search_type == "random":
            search = RandomizedSearchCV(
                estimator=estimator,
                param_distributions=param_grid,
                n_iter=n_iter,
                cv=cv,
                scoring=scoring,
                n_jobs=-1,
                random_state=42,
            )
        else:
            raise ValueError("search_type must be 'grid' or 'random'")

        search.fit(X_train, y_train)
        self.best_model = search.best_estimator_
        logger.info("Best %s search score: %.4f", search_type, search.best_score_)
        return self.best_model, search.best_params_

    def save_model(self, filepath: str | Path) -> Path:
        """Persist the current best model, or the trained base model if tuning was skipped."""
        target_path = Path(filepath)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        model_to_save = self.best_model if self.best_model is not None else self.model
        joblib.dump(model_to_save, target_path)
        logger.info("Saved model to %s", target_path)
        return target_path

    @staticmethod
    def load_model(filepath: str | Path) -> Any:
        """Load a persisted model from disk."""
        model = joblib.load(filepath)
        logger.info("Loaded model from %s", filepath)
        return model
