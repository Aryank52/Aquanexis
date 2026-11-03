"""
RUL Multivariate Regression Model Definition.
Separated from training runner so pickle serialization uses canonical module path app.ml.model.
"""

from __future__ import annotations

import math
from typing import Dict, List, Union

from app.ml.dataset import FEATURE_NAMES


class RULMultivariateModel:
    """
    Multivariate regularized regression model with calibrated confidence intervals.
    Standardized, self-contained, no external C-extensions required.
    """

    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or FEATURE_NAMES.copy()
        self.weights: List[float] = [0.0] * len(self.feature_names)
        self.intercept: float = 0.0
        self.feature_means: List[float] = [0.0] * len(self.feature_names)
        self.feature_stds: List[float] = [1.0] * len(self.feature_names)
        self.feature_importances_: List[float] = [0.0] * len(self.feature_names)
        self.is_fitted: bool = False

    def fit(
        self,
        X: List[Dict[str, float]],
        y: List[float],
        epochs: int = 400,
        lr: float = 0.01,
        l2_reg: float = 0.001,
    ) -> Dict[str, float]:
        n_samples = len(X)
        n_features = len(self.feature_names)

        # 1. Compute means and stds for normalization
        for j, feat in enumerate(self.feature_names):
            vals = [row.get(feat, 0.0) for row in X]
            mean_j = sum(vals) / n_samples
            var_j = sum((v - mean_j) ** 2 for v in vals) / max(1, n_samples - 1)
            std_j = math.sqrt(var_j) if var_j > 1e-9 else 1.0
            self.feature_means[j] = mean_j
            self.feature_stds[j] = std_j

        # Normalize features
        norm_X = []
        for row in X:
            norm_row = [
                (row.get(feat, 0.0) - self.feature_means[j]) / self.feature_stds[j]
                for j, feat in enumerate(self.feature_names)
            ]
            norm_X.append(norm_row)

        # 2. Gradient descent with L2 penalty
        weights = [0.0] * n_features
        intercept = sum(y) / n_samples

        for epoch in range(epochs):
            grad_w = [0.0] * n_features
            grad_b = 0.0

            for i in range(n_samples):
                xi = norm_X[i]
                yi = y[i]
                y_pred = intercept + sum(weights[j] * xi[j] for j in range(n_features))
                error = y_pred - yi

                grad_b += error
                for j in range(n_features):
                    grad_w[j] += error * xi[j]

            # Update weights and intercept
            intercept -= lr * (grad_b / n_samples)
            for j in range(n_features):
                reg_term = l2_reg * weights[j]
                weights[j] -= lr * ((grad_w[j] / n_samples) + reg_term)

        self.weights = weights
        self.intercept = intercept
        self.is_fitted = True

        # Compute normalized feature importances
        abs_weights = [abs(w) for w in self.weights]
        total_abs = sum(abs_weights) or 1.0
        self.feature_importances_ = [round(w / total_abs, 4) for w in abs_weights]

        preds = self._predict_norm(norm_X)
        mae = sum(abs(p - actual) for p, actual in zip(preds, y)) / n_samples
        rmse = math.sqrt(sum((p - actual) ** 2 for p, actual in zip(preds, y)) / n_samples)

        return {"train_mae": round(mae, 2), "train_rmse": round(rmse, 2)}

    def _predict_norm(self, norm_X: List[List[float]]) -> List[float]:
        preds = []
        for row in norm_X:
            val = self.intercept + sum(w * x for w, x in zip(self.weights, row))
            preds.append(max(0.0, val))
        return preds

    def predict(
        self, X: Union[Dict[str, float], List[List[float]], List[Dict[str, float]], List[float]]
    ) -> List[float]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted")

        if not X:
            return []

        if isinstance(X, dict):
            X = [X]
        elif isinstance(X[0], (int, float)):
            X = [X]

        norm_X = []
        for item in X:
            if isinstance(item, dict):
                norm_row = [
                    (item.get(feat, 0.0) - self.feature_means[j]) / self.feature_stds[j]
                    for j, feat in enumerate(self.feature_names)
                ]
            elif isinstance(item, (list, tuple)):
                norm_row = [
                    (item[j] - self.feature_means[j]) / self.feature_stds[j]
                    if j < len(item)
                    else 0.0
                    for j in range(len(self.feature_names))
                ]
            else:
                norm_row = [0.0] * len(self.feature_names)
            norm_X.append(norm_row)

        return self._predict_norm(norm_X)
