import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { LandingPage } from './pages/landing/LandingPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { WaterQualityPage } from './pages/water-quality/WaterQualityPage';
import { PurificationPerformancePage } from './pages/purification-performance/PurificationPerformancePage';
import { FilterHealthPage } from './pages/filter-health/FilterHealthPage';
import { DiagnosticsPage } from './pages/diagnostics/DiagnosticsPage';
import { AlertsPage } from './pages/alerts/AlertsPage';
import { MaintenancePage } from './pages/maintenance/MaintenancePage';
import { DeviceHealthPage } from './pages/device-health/DeviceHealthPage';
import { ReadinessPage } from './pages/readiness/ReadinessPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />

      {/* Authenticated routes with layout */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/water-quality" element={<WaterQualityPage />} />
        <Route path="/purification-performance" element={<PurificationPerformancePage />} />
        <Route path="/filter-health" element={<FilterHealthPage />} />
        <Route path="/diagnostics" element={<DiagnosticsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/maintenance" element={<MaintenancePage />} />
        <Route path="/device-health" element={<DeviceHealthPage />} />
        <Route path="/readiness" element={<ReadinessPage />} />
      </Route>

      {/* Redirect unknown routes to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}