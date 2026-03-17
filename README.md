# Production, Trade and Supply of Energy - Predictive Modeling Analysis

**Course:** 04-638: Programming for Data Analytics  
**Assignment:** Analytics Assignment II: Predictive Modeling and Hypothesis Testing  
**Due:** 24th November, 2025

## 📋 Project Overview

This project applies supervised machine learning to test three key hypotheses about global energy systems using UN energy production, trade, and supply data. The analysis combines exploratory data analysis insights with predictive modeling to understand energy dynamics across countries and years.

## 🎯 Research Hypotheses

### Hypothesis 1: Energy Supply Prediction (Regression)
**Question:** Can primary energy production, net imports, and stock changes accurately predict total energy supply?

- **H₀ (Null):** These variables are not significantly predictive of total supply (R² < 0.5)
- **H₁ (Alternative):** These variables significantly predict total supply (R² ≥ 0.8)
- **Problem Type:** Regression
- **Target Variable:** Total energy supply
- **Features:** Primary energy production, Net imports, Changes in stocks

**Rationale:** Understanding energy balances is critical for predicting national energy availability and identifying supply vulnerabilities.

---

### Hypothesis 2: Importer Classification (Classification)
**Question:** Can we classify countries as importers vs exporters based on energy characteristics?

- **H₀ (Null):** Classification accuracy < 0.75
- **H₁ (Alternative):** Classification accuracy ≥ 0.85
- **Problem Type:** Classification
- **Target Variable:** is_importer (binary: 1=importer, 0=exporter)
- **Features:** Primary energy production, Net imports, Changes in stocks, Total supply

**Rationale:** Identifying importer/exporter status helps understand global trade dependencies and energy security vulnerabilities.

---

### Hypothesis 3: Per-Capita Consumption Prediction (Regression)
**Question:** Does total supply combined with production/import patterns predict per-capita energy consumption?

- **H₀ (Null):** Model R² < 0.6
- **H₁ (Alternative):** Model R² ≥ 0.75
- **Problem Type:** Regression
- **Target Variable:** Energy supply per capita
- **Features:** Total supply, Primary energy production, Net imports

**Rationale:** Per-capita consumption indicates development level and reveals consumption disparities between nations.

---

## 📁 Project Structure

```
Production, Trade and Supply/
│
├── src/                              # Python modules (OOP implementation)
│   ├── __init__.py
│   ├── data_processor.py            # DataProcessor class - data loading & cleaning
│   ├── feature_engineer.py          # FeatureEngineer class - feature creation
│   ├── model_trainer.py             # ModelTrainer class - model training & tuning
│   ├── model_evaluator.py           # ModelEvaluator class - evaluation & comparison
│   └── utils.py                     # Helper functions (if needed)
│
├── notebooks/
│   └── main_analysis.ipynb          # Main workflow notebook
│
├── dataset/
│   └── Production,Trade and Supply of Energy.csv
│
├── results/
│   ├── figures/                     # Generated visualizations
│   └── models/                      # Saved model files
│
├── README.md                        # This file
└── requirements.txt                 # Python dependencies
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- pip or conda

### Steps

1. **Navigate to project directory**
   ```bash
   cd "Production, Trade and Supply"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -c "import pandas, sklearn, numpy; print('✓ All dependencies installed')"
   ```

---

## 🚀 Running the Analysis

### Option 1: Jupyter Notebook (Recommended)
```bash
jupyter notebook notebooks/main_analysis.ipynb
```

The notebook includes:
- Data loading and cleaning
- Feature engineering with documentation
- Three complete hypothesis tests
- Model training and evaluation (3+ models per hypothesis)
- Comparison visualizations
- Hypothesis decisions with statistical evidence

### Option 2: Command Line
```bash
python -c "
from src.data_processor import DataProcessor
from src.feature_engineer import FeatureEngineer

