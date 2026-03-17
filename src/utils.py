from __future__ import annotations

from pathlib import Path
import logging

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return it as a ``Path``."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_plot(fig: plt.Figure, filepath: str | Path) -> Path:
    """Save a matplotlib figure and close it to free memory."""
    target_path = Path(filepath)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved figure to %s", target_path)
    return target_path


def plot_model_comparison(
    metrics_df: pd.DataFrame,
    title: str = "Model Comparison",
    metric_column: str = "R2 Score",
) -> plt.Figure:
    """Generate a simple bar chart for side-by-side model comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        metrics_df["Model"],
        metrics_df[metric_column],
        alpha=0.8,
        edgecolor="black",
        color="#2F5D8A",
    )
    ax.set_ylabel(metric_column)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.3f}", ha="center", va="bottom")

    fig.tight_layout()
    return fig


def create_evaluation_report(model_name: str, metrics_dict: dict[str, float], cv_mean: float | None = None, cv_std: float | None = None) -> str:
    """Build a compact plain-text performance summary for one model."""
    lines = [f"Model: {model_name}", "Test Metrics:"]
    for metric_name, value in metrics_dict.items():
        lines.append(f"  {metric_name}: {value:.4f}")
    if cv_mean is not None and cv_std is not None:
        lines.append(f"Cross-validation: {cv_mean:.4f} +/- {cv_std:.4f}")
    return "\n".join(lines)
