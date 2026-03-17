"""
Utility functions for data analysis and visualization.

Provides helper functions for:
- Saving plots
- Performance visualization
- Summary statistics
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def save_plot(fig, filepath):
    """
    Save matplotlib figure to file.
    
    Args:
        fig: matplotlib Figure object
        filepath (str): Path to save figure (PNG recommended)
    
    Returns:
        None
    """
    try:
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Plot saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving plot: {e}")
        raise


def plot_model_comparison(metrics_df, title="Model Comparison", metric_column="R2 Score"):
    """
    Create bar plot comparing model performance.
    
    Args:
        metrics_df (pd.DataFrame): DataFrame with model names and metrics
        title (str): Plot title
        metric_column (str): Column name to plot
    
    Returns:
        matplotlib.Figure: Figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    models = metrics_df['Model']
    values = metrics_df[metric_column]
    
    bars = ax.bar(models, values, alpha=0.7, edgecolor='black', color='steelblue')
    
    ax.set_ylabel(metric_column, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim([0, 1.05])
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return fig


def print_hypothesis_summary(hypothesis_name, decision, score, threshold, problem_type="regression"):
    """
    Print formatted hypothesis decision summary.
    
    Args:
        hypothesis_name (str): Name of hypothesis
        decision (str): "ACCEPT H₁", "MARGINAL", or "REJECT H₁"
        score (float): Best model performance score
        threshold (float): Decision threshold
        problem_type (str): "regression" or "classification"
    
    Returns:
        None
    """
    metric_name = "R² Score" if problem_type == "regression" else "Accuracy"
    
    print("\n" + "=" * 70)
    print(f"HYPOTHESIS: {hypothesis_name}")
    print("=" * 70)
    print(f"\n{metric_name}: {score:.4f}")
    print(f"Threshold: {threshold:.2f}")
    print(f"Decision: {decision}")
    
    if decision == "ACCEPT H₁":
        confidence = "HIGH"
        print(f"\n✓ Confidence: {confidence}")
        print(f"  Strong evidence supports the alternative hypothesis")
    elif decision == "MARGINAL":
        confidence = "MODERATE"
        print(f"\n? Confidence: {confidence}")
        print(f"  Evidence is mixed - results near decision boundary")
    else:
        confidence = "LOW"
        print(f"\n✗ Confidence: {confidence}")
        print(f"  Insufficient evidence to reject null hypothesis")
    
    print()


def create_evaluation_report(model_name, metrics_dict, cv_mean=None, cv_std=None):
    """
    Create formatted evaluation report for a model.
    
    Args:
        model_name (str): Name of model
        metrics_dict (dict): Dictionary of metrics
        cv_mean (float, optional): Cross-validation mean score
        cv_std (float, optional): Cross-validation std dev
    
    Returns:
        str: Formatted report
    """
    report = f"\n{'Model: ' + model_name:─^50}\n"
    
    report += "\nTest Set Metrics:\n"
    for metric_name, value in metrics_dict.items():
        if isinstance(value, float):
            report += f"  {metric_name:.<30} {value:.4f}\n"
    
    if cv_mean is not None and cv_std is not None:
        report += f"\nCross-Validation:\n"
        report += f"  Mean Score:..................... {cv_mean:.4f}\n"
        report += f"  Std Deviation:.................. {cv_std:.4f}\n"
    
    return report