dp = DataProcessor('dataset/Production,Trade and Supply of Energy.csv')
df = dp.load_data()
df_clean = dp.clean()
print('Data loaded and cleaned successfully')
"
```

---

## 📊 Module Documentation

### `DataProcessor` Class
**Purpose:** Loads, cleans, and transforms raw energy data

**Key Methods:**
- `load_data()` - Load CSV and standardize columns
- `clean()` - Type conversion, missing value handling, pivoting to wide format
- `get_processed_data()` - Retrieve processed dataframe
- `get_summary_stats()` - Data quality statistics

---

### `FeatureEngineer` Class
**Purpose:** Creates and transforms features for modeling

**Key Methods:**
- `create_features()` - Generate engineered features (is_importer, log transforms)
- `scale_numeric()` - Standardize numeric columns using StandardScaler
- `get_feature_report()` - Documentation of all feature engineering steps

**Features Created:**
1. **is_importer:** Binary indicator (1 if net imports > 0, else 0)
2. **Log Transformations:** Safe log(1+x) for production, imports, supply (reduces skew)

---

### `ModelTrainer` Class
**Purpose:** Trains models with stratified splitting and hyperparameter tuning

**Key Methods:**
- `split()` - Train-test split with stratification support for balanced classes
- `train()` - Fit model on full dataset
- `tune()` - GridSearchCV/RandomizedSearchCV for hyperparameter optimization
- `save_model()` - Persist model to disk
- `load_model()` - Load saved model

---

### `ModelEvaluator` Class
**Purpose:** Comprehensive model evaluation and comparison

**Key Methods:**
- `regression()` - R², RMSE, MAE, MAPE metrics
- `classification()` - Accuracy, Precision, Recall, F1 Score
- `cross_val()` - K-fold cross-validation (configurable scoring metric)
- `get_feature_importance()` - Feature importance for tree/linear models
- `compare_models()` - Compare multiple models on same test set
- `get_confusion_matrix()` - Classification confusion matrix
- `get_evaluation_summary()` - All computed metrics

---

## 📈 Models Implemented

### For Hypothesis 1 & 3 (Regression):
1. **Random Forest Regressor** - Ensemble method, non-linear, feature importance
2. **Gradient Boosting Regressor** - Sequential boosting, often superior performance
3. **Linear Regression** - Baseline for interpretability

### For Hypothesis 2 (Classification):
1. **Random Forest Classifier** - Ensemble classifier, handles imbalance well
2. **Logistic Regression** - Linear classifier baseline, probabilistic

---

## 📊 Expected Results

The analysis evaluates each model on:
- Test set performance
- Cross-validation scores (5-fold)
- Feature importance rankings

Hypothesis decisions are based on:
- **H1:** Target R² ≥ 0.8 (strong predictability of energy supply)
- **H2:** Target Accuracy ≥ 0.85 (high confidence in importer classification)
- **H3:** Target R² ≥ 0.75 (good predictability of per-capita consumption)

---

## 🎓 Code Quality Standards

### PEP 8 Compliance:
- ✓ 4-space indentation
- ✓ Descriptive variable names
- ✓ Line length considerations

### Documentation:
- ✓ Comprehensive class docstrings
- ✓ Method docstrings with Args/Returns/Raises
- ✓ Inline comments for complex logic

### OOP Principles:
- ✓ Single Responsibility Principle
- ✓ Encapsulation
- ✓ Clear separation of concerns
- ✓ Reusable, composable classes

---

## 📚 Dependencies

See `requirements.txt` for exact versions. Key packages:
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **scikit-learn** - Machine learning algorithms
- **matplotlib/seaborn** - Visualization
- **jupyter** - Notebook environment

---

## 🚦 Quick Start Example

```python
from src.data_processor import DataProcessor
from src.feature_engineer import FeatureEngineer
from src.model_trainer import ModelTrainer
from src.model_evaluator import ModelEvaluator
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# 1. Load and clean data
dp = DataProcessor("dataset/Production,Trade and Supply of Energy.csv")
df = dp.load_data()
df = dp.clean()

# 2. Engineer features
fe = FeatureEngineer(df)
df = fe.create_features()

# 3. Prepare for modeling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
y = df['Total supply']

# 4. Train and evaluate
trainer = ModelTrainer(X_scaled, y, RandomForestRegressor(random_state=42))
X_train, X_test, y_train, y_test = trainer.split()
model = trainer.train()

# 5. Evaluate
evaluator = ModelEvaluator(model)
metrics = evaluator.regression(y_test, model.predict(X_test))
cv_mean, cv_std = evaluator.cross_val(X_scaled, y)

print(f"R² Score: {metrics['R2 Score']:.4f}")
print(f"Cross-validation: {cv_mean:.4f} ± {cv_std:.4f}")
```

---

## 📝 Assignment Checklist

- [x] 3 clear, testable hypotheses with null/alternative
- [x] Data cleaning and feature engineering with documentation
- [x] 3+ supervised learning models with tuning
- [x] Appropriate metrics for regression and classification
- [x] Cross-validation evaluation
- [x] Feature importance analysis
- [x] Model comparison tables/visualizations
- [x] Hypothesis testing results with evidence
- [x] OOP implementation (4 required classes)
- [x] PEP 8 compliant code
- [x] Comprehensive docstrings
- [x] README documentation

---

**Last Updated:** November 21, 2025
