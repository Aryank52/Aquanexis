"""
Filter Compatibility Engine - validates filter compatibility with purifier models.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.domain.maintenance import CompatibilityResult, FilterCatalog


@dataclass
class CompatibilityCheck:
    """Result of a compatibility check."""

    result: CompatibilityResult
    reasons: List[str]
    details: Dict[str, Any] = None


class CompatibilityEngine:
    """Service for validating filter compatibility with purifier models."""

    def __init__(self):
        # Known purifier models and their specifications
        # In production, this would come from a database or configuration
        self.purifier_specs = {
            "AQUANEXIS_HOME_1": {
                "stages": 5,
                "stage_specs": {
                    1: {
                        "category": "sediment",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    2: {
                        "category": "pre_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    3: {
                        "category": "activated_carbon_block",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    4: {
                        "category": "ro_membrane",
                        "max_diameter_mm": 50,
                        "max_length_mm": 300,
                        "connector": "quick_connect",
                    },
                    5: {
                        "category": "post_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                },
                "supported_manufacturers": ["AquaNexis", "Generic"],
            },
            "AQUANEXIS_PRO_2": {
                "stages": 6,
                "stage_specs": {
                    1: {
                        "category": "sediment",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    2: {
                        "category": "pre_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    3: {
                        "category": "activated_carbon_block",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    4: {
                        "category": "ro_membrane",
                        "max_diameter_mm": 50,
                        "max_length_mm": 300,
                        "connector": "quick_connect",
                    },
                    5: {
                        "category": "uf_membrane",
                        "max_diameter_mm": 50,
                        "max_length_mm": 300,
                        "connector": "quick_connect",
                    },
                    6: {
                        "category": "post_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                },
                "supported_manufacturers": ["AquaNexis", "Generic"],
            },
            "AQUANEXIS_UV_3": {
                "stages": 7,
                "stage_specs": {
                    1: {
                        "category": "sediment",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    2: {
                        "category": "pre_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    3: {
                        "category": "activated_carbon_block",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                    4: {
                        "category": "ro_membrane",
                        "max_diameter_mm": 50,
                        "max_length_mm": 300,
                        "connector": "quick_connect",
                    },
                    5: {
                        "category": "uv_lamp",
                        "max_diameter_mm": 30,
                        "max_length_mm": 400,
                        "connector": "bayonet",
                    },
                    6: {
                        "category": "uv_chamber",
                        "max_diameter_mm": 50,
                        "max_length_mm": 300,
                        "connector": "standard",
                    },
                    7: {
                        "category": "post_carbon",
                        "max_diameter_mm": 70,
                        "max_length_mm": 250,
                        "connector": "standard",
                    },
                },
                "supported_manufacturers": ["AquaNexis", "Generic"],
            },
        }

    def check_compatibility(
        self,
        purifier_model: str,
        filter_catalog: FilterCatalog,
        stage_position: Optional[int] = None,
    ) -> CompatibilityCheck:
        """
        Check if a filter is compatible with a purifier model.

        Returns CompatibilityCheck with result and reasons.
        """
        reasons = []
        details = {
            "purifier_model": purifier_model,
            "filter_id": str(filter_catalog.id),
            "filter_category": filter_catalog.category.value,
            "stage_position": stage_position,
        }

        # Check if purifier model is known
        if purifier_model not in self.purifier_specs:
            return CompatibilityCheck(
                result=CompatibilityResult.INSUFFICIENT_INFORMATION,
                reasons=[f"Unknown purifier model: {purifier_model}"],
                details=details,
            )

        purifier = self.purifier_specs[purifier_model]

        # Check manufacturer compatibility
        if filter_catalog.manufacturer not in purifier["supported_manufacturers"]:
            reasons.append(
                f"Manufacturer '{filter_catalog.manufacturer}' not in supported list: {purifier['supported_manufacturers']}"
            )

        # Determine stage to check
        check_stage = stage_position or filter_catalog.stage_position
        if check_stage <= 0:
            reasons.append("Invalid stage position (must be > 0)")

        # Check if stage exists in purifier
        if check_stage not in purifier["stage_specs"]:
            reasons.append(
                f"Stage {check_stage} does not exist in purifier model {purifier_model} (has {purifier['stages']} stages)"
            )
            return CompatibilityCheck(
                result=CompatibilityResult.INCOMPATIBLE,
                reasons=reasons,
                details=details,
            )

        stage_spec = purifier["stage_specs"][check_stage]

        # Check category match
        if filter_catalog.category.value != stage_spec["category"]:
            reasons.append(
                f"Category mismatch: filter is '{filter_catalog.category.value}', stage expects '{stage_spec['category']}'"
            )

        # Check dimensions if provided
        if filter_catalog.dimensions_mm:
            dims = filter_catalog.dimensions_mm
            if "diameter_mm" in dims and "max_diameter_mm" in stage_spec:
                if dims["diameter_mm"] > stage_spec["max_diameter_mm"]:
                    reasons.append(
                        f"Diameter {dims['diameter_mm']}mm exceeds max {stage_spec['max_diameter_mm']}mm"
                    )

            if "length_mm" in dims and "max_length_mm" in stage_spec:
                if dims["length_mm"] > stage_spec["max_length_mm"]:
                    reasons.append(
                        f"Length {dims['length_mm']}mm exceeds max {stage_spec['max_length_mm']}mm"
                    )

        # Check connector compatibility
        if filter_catalog.connector_details and "connector" in stage_spec:
            if filter_catalog.connector_details != stage_spec["connector"]:
                reasons.append(
                    f"Connector mismatch: filter has '{filter_catalog.connector_details}', stage expects '{stage_spec['connector']}'"
                )

        # Check purifier compatibility list
        if filter_catalog.purifier_compatibility:
            if purifier_model not in filter_catalog.purifier_compatibility:
                reasons.append(
                    f"Purifier model '{purifier_model}' not in filter's compatibility list"
                )

        # Determine result
        if reasons:
            return CompatibilityCheck(
                result=CompatibilityResult.INCOMPATIBLE,
                reasons=reasons,
                details=details,
            )

        # Check if there are any unknowns
        has_unknowns = (
            filter_catalog.dimensions_mm is None and "max_diameter_mm" in stage_spec
        ) or (filter_catalog.connector_details is None and "connector" in stage_spec)

        if has_unknowns:
            return CompatibilityCheck(
                result=CompatibilityResult.REQUIRES_REVIEW,
                reasons=["Some specifications not provided for full validation"],
                details=details,
            )

        return CompatibilityCheck(
            result=CompatibilityResult.COMPATIBLE,
            reasons=["All compatibility checks passed"],
            details=details,
        )

    def get_purifier_spec(self, purifier_model: str) -> Optional[Dict[str, Any]]:
        """Get purifier specifications."""
        return self.purifier_specs.get(purifier_model)

    def get_supported_purifiers(self) -> List[str]:
        """Get list of supported purifier models."""
        return list(self.purifier_specs.keys())

    def add_purifier_spec(self, model: str, spec: Dict[str, Any]) -> None:
        """Add or update a purifier specification."""
        self.purifier_specs[model] = spec
