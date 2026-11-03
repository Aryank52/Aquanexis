"""
Controlled Membrane Degradation Dataset Generator.
Dataset Version: controlled-membrane-deg-v1.0
Provenance: CONTROLLED_EXPERIMENT
Simulates run-to-failure degradation cycles of thin-film composite (TFC) RO membranes.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

FEATURE_NAMES = [
    "fsi_score",
    "fsi_state",
    "dp_score",
    "flow_dev_score",
    "turbidity_score",
    "cum_vol_score",
    "age_score",
    "op_hours_score",
    "tds_trend_score",
    "dp",
    "flow_dev",
    "pressure_trend",
    "flow_trend",
    "rejection_rate",
    "recovery",
]


@dataclass
class DatasetMetadata:
    dataset_id: str = "controlled-membrane-deg-v1.0"
    provenance: str = "CONTROLLED_EXPERIMENT"
    description: str = (
        "Simulated run-to-failure thin-film composite RO membrane degradation experiment dataset"
    )
    sample_count: int = 600
    features: List[str] = None
    target: str = "rul_days"
    train_count: int = 480
    test_count: int = 120

    def __post_init__(self):
        if self.features is None:
            self.features = FEATURE_NAMES.copy()


def generate_controlled_degradation_dataset(
    num_samples: int = 600,
    seed: int = 42,
) -> Tuple[
    List[Dict[str, float]], List[float], List[Dict[str, float]], List[float], DatasetMetadata
]:
    """
    Generate deterministic, physics-informed controlled degradation dataset.
    Returns: (X_train, y_train, X_test, y_test, metadata)
    """
    rng = random.Random(seed)
    records: List[Tuple[Dict[str, float], float]] = []

    for i in range(num_samples):
        # Progress along life cycle (0.0 = brand new, 1.0 = completely fouled / failed)
        progress = rng.uniform(0.02, 0.98)

        # Non-linear exponential fouling acceleration in late life
        fouling_factor = math.pow(progress, 1.4)

        # Remaining useful life in days (rated life = 365 days)
        true_rul = max(0.0, (1.0 - progress) * 365.0 + rng.gauss(0, 3.5))

        # Membrane physical parameters
        age_days = progress * 365.0 + rng.gauss(0, 5)
        age_days = max(1.0, min(390.0, age_days))
        age_score = min(100.0, (age_days / 365.0) * 100.0)

        cum_vol_l = progress * 10000.0 + rng.gauss(0, 150)
        cum_vol_l = max(10.0, min(12000.0, cum_vol_l))
        cum_vol_score = min(100.0, (cum_vol_l / 10000.0) * 100.0)

        op_hours = progress * 2000.0 + rng.gauss(0, 30)
        op_hours_score = min(100.0, (op_hours / 2000.0) * 100.0)

        # Hydraulic indicators
        dp_kpa = 50.0 + fouling_factor * 180.0 + rng.gauss(0, 4.0)
        dp_score = min(100.0, max(0.0, (dp_kpa - 50.0) / 1.5))

        flow_dev_pct = -(fouling_factor * 45.0 + rng.gauss(0, 2.0))
        flow_dev_score = min(100.0, max(0.0, abs(flow_dev_pct) * 2.0))

        turbidity_score = min(100.0, max(5.0, fouling_factor * 80.0 + rng.gauss(0, 5.0)))
        tds_trend_score = min(100.0, max(0.0, fouling_factor * 60.0 + rng.gauss(0, 3.0)))

        # Composite FSI score
        fsi_score = min(
            100.0,
            max(
                0.0,
                0.25 * dp_score
                + 0.20 * flow_dev_score
                + 0.15 * turbidity_score
                + 0.15 * cum_vol_score
                + 0.10 * age_score
                + 0.08 * op_hours_score
                + 0.07 * tds_trend_score,
            ),
        )
        fsi_state = 0 if fsi_score < 35 else (1 if fsi_score < 70 else 2)

        pressure_trend = round(fouling_factor * 1.5 + rng.gauss(0, 0.1), 3)
        flow_trend = round(-(fouling_factor * 0.05 + rng.gauss(0, 0.005)), 4)

        # Purification performance
        rejection_rate = round(
            max(75.0, min(99.0, 98.0 - fouling_factor * 15.0 + rng.gauss(0, 0.5))), 1
        )
        recovery_ratio = round(
            max(40.0, min(80.0, 72.0 - fouling_factor * 20.0 + rng.gauss(0, 0.8))), 1
        )

        feature_dict = {
            "fsi_score": round(fsi_score, 2),
            "fsi_state": float(fsi_state),
            "dp_score": round(dp_score, 2),
            "flow_dev_score": round(flow_dev_score, 2),
            "turbidity_score": round(turbidity_score, 2),
            "cum_vol_score": round(cum_vol_score, 2),
            "age_score": round(age_score, 2),
            "op_hours_score": round(op_hours_score, 2),
            "tds_trend_score": round(tds_trend_score, 2),
            "dp": round(dp_kpa, 2),
            "flow_dev": round(flow_dev_pct, 2),
            "pressure_trend": pressure_trend,
            "flow_trend": flow_trend,
            "rejection_rate": rejection_rate,
            "recovery": recovery_ratio,
        }

        records.append((feature_dict, round(true_rul, 1)))

    # Deterministic split: 80% train, 20% test
    rng.shuffle(records)
    split_idx = int(num_samples * 0.8)
    train_records = records[:split_idx]
    test_records = records[split_idx:]

    X_train = [r[0] for r in train_records]
    y_train = [r[1] for r in train_records]
    X_test = [r[0] for r in test_records]
    y_test = [r[1] for r in test_records]

    meta = DatasetMetadata(
        dataset_id="controlled-membrane-deg-v1.0",
        sample_count=num_samples,
        train_count=len(train_records),
        test_count=len(test_records),
        features=FEATURE_NAMES.copy(),
    )

    return X_train, y_train, X_test, y_test, meta
