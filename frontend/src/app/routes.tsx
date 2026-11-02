// ============================================================================
// AquaNexis Routes — Lazy-loaded with auth guards
// ============================================================================
import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { PageSkeleton } from '@/components/ui/PageSkeleton';

// Lazy-load heavy routes for fast first paint
const LandingPage = lazy(() => import('@/pages/landing/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('@/pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const SessionExpiredPage = lazy(() => import('@/pages/auth/SessionExpiredPage').then(m => ({ default: m.SessionExpiredPage })));
const LockedSessionPage = lazy(() => import('@/pages/auth/LockedSessionPage').then(m => ({ default: m.LockedSessionPage })));
const AccessDeniedPage = lazy(() => import('@/pages/auth/AccessDeniedPage').then(m => ({ default: m.AccessDeniedPage })));
const DeviceOnboardingPage = lazy(() => import('@/pages/onboarding/DeviceOnboardingPage').then(m => ({ default: m.DeviceOnboardingPage })));

const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage').then(m => ({ default: m.DashboardPage })));
const WaterQualityPage = lazy(() => import('@/pages/water-quality/WaterQualityPage').then(m => ({ default: m.WaterQualityPage })));
const PurificationPerformancePage = lazy(() => import('@/pages/purification-performance/PurificationPerformancePage').then(m => ({ default: m.PurificationPerformancePage })));
const FilterHealthPage = lazy(() => import('@/pages/filter-health/FilterHealthPage').then(m => ({ default: m.FilterHealthPage })));
const DiagnosticsPage = lazy(() => import('@/pages/diagnostics/DiagnosticsPage').then(m => ({ default: m.DiagnosticsPage })));
const AlertsPage = lazy(() => import('@/pages/alerts/AlertsPage').then(m => ({ default: m.AlertsPage })));
const MaintenancePage = lazy(() => import('@/pages/maintenance/MaintenancePage').then(m => ({ default: m.MaintenancePage })));
const DeviceHealthPage = lazy(() => import('@/pages/device-health/DeviceHealthPage').then(m => ({ default: m.DeviceHealthPage })));
const ReadinessPage = lazy(() => import('@/pages/readiness/ReadinessPage').then(m => ({ default: m.ReadinessPage })));

// Protected route wrapper — imported lazily since auth pages exist
const ProtectedRoute = lazy(() => import('@/components/auth/ProtectedRoute').then(m => ({ default: m.ProtectedRoute })));

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageSkeleton />}>{children}</Suspense>;
}

export function AppRoutes() {
  return (
    <SuspenseWrapper>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/session-expired" element={<SessionExpiredPage />} />
        <Route path="/locked" element={<LockedSessionPage />} />
        <Route path="/access-denied" element={<AccessDeniedPage />} />

        {/* Protected routes with layout */}
        <Route element={<ProtectedRoute />}>
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
            <Route path="/onboarding" element={<DeviceOnboardingPage />} />
          </Route>
        </Route>

        {/* Redirect unknown routes */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </SuspenseWrapper>
  );
}
