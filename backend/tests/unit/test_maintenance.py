"""
Tests for Maintenance and Lifecycle (Phase G4).
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.maintenance import (
    FilterCatalog,
    InstalledFilter,
    MaintenanceEvent,
    MaintenanceWorkflow,
    CalibrationRecord,
    CalibrationPolicy,
    VerificationRun,
    VerificationCheck,
    VerificationState,
    BaselineVersion,
    MaintenanceRecommendation,
    FilterCategory,
    FilterLifecycleState,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    CalibrationState,
    CompatibilityResult,
    MAINTENANCE_WORKFLOW_TRANSITIONS,
    DEFAULT_CALIBRATION_POLICIES,
)
from app.services.compatibility_engine import CompatibilityEngine, CompatibilityCheck
from app.services.maintenance_service import MaintenanceService
from app.models.maintenance import (
    FilterCatalogModel,
    InstalledFilterModel,
    MaintenanceEventModel,
    MaintenanceWorkflowModel,
    CalibrationRecordModel,
    CalibrationPolicyModel,
    VerificationRunModel,
    BaselineVersionModel,
    MaintenanceRecommendationModel,
    FilterLifecycleState,
    MaintenanceEventType,
    MaintenanceWorkflowState,
    VerificationState,
)
from app.models.device import Device as DeviceModel
from app.models.alert import Alert as AlertModel, AlertSeverity, AlertStatus


class MockDevice:
    """Mock device for testing."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get('id', uuid4())


class MockFilterCatalog:
    """Mock filter catalog for testing."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = kwargs.get('id', uuid4())
        self.filter_identifier = kwargs.get('filter_identifier', 'FILTER-001')
        self.manufacturer = kwargs.get('manufacturer', 'AquaNexis')
        self.product_name = kwargs.get('product_name', 'Test Filter')
        self.category = kwargs.get('category', FilterCategory.SEDIMENT)
        self.purifier_compatibility = kwargs.get('purifier_compatibility', ['AQUANEXIS_HOME_1'])
        self.stage_position = kwargs.get('stage_position', 1)
        self.specifications = kwargs.get('specifications', {})
        self.connector_details = kwargs.get('connector_details', 'standard')
        self.dimensions_mm = kwargs.get('dimensions_mm', {'diameter_mm': 65, 'length_mm': 240})
        self.rated_service_interval_days = kwargs.get('rated_service_interval_days', 365)
        self.rated_usage_volume_liters = kwargs.get('rated_usage_volume_liters', 10000)
        self.installation_requirements = kwargs.get('installation_requirements')
        self.maintenance_instructions = kwargs.get('maintenance_instructions')
        self.datasheet_reference = kwargs.get('datasheet_reference')
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_device():
    """Create a sample device."""
    return MockDevice(id=uuid4())


@pytest.fixture
def sample_catalog():
    """Create a sample filter catalog."""
    return MockFilterCatalog(
        id=uuid4(),
        filter_identifier='FILTER-001',
        manufacturer='AquaNexis',
        product_name='Sediment Filter 5μm',
        category=FilterCategory.SEDIMENT,
        purifier_compatibility=['AQUANEXIS_HOME_1'],
        stage_position=1,
    )


class TestCompatibilityEngine:
    """Tests for CompatibilityEngine."""

    @pytest.fixture
    def engine(self):
        return CompatibilityEngine()

    @pytest.fixture
    def catalog(self):
        return MockFilterCatalog(
            id=uuid4(),
            filter_identifier='FILTER-001',
            manufacturer='AquaNexis',
            product_name='Sediment Filter 5μm',
            category=FilterCategory.SEDIMENT,
            purifier_compatibility=['AQUANEXIS_HOME_1'],
            stage_position=1,
            dimensions_mm={'diameter_mm': 65, 'length_mm': 240},
            connector_details='standard',
        )

    def test_compatible_filter(self, engine, catalog):
        """Test compatible filter returns COMPATIBLE."""
        result = engine.check_compatibility('AQUANEXIS_HOME_1', catalog)
        
        assert result.result == CompatibilityResult.COMPATIBLE
        assert "All compatibility checks passed" in result.reasons[0]

    def test_incompatible_category(self, engine, catalog):
        """Test incompatible category returns INCOMPATIBLE."""
        catalog.category = FilterCategory.RO_MEMBRANE  # Stage 1 expects sediment
        
        result = engine.check_compatibility('AQUANEXIS_HOME_1', catalog)
        
        assert result.result == CompatibilityResult.INCOMPATIBLE
        assert any("Category mismatch" in r for r in result.reasons)

    def test_incompatible_dimensions(self, engine, catalog):
        """Test oversized filter returns INCOMPATIBLE."""
        catalog.dimensions_mm = {'diameter_mm': 80, 'length_mm': 240}  # Exceeds 70mm max
        
        result = engine.check_compatibility('AQUANEXIS_HOME_1', catalog)
        
        assert result.result == CompatibilityResult.INCOMPATIBLE
        assert any("exceeds max" in r for r in result.reasons)

    def test_incompatible_connector(self, engine, catalog):
        """Test wrong connector returns INCOMPATIBLE."""
        catalog.connector_details = 'wrong_connector'
        
        result = engine.check_compatibility('AQUANEXIS_HOME_1', catalog)
        
        assert result.result == CompatibilityResult.INCOMPATIBLE
        assert any("Connector mismatch" in r for r in result.reasons)

    def test_unknown_purifier(self, engine, catalog):
        """Test unknown purifier model returns INSUFFICIENT_INFORMATION."""
        result = engine.check_compatibility('UNKNOWN_MODEL', catalog)
        
        assert result.result == CompatibilityResult.INSUFFICIENT_INFORMATION
        assert any("Unknown purifier model" in r for r in result.reasons)

    def test_requires_review_missing_specs(self, engine, catalog):
        """Test missing dimensions returns REQUIRES_REVIEW."""
        catalog.dimensions_mm = None
        
        result = engine.check_compatibility('AQUANEXIS_HOME_1', catalog)
        
        assert result.result == CompatibilityResult.REQUIRES_REVIEW
        assert any("not provided" in r for r in result.reasons)

    def test_get_supported_purifiers(self, engine):
        """Test getting supported purifier list."""
        purifiers = engine.get_supported_purifiers()
        
        assert 'AQUANEXIS_HOME_1' in purifiers
        assert 'AQUANEXIS_PRO_2' in purifiers
        assert 'AQUANEXIS_UV_3' in purifiers


class TestMaintenanceWorkflowTransitions:
    """Tests for maintenance workflow state transitions."""

    def test_all_states_have_transitions(self):
        """Test all workflow states have transitions defined."""
        for state in MaintenanceWorkflowState:
            assert state in MAINTENANCE_WORKFLOW_TRANSITIONS

    def test_requested_transitions(self):
        """Test REQUESTED state transitions."""
        assert set(MAINTENANCE_WORKFLOW_TRANSITIONS[MaintenanceWorkflowState.REQUESTED]) == {
            MaintenanceWorkflowState.APPROVED,
            MaintenanceWorkflowState.CANCELLED,
        }

    def test_in_progress_transitions(self):
        """Test IN_PROGRESS state transitions."""
        assert set(MAINTENANCE_WORKFLOW_TRANSITIONS[MaintenanceWorkflowState.IN_PROGRESS]) == {
            MaintenanceWorkflowState.AWAITING_VERIFICATION,
            MaintenanceWorkflowState.FAILED,
            MaintenanceWorkflowState.CANCELLED,
        }

    def test_completed_is_terminal(self):
        """Test COMPLETED is terminal."""
        assert MAINTENANCE_WORKFLOW_TRANSITIONS[MaintenanceWorkflowState.COMPLETED] == []

    def test_failed_can_retry(self):
        """Test FAILED can go back to REQUESTED."""
        assert MaintenanceWorkflowState.REQUESTED in MAINTENANCE_WORKFLOW_TRANSITIONS[MaintenanceWorkflowState.FAILED]


class TestMaintenanceWorkflowStateMachine:
    """Tests for MaintenanceWorkflow state machine."""

    @pytest.mark.asyncio
    async def test_valid_transition(self):
        """Test valid state transition."""
        workflow = MaintenanceWorkflow(
            id=uuid4(),
            device_id=uuid4(),
            maintenance_event_id=uuid4(),
            state=MaintenanceWorkflowState.REQUESTED,
        )
        
        success = workflow.transition_to(MaintenanceWorkflowState.APPROVED)
        
        assert success is True
        assert workflow.state == MaintenanceWorkflowState.APPROVED

    @pytest.mark.asyncio
    async def test_invalid_transition(self):
        """Test invalid state transition fails."""
        workflow = MaintenanceWorkflow(
            id=uuid4(),
            device_id=uuid4(),
            maintenance_event_id=uuid4(),
            state=MaintenanceWorkflowState.REQUESTED,
        )
        
        success = workflow.transition_to(MaintenanceWorkflowState.COMPLETED)
        
        assert success is False
        assert workflow.state == MaintenanceWorkflowState.REQUESTED

    @pytest.mark.asyncio
    async def test_terminal_state_blocks(self):
        """Test terminal state blocks further transitions."""
        workflow = MaintenanceWorkflow(
            id=uuid4(),
            device_id=uuid4(),
            maintenance_event_id=uuid4(),
            state=MaintenanceWorkflowState.COMPLETED,
        )
        
        success = workflow.transition_to(MaintenanceWorkflowState.IN_PROGRESS)
        
        assert success is False
        assert workflow.state == MaintenanceWorkflowState.COMPLETED


class TestDefaultCalibrationPolicies:
    """Tests for default calibration policies."""

    def test_all_sensor_types_have_policies(self):
        """Test all expected sensor types have default policies."""
        expected_sensors = {'tds', 'ph', 'turbidity', 'temperature', 'flow', 'pressure', 'level'}
        assert set(DEFAULT_CALIBRATION_POLICIES.keys()) == expected_sensors

    def test_policies_have_required_fields(self):
        """Test policies have time or usage intervals."""
        for sensor_type, policy in DEFAULT_CALIBRATION_POLICIES.items():
            has_time = 'time_days' in policy
            has_usage = 'usage_measurements' in policy
            assert has_time or has_usage, f"{sensor_type} missing both time and usage intervals"


class TestFilterCatalog:
    """Tests for FilterCatalog domain model."""

    def test_catalog_creation(self):
        """Test filter catalog creation."""
        catalog = FilterCatalog(
            id=uuid4(),
            filter_identifier='FILTER-001',
            manufacturer='AquaNexis',
            product_name='Sediment Filter 5μm',
            category=FilterCategory.SEDIMENT,
            purifier_compatibility=['AQUANEXIS_HOME_1'],
            stage_position=1,
        )
        
        assert catalog.filter_identifier == 'FILTER-001'
        assert catalog.manufacturer == 'AquaNexis'
        assert catalog.category == FilterCategory.SEDIMENT

    def test_all_categories_defined(self):
        """Test all filter categories are defined."""
        categories = [c.value for c in FilterCategory]
        expected = [
            'sediment', 'pre_carbon', 'activated_carbon_block', 'ro_membrane',
            'uf_membrane', 'uv_chamber', 'uv_lamp', 'post_carbon',
            'mineral_remineralization', 'alkaline_treatment', 'other',
        ]
        assert set(categories) == set(expected)


class TestInstalledFilter:
    """Tests for InstalledFilter domain model."""

    def test_installed_filter_creation(self):
        """Test installed filter creation."""
        installed = InstalledFilter(
            id=uuid4(),
            device_id=uuid4(),
            catalog_id=uuid4(),
            stage_position=1,
            lifecycle_state=FilterLifecycleState.INSTALLED,
        )
        
        assert installed.lifecycle_state == FilterLifecycleState.INSTALLED
        assert installed.cumulative_volume_liters == 0.0
        assert installed.operating_hours == 0.0


class TestCalibrationPolicies:
    """Tests for calibration policy logic."""

    def test_time_based_due_calculation(self):
        """Test time-based due date calculation."""
        policy = DEFAULT_CALIBRATION_POLICIES['ph']
        assert policy['time_days'] == 30
        
        policy = DEFAULT_CALIBRATION_POLICIES['temperature']
        assert policy['time_days'] == 365

    def test_usage_based_due_calculation(self):
        """Test usage-based due threshold."""
        policy = DEFAULT_CALIBRATION_POLICIES['flow']
        assert policy['usage_measurements'] == 20000


class TestVerificationStateMachine:
    """Tests for verification state machine."""

    def test_verification_states(self):
        """Test all verification states are defined."""
        states = [s.value for s in VerificationState]
        assert set(states) == {'pending', 'running', 'passed', 'failed', 'incomplete'}

    def test_verification_check_creation(self):
        """Test verification check creation."""
        check = VerificationCheck(
            name="flow_rate",
            description="Flow rate within acceptable range",
            expected_range={"min": 0.5, "max": 5.0},
            actual_value=2.5,
            passed=True,
            check_type="measured",
        )
        
        assert check.passed is True
        assert check.check_type == "measured"


class TestBaselineVersioning:
    """Tests for baseline versioning logic."""

    def test_baseline_version_increment(self):
        """Test baseline version increments."""
        v1 = BaselineVersion(device_id=uuid4(), version=1)
        v2 = BaselineVersion(device_id=uuid4(), version=2)
        
        assert v2.version > v1.version

    def test_baseline_metrics_storage(self):
        """Test baseline stores metrics."""
        baseline = BaselineVersion(
            device_id=uuid4(),
            version=1,
            metrics={"flow_baseline_lpm": 2.5, "pressure_baseline_kpa": 300.0},
        )
        
        assert baseline.metrics["flow_baseline_lpm"] == 2.5
        assert baseline.metrics["pressure_baseline_kpa"] == 300.0


class TestMaintenanceRecommendations:
    """Tests for maintenance recommendation triggers."""

    def test_trigger_types(self):
        """Test all recommendation trigger types."""
        triggers = ['time_based', 'usage_based', 'health_based', 'calibration_due']
        
        for trigger in triggers:
            rec = MaintenanceRecommendation(
                device_id=uuid4(),
                trigger=trigger,
                severity='warning',
                recommended_action='Test action',
            )
            assert rec.trigger == trigger


class TestMaintenanceEventTypes:
    """Tests for maintenance event types."""

    def test_all_event_types_defined(self):
        """Test all maintenance event types are defined."""
        types = [t.value for t in MaintenanceEventType]
        expected = ['install', 'replace', 'inspect', 'clean', 'recalibrate', 'verify', 'remove']
        assert set(types) == set(expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])