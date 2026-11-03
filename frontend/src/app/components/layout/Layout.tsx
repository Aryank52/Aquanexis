// ============================================================================
// AquaNexis Layout — Sidebar + Header with real device status
// ============================================================================
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Menu,
  X,
  ChevronLeft,
  Droplet,
  Filter,
  Gauge,
  Waves,
  Mountain,
  Database,
  Shield,
  AlertTriangle,
  Wrench,
  Cpu,
  ClipboardCheck,
  Sun,
  Moon,
  LogOut,
  Bell,
  User,
  Wifi,
  WifiOff,
  ChevronDown,
  Send,
  Settings,
  Package,
} from 'lucide-react';
import { useTheme } from '@/state/theme';
import { useAuth } from '@/state/auth';
import { apiClient } from '@/api/client';
import { cn } from '@/utils/cn';
import type { DeviceStatus } from '@/types/api';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Gauge },
  { name: 'Water Quality', href: '/water-quality', icon: Droplet },
  { name: 'Purification', href: '/purification-performance', icon: Filter },
  { name: 'Filter Health', href: '/filter-health', icon: Gauge },
  { name: 'Diagnostics', href: '/diagnostics', icon: Waves },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Maintenance', href: '/maintenance', icon: Wrench },
  { name: 'Notifications', href: '/notifications', icon: Send },
  { name: 'Calibration', href: '/calibration', icon: Settings },
  { name: 'Verification', href: '/verification', icon: ClipboardCheck },
  { name: 'Filter Catalog', href: '/filters', icon: Package },
  { name: 'Device Health', href: '/device-health', icon: Cpu },
  { name: 'Readiness', href: '/readiness', icon: ClipboardCheck },
];

const deviceStatusConfig: Record<
  DeviceStatus,
  { label: string; color: string; icon: typeof Wifi }
