import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { Menu, X, ChevronLeft, Droplet, Filter, Gauge, Waves, Mountain, Database, Shield, AlertTriangle, Wrench, Cpu, ClipboardCheck, Sun, Moon, LogOut, Bell, HelpCircle, Settings, User } from 'lucide-react';
import { useTheme } from '@state/theme';
import { cn } from '@utils/cn';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Gauge },
  { name: 'Water Quality', href: '/water-quality', icon: Droplet },
  { name: 'Purification', href: '/purification-performance', icon: Filter },
  { name: 'Filter Health', href: '/filter-health', icon: Gauge },
  { name: 'Diagnostics', href: '/diagnostics', icon: Waves },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Maintenance', href: '/maintenance', icon: Wrench },
  { name: 'Device Health', href: '/device-health', icon: Cpu },
  { name: 'Readiness', href: '/readiness', icon: ClipboardCheck },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-base flex">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 bg-surface border-r border-subtle transition-all duration-300 ease-out',
          sidebarOpen ? 'w-72' : 'w-18',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        aria-label="Main navigation"
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-info rounded-lg flex items-center justify-center">
              <Droplet className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && (
              <span className="font-semibold text-h3 text-text-primary">AquaNexis</span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-button hover:bg-hover text-text-secondary transition-colors lg:hidden"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto" aria-label="Main navigation">
          <ul className="space-y-1 px-2" role="list">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={({ isActive }) => cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-button text-body-sm transition-all duration-150',
                      isActive
                        ? 'bg-info/10 text-info font-medium'
                        : 'text-text-secondary hover:bg-hover hover:text-text-primary',
                      !sidebarOpen && 'justify-center'
                    )}
                    title={sidebarOpen ? undefined : item.name}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                    {sidebarOpen && <span className="truncate">{item.name}</span>}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom: Theme toggle, User menu */}
        <div className="p-4 border-t border-subtle space-y-2">
          <button
            onClick={toggleTheme}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-button text-body-sm text-text-secondary',
              'hover:bg-hover transition-colors',
              !sidebarOpen && 'justify-center'
            )}
            title={sidebarOpen ? undefined : theme === 'light' ? 'Dark mode' : 'Light mode'}
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            {sidebarOpen && <span>{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>}
          </button>

          <div className={cn(!sidebarOpen && 'hidden')}>
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full bg-info/10 flex items-center justify-center">
                <User className="w-5 h-5 text-info" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-body-sm font-medium text-text-primary truncate">Engineer</p>
                <p className="text-caption text-text-muted truncate">admin@aquanexis.local</p>
              </div>
            </div>
          </div>
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
      <div className={cn(
        'flex-1 flex flex-col min-w-0',
        sidebarOpen ? 'lg:ml-72' : 'lg:ml-18'
      )}>
        {/* Header */}
        <header className="sticky top-0 z-20 h-16 bg-elevated/80 backdrop-blur-sm border-b border-subtle flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-button hover:bg-hover text-text-secondary"
              aria-label="Open menu"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Device selector placeholder */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-surface rounded-button border border-subtle">
              <Database className="w-4 h-4 text-text-muted" />
              <span className="text-body-sm text-text-primary">Device-001</span>
              <ChevronLeft className="w-4 h-4 text-text-muted" />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button className="relative p-2 rounded-button hover:bg-hover text-text-secondary transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-critical rounded-full" />
            </button>

            {/* Theme toggle for mobile */}
            <button
              onClick={toggleTheme}
              className="sm:hidden p-2 rounded-button hover:bg-hover text-text-secondary transition-colors"
              aria-label={theme === 'light' ? 'Enable dark mode' : 'Enable light mode'}
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>

            {/* User menu dropdown (simplified) */}
            <div className="hidden sm:flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-info/10 flex items-center justify-center">
                <User className="w-5 h-5 text-info" />
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}