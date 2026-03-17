from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
import joblib
import logging

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Encapsulates model training and hyperparameter tuning functionality.
    
    Provides methods for:
    - Splitting data into training and testing sets
    - Training models with fit validation
    - Hyperparameter tuning using GridSearchCV/RandomizedSearchCV
    - Model persistence (saving/loading)
    
    Attributes:
        X (array-like): Feature matrix
        y (array-like): Target variable
        model: Scikit-learn model instance
        best_model: Best model from hyperparameter tuning
        train_test_split_params (dict): Parameters used for data splitting
    """

    def __init__(self, X, y, model):
        """
        Initialize ModelTrainer.
        
        Args:
            X (array-like): Feature matrix
            y (array-like): Target variable
            model: Unfitted scikit-learn model instance
        """
        self.X = X
        self.y = y
        self.model = model
        self.best_model = None
        self.train_test_split_params = {}
        logger.info(f"ModelTrainer initialized with model: {type(model).__name__}")

    def split(self, test_size=0.2, stratify=None, random_state=42):
        """
        Split data into training and testing sets.
        
        Args:
            test_size (float): Proportion of data for testing (default: 0.2)
            stratify (array-like, optional): Array for stratified splitting.
                Use for classification to maintain class distribution.
            random_state (int): Random seed for reproducibility
        
        Returns:
            tuple: (X_train, X_test, y_train, y_test)
            
        Note:
            Stratified splits ensure both train/test maintain original class distribution.
            Essential for imbalanced classification problems.
        """
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y,
            test_size=test_size,
            stratify=stratify,
            random_state=random_state
        )
        
        self.train_test_split_params = {
            "test_size": test_size,
            "stratified": stratify is not None,
            "random_state": random_state,
            "train_size": len(X_train),
            "test_size_actual": len(X_test)
        }
        
        logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test (stratified: {stratify is not None})")
        
        return X_train, X_test, y_train, y_test

    def train(self):
        """
        Train the model on the full dataset (X, y).
        
        This trains on all available data. For proper evaluation,
        call split() first and train on training set separately
        if using this for cross-validation.
        
        Returns:
            Fitted model instance
        """
        try:
            self.model.fit(self.X, self.y)
            logger.info(f"Model trained successfully: {type(self.model).__name__}")
            return self.model
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    def tune(self, param_grid, X_train=None, y_train=None, search_type="grid", cv=5, scoring=None):
        """
        Perform hyperparameter tuning using GridSearchCV or RandomizedSearchCV.
        
        Args:
            param_grid (dict): Hyperparameter grid to search
            X_train (array-like, optional): Training features. If None, uses self.X
            y_train (array-like, optional): Training target. If None, uses self.y
            search_type (str): "grid" for GridSearchCV, "random" for RandomizedSearchCV
            cv (int): Number of cross-validation folds (default: 5)
            scoring (str): Scoring metric (e.g., "accuracy", "r2", "f1")
        
        Returns:
            tuple: (best_model, best_params) - Tuned model and optimal hyperparameters
        """
        X = X_train if X_train is not None else self.X
        y = y_train if y_train is not None else self.y
        
        if search_type == "grid":
            search = GridSearchCV(
                estimator=self.model,
                param_grid=param_grid,
                cv=cv,
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
            logger.info(f"Starting GridSearchCV with {len(param_grid)} parameter combinations")
        elif search_type == "random":
            search = RandomizedSearchCV(
                estimator=self.model,
                param_distributions=param_grid,
                n_iter=10,
                cv=cv,
                scoring=scoring,
                n_jobs=-1,
                random_state=42,
                verbose=1
            )
            logger.info(f"Starting RandomizedSearchCV with 10 iterations")
        else:
            raise ValueError("search_type must be 'grid' or 'random'")
        
        search.fit(X, y)
        self.best_model = search.best_estimator_
        
        logger.info(f"Best CV score: {search.best_score_:.4f}")
        logger.info(f"Best parameters: {search.best_params_}")
        
        return self.best_model, search.best_params_

    def save_model(self, filepath):
        """
        Save the trained model to disk using joblib.
        
        Args:
            filepath (str): Path to save the model file
        """
        if self.best_model is None:
            model_to_save = self.model
        else:
            model_to_save = self.best_model
        
        joblib.dump(model_to_save, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """
        Load a saved model from disk.
        
        Args:
            filepath (str): Path to the saved model file
            
        Returns:
            Loaded model instance
        """
        model = joblib.load(filepath)
        logger.info(f"Model loaded from {filepath}")
        return model