> = {
  online: { label: 'Online', color: 'text-success bg-success/10', icon: Wifi },
  degraded: { label: 'Degraded', color: 'text-warning bg-warning/10', icon: Wifi },
  offline: { label: 'Offline', color: 'text-text-muted bg-text-muted/10', icon: WifiOff },
  maintenance: { label: 'Maintenance', color: 'text-info bg-info/10', icon: Wrench },
  error: { label: 'Error', color: 'text-critical bg-critical/10', icon: AlertTriangle },
};

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const location = useLocation();
  const queryClient = useQueryClient();

  const demoStatus = useQuery({
    queryKey: ['demoStatus'],
    queryFn: () =>
      apiClient
        .get<{ demo_mode: boolean; active_scenario: string; device_status?: DeviceStatus }>(
          '/demo/status'
        )
        .then(r => r.data),
    refetchInterval: 5000,
    retry: false,
  });

  const switchScenario = useMutation({
    mutationFn: (scenario: string) =>
      apiClient.post('/demo/scenario', { scenario }).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });

  const deviceStatus: DeviceStatus = demoStatus.data?.device_status ?? 'online';
  const statusConfig = deviceStatusConfig[deviceStatus] ?? deviceStatusConfig.online;
  const StatusIcon = statusConfig.icon;
  const activeScenario = demoStatus.data?.active_scenario ?? 'NORMAL';

  return (
    <div className="flex min-h-screen bg-base">
      {/* Sidebar */}
      <aside
        className={cn(
          'border-subtle fixed inset-y-0 left-0 z-40 border-r bg-surface transition-all duration-300 ease-out',
          sidebarOpen ? 'w-72' : 'w-18',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        aria-label="Main navigation"
      >
        {/* Logo */}
        <div className="border-subtle flex h-16 items-center justify-between border-b px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-info">
              <Droplet className="h-5 w-5 text-white" />
            </div>
            {sidebarOpen && (
              <span className="text-text-primary text-h3 font-semibold">AquaNexis</span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden rounded-button p-2 text-text-secondary transition-colors hover:bg-hover lg:block"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <ChevronLeft
              className={cn('h-5 w-5 transition-transform', !sidebarOpen && 'rotate-180')}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4" aria-label="Main navigation">
          <ul className="space-y-1 px-2" role="list">
            {navigation.map(item => {
              const Icon = item.icon;
              return (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-button px-3 py-2.5 text-body-sm transition-colors duration-150',
                        isActive
                          ? 'bg-info/10 font-medium text-info'
                          : 'hover:text-text-primary text-text-secondary hover:bg-hover',
                        !sidebarOpen && 'justify-center'
                      )
                    }
                    title={sidebarOpen ? undefined : item.name}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                    {sidebarOpen && <span className="truncate">{item.name}</span>}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom: Theme toggle, User */}
        <div className="border-subtle space-y-2 border-t p-4">
          <button
            onClick={toggleTheme}
            className={cn(
              'flex w-full items-center gap-3 rounded-button px-3 py-2 text-body-sm text-text-secondary',
              'transition-colors hover:bg-hover',
              !sidebarOpen && 'justify-center'
            )}
            title={sidebarOpen ? undefined : theme === 'light' ? 'Dark mode' : 'Light mode'}
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            {sidebarOpen && <span>{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>}
          </button>

          {sidebarOpen && user && (
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-info/10">
                <User className="h-5 w-5 text-info" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-text-primary truncate text-body-sm font-medium">
                  {user.display_name}
                </p>
                <p className="truncate text-caption text-text-muted">{user.role}</p>
              </div>
              <button
                onClick={logout}
                className="hover:text-text-primary rounded-button p-1.5 text-text-muted transition-colors hover:bg-hover"
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main content */}
      <div
        className={cn(
          'flex min-w-0 flex-1 flex-col transition-all duration-300',
          sidebarOpen ? 'lg:ml-72' : 'lg:ml-18'
        )}
      >
        {/* Header */}
        <header className="border-subtle sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-elevated/80 px-6 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="rounded-button p-2 text-text-secondary hover:bg-hover lg:hidden"
              aria-label="Open navigation menu"
            >
              <Menu className="h-6 w-6" />
            </button>

            {/* Device selector + status */}
            <div className="border-subtle hidden items-center gap-2 rounded-button border bg-surface px-3 py-1.5 sm:flex">
              <Database className="h-4 w-4 text-text-muted" />
              <span className="text-text-primary text-body-sm">Kitchen RO System</span>
              <span
                className={cn(
                  'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-caption font-medium',
                  statusConfig.color
                )}
              >
                <StatusIcon className="h-3 w-3" />
                {statusConfig.label}
              </span>
            </div>

            {/* Demo Mode Scenario Switcher */}
            {demoStatus.data?.demo_mode && (
              <div className="border-subtle hidden items-center gap-1.5 rounded-button border bg-surface px-2.5 py-1 md:flex">
                <span className="rounded bg-warning/15 px-1.5 py-0.5 text-caption font-semibold text-warning">
                  DEMO_MODE (SIMULATED)
                </span>
                {(['NORMAL', 'FILTER_STRESS', 'LEAK', 'SENSOR_FAULT'] as const).map(scen => (
                  <button
                    key={scen}
                    type="button"
                    disabled={switchScenario.isPending}
                    onClick={() => switchScenario.mutate(scen)}
                    className={cn(
                      'rounded px-2 py-0.5 font-mono text-caption transition-colors',
                      activeScenario === scen
                        ? scen === 'LEAK'
                          ? 'bg-critical font-semibold text-white'
                          : scen === 'FILTER_STRESS' || scen === 'SENSOR_FAULT'
                            ? 'bg-warning font-semibold text-black'
                            : 'bg-info font-semibold text-white'
                        : 'text-text-secondary hover:bg-hover'
                    )}
                  >
                    {scen}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button
              className="relative rounded-button p-2 text-text-secondary transition-colors hover:bg-hover"
              aria-label="View notifications"
            >
              <Bell className="h-5 w-5" />
              <span
                className="absolute right-1 top-1 h-2 w-2 rounded-full bg-critical"
                aria-hidden="true"
              />
            </button>

            {/* Theme toggle for mobile */}
            <button
              onClick={toggleTheme}
              className="rounded-button p-2 text-text-secondary transition-colors hover:bg-hover sm:hidden"
              aria-label={theme === 'light' ? 'Enable dark mode' : 'Enable light mode'}
            >
              {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </button>

            {/* User avatar */}
            <div className="hidden items-center gap-2 sm:flex">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-info/10">
                <User className="h-5 w-5 text-info" />
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6 lg:p-8" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
