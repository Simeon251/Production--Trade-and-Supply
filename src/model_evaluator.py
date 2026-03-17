import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve
)
from sklearn.model_selection import cross_val_score
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Comprehensive model evaluation and comparison tool.
    
    Provides methods for:
    - Regression metrics (RMSE, MAE, R2, MAPE)
    - Classification metrics (Accuracy, Precision, Recall, F1)
    - Cross-validation evaluation
    - Feature importance extraction
    - Model comparison and visualization
    
    Attributes:
        model: Trained scikit-learn model instance
        evaluation_results (dict): Storage for evaluation metrics
    """

    def __init__(self, model):
        """
        Initialize ModelEvaluator.
        
        Args:
            model: Fitted scikit-learn model
        """
        self.model = model
        self.evaluation_results = {}
        logger.info(f"ModelEvaluator initialized with model: {type(model).__name__}")

    # ---------------------------
    # Regression evaluation
    # ---------------------------
    def regression(self, y_true, y_pred):
        """
        Compute comprehensive regression metrics.
        
        Metrics:
        - RMSE: Root Mean Squared Error (penalizes large errors more)
        - MAE: Mean Absolute Error (interpretable in original units)
        - R2: Coefficient of determination (% variance explained)
        - MAPE: Mean Absolute Percentage Error (scale-independent)
        
        Args:
            y_true (array-like): True target values
            y_pred (array-like): Predicted values
        
        Returns:
            dict: Dictionary with regression metrics
        """
        # Handle division by zero for MAPE
        non_zero_mask = y_true != 0
        if non_zero_mask.sum() > 0:
            mape = np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / 
                                   y_true[non_zero_mask])) * 100
        else:
            mape = np.nan
        
        metrics = {
            "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            "MAE": mean_absolute_error(y_true, y_pred),
            "R2 Score": r2_score(y_true, y_pred),
            "MAPE": mape
        }
        
        self.evaluation_results["regression"] = metrics
        logger.info(f"Regression metrics - R²: {metrics['R2 Score']:.4f}, RMSE: {metrics['RMSE']:.4f}")
        
        return metrics

    # ---------------------------
    # Classification evaluation
    # ---------------------------
    def classification(self, y_true, y_pred):
        """
        Compute comprehensive classification metrics.
        
        Metrics:
        - Accuracy: Overall correctness
        - Precision: True positives / predicted positives
        - Recall: True positives / actual positives
        - F1: Harmonic mean of precision and recall
        
        Args:
            y_true (array-like): True labels
            y_pred (array-like): Predicted labels
        
        Returns:
            dict: Dictionary with classification metrics
        """
        metrics = {
            "Accuracy": accuracy_score(y_true, y_pred),
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1 Score": f1_score(y_true, y_pred, zero_division=0),
        }
        
        self.evaluation_results["classification"] = metrics
        logger.info(f"Classification metrics - Accuracy: {metrics['Accuracy']:.4f}, F1: {metrics['F1 Score']:.4f}")
        
        return metrics

    # ---------------------------
    # Cross-validation
    # ---------------------------
    def cross_val(self, X, y, cv=5, scoring="r2"):
        """
        Perform k-fold cross-validation to assess model generalization.
        
        Args:
            X (array-like): Feature matrix
            y (array-like): Target variable
            cv (int): Number of folds (default: 5)
            scoring (str): Scoring metric (e.g., "r2", "accuracy", "f1")
        
        Returns:
            tuple: (mean_score, std_score) - Mean and standard deviation of CV scores
        """
        scores = cross_val_score(self.model, X, y, cv=cv, scoring=scoring)
        mean_score = scores.mean()
        std_score = scores.std()
        
        self.evaluation_results["cross_val"] = {
            "scoring": scoring,
            "cv_folds": cv,
            "mean": mean_score,
            "std": std_score,
            "all_scores": scores
        }
        
        logger.info(f"Cross-validation ({scoring}): {mean_score:.4f} ± {std_score:.4f}")
        
        return mean_score, std_score

    # ---------------------------
    # Feature importance
    # ---------------------------
    def get_feature_importance(self, feature_names=None):
        """
        Extract feature importance from tree-based and linear models.
        
        Supports:
        - Tree-based models (RandomForest, GradientBoosting)
        - Linear models (coefficients)
        
        Args:
            feature_names (list, optional): Names of features for readability
        
        Returns:
            pd.DataFrame: Features ranked by importance
            
        Raises:
            AttributeError: If model doesn't support feature importance
        """
        try:
            # Tree-based models
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                importance_type = "tree-based"
            # Linear models
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_).flatten()
                importance_type = "coefficient"
            else:
                logger.warning(f"Model {type(self.model).__name__} does not support feature importance")
                return None
            
            if feature_names is None:
                feature_names = [f"Feature_{i}" for i in range(len(importances))]
            
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            logger.info(f"Feature importance extracted ({importance_type})")
            return importance_df
            
        except Exception as e:
            logger.error(f"Error extracting feature importance: {e}")
            raise

    # ---------------------------
    # Model comparison
    # ---------------------------
    def compare_models(self, models_dict, X_test, y_test, problem_type="regression"):
        """
        Compare multiple models on the same test set.
        
        Args:
            models_dict (dict): Dictionary of {model_name: fitted_model}
            X_test (array-like): Test features
            y_test (array-like): Test target
            problem_type (str): "regression" or "classification"
        
        Returns:
            pd.DataFrame: Comparison table with metrics for each model
        """
        comparison_results = []
        
        for model_name, model in models_dict.items():
            y_pred = model.predict(X_test)
            
            if problem_type == "regression":
                metrics = self.regression(y_test, y_pred)
                comparison_results.append({
                    "Model": model_name,
                    **metrics
                })
            elif problem_type == "classification":
                metrics = self.classification(y_test, y_pred)
                comparison_results.append({
                    "Model": model_name,
                    **metrics
                })
        
        comparison_df = pd.DataFrame(comparison_results)
        logger.info(f"Model comparison complete for {len(models_dict)} models")
        
        return comparison_df

    def get_confusion_matrix(self, y_true, y_pred):
        """
        Compute confusion matrix for classification problems.
        
        Args:
            y_true (array-like): True labels
            y_pred (array-like): Predicted labels
        
        Returns:
            np.ndarray: Confusion matrix
        """
        cm = confusion_matrix(y_true, y_pred)
        logger.info(f"Confusion matrix shape: {cm.shape}")
        return cm

    def get_evaluation_summary(self):
        """
        Return all evaluation results computed so far.
        
        Returns:
            dict: Summary of all evaluation metrics
        """
        return self.evaluation_results
