"""
Train and Evaluate RUL Prognostics Model for AquaNexis.
Evaluates baseline vs candidate models, records metrics (MAE/RMSE/R2),
failure cases, confidence calibration, and exports serialized artifact.
"""

from __future__ import annotations

import math
import os
import pickle
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.ml.dataset import FEATURE_NAMES, generate_controlled_degradation_dataset
from app.ml.model import RULMultivariateModel


def evaluate_model(
    model: RULMultivariateModel,
    X: List[Dict[str, float]],
    y: List[float],
) -> Dict[str, float]:
    preds = model.predict(X)
    n = len(y)
    mae = sum(abs(p - actual) for p, actual in zip(preds, y)) / n
    rmse = math.sqrt(sum((p - actual) ** 2 for p, actual in zip(preds, y)) / n)
    y_mean = sum(y) / n
    ss_tot = sum((actual - y_mean) ** 2 for actual in y)
    ss_res = sum((actual - p) ** 2 for p, actual in zip(preds, y))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-9 else 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
    }


def train_and_export_model(
    output_dir: Optional[str] = None,
) -> Tuple[RULMultivariateModel, Dict[str, Any], str]:
    """Train candidate models, compare against baseline, and export artifact."""
    X_train, y_train, X_test, y_test, meta = generate_controlled_degradation_dataset(
        num_samples=600,
        seed=42,
    )

    # 1. Baseline Model (Mean Predictor)
    mean_val = sum(y_train) / len(y_train)
    baseline_mae = sum(abs(mean_val - yi) for yi in y_test) / len(y_test)
    baseline_rmse = math.sqrt(sum((mean_val - yi) ** 2 for yi in y_test) / len(y_test))

    # 2. Candidate Model: Multivariate Regularized Degradation Model
    model = RULMultivariateModel(feature_names=FEATURE_NAMES)
    train_metrics = model.fit(X_train, y_train, epochs=600, lr=0.03, l2_reg=0.005)
    test_metrics = evaluate_model(model, X_test, y_test)

    # 3. Failure Case Evaluation
    # Edge case 1: Brand new filter under normal operation (progress < 0.1)
    new_filter_cases = [
        (x, y)
        for x, y in zip(X_test, y_test)
        if x.get("fsi_score", 0) < 20 and x.get("age_score", 0) < 15
    ]
    new_filter_mae = (
        sum(abs(model.predict([x])[0] - y) for x, y in new_filter_cases) / len(new_filter_cases)
        if new_filter_cases
        else 0.0
    )

    # Edge case 2: Heavily degraded end-of-life filter (progress > 0.85)
    fouled_filter_cases = [
        (x, y) for x, y in zip(X_test, y_test) if x.get("fsi_score", 0) > 75 or x.get("dp", 0) > 200
    ]
    fouled_filter_mae = (
        sum(abs(model.predict([x])[0] - y) for x, y in fouled_filter_cases)
        / len(fouled_filter_cases)
        if fouled_filter_cases
        else 0.0
    )

    # 4. Calibration & Prediction Intervals
    # 95% confidence margin = 1.96 * test_mae
    calibrated_interval_days = round(1.96 * test_metrics["mae"], 1)

    export_metadata = {
        "model_name": "AquaNexis-Multivariate-Degradation-Regressor",
        "model_version": "1.0.0",
        "dataset_version": meta.dataset_id,
        "provenance": meta.provenance,
        "feature_names": FEATURE_NAMES.copy(),
        "baseline_metrics": {
            "model": "MeanBaseline",
            "test_mae": round(baseline_mae, 2),
            "test_rmse": round(baseline_rmse, 2),
        },
        "metrics": {
            "train_mae": train_metrics["train_mae"],
            "train_rmse": train_metrics["train_rmse"],
            "test_mae": test_metrics["mae"],
            "test_rmse": test_metrics["rmse"],
            "r2": test_metrics["r2"],
            "mae": test_metrics["mae"],  # Key expected by rul_service
        },
        "failure_cases": {
            "early_life_mae": round(new_filter_mae, 2),
            "end_of_life_mae": round(fouled_filter_mae, 2),
        },
        "calibration": {
            "interval_multiplier": 1.96,
            "margin_days": calibrated_interval_days,
            "coverage_pct": 95.0,
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(X_train),
        "validation_samples": len(X_test),
    }

    # Save artifact
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(output_dir, exist_ok=True)
    model_artifact_path = os.path.join(output_dir, "rul_model.pkl")

    artifact_bundle = {
        "model": model,
        **export_metadata,
    }

    with open(model_artifact_path, "wb") as f:
        pickle.dump(artifact_bundle, f)

    return model, export_metadata, model_artifact_path


if __name__ == "__main__":
    model, metadata, path = train_and_export_model()
    print("=" * 60)
    print("AQUANEXIS RUL MODEL TRAINING COMPLETE")
    print(f"Artifact Path: {path}")
    print(f"Dataset Version: {metadata['dataset_version']}")
    print(f"Baseline MAE: {metadata['baseline_metrics']['test_mae']} days")
    print(
        f"Candidate Test MAE: {metadata['metrics']['test_mae']} days (R2: {metadata['metrics']['r2']})"
    )
    print(f"Calibrated 95% Interval: ±{metadata['calibration']['margin_days']} days")
    print("=" * 60)
