import { Link } from 'react-router-dom';
import {
  Droplet,
  Filter,
  Gauge,
  Shield,
  ArrowRight,
  CheckCircle,
  BarChart2,
  Zap,
  Database,
  Wrench,
} from 'lucide-react';
import { cn } from '@utils/cn';

const features = [
  {
    icon: Droplet,
    title: 'Multi-Parameter Sensing',
    description:
      'Beyond TDS: pH, turbidity, temperature, flow, pressure, tank level, leak detection, and pump energy monitoring.',
  },
  {
    icon: Filter,
    title: 'Filter Intelligence',
    description:
      'Filter Stress Index (FSI), Filter Health Index (FHI), and Remaining Useful Life (RUL) predictions with explainable AI.',
  },
  {
    icon: Gauge,
    title: 'AquaScore Water Quality',
    description:
      'Real-time 0-100 water quality score from weighted WHO/EPA guideline compliance across all parameters.',
  },
  {
    icon: Shield,
    title: 'Safety-First Diagnostics',
    description:
      'Leak, overpressure, dry-run, and overcurrent protection with validated actions and full audit trail.',
  },
  {
    icon: BarChart2,
    title: 'Trend Analysis & Anomalies',
    description:
      'Statistical anomaly detection (z-score, IQR, rate-of-change) with historical trend visualization.',
  },
  {
    icon: Wrench,
    title: 'Maintenance Workflows',
    description:
      'Guided filter replacement, sensor calibration, and post-maintenance verification with automated quality checks.',
  },
];

const specs = [
  { label: 'Sensors Supported', value: '9+ Level-1 Parameters' },
  { label: 'Data Retention', value: '2 Years Raw / 5 Years Aggregated' },
  { label: 'Alert Precision', value: '> 90% (Target)' },
  { label: 'RUL Accuracy', value: 'MAE < 14 Days (Target)' },
  { label: 'Dashboard Load', value: '< 2s First Paint' },
  { label: 'API Latency', value: '< 200ms p99' },
];

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-base">
      {/* Hero Section */}
      <section className="relative flex flex-1 items-center justify-center overflow-hidden px-6 py-20">
        {/* Background pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-info/5 via-transparent to-transparent" />

        <div className="relative mx-auto w-full max-w-6xl text-center">
          {/* Product visualization */}
          <div className="mb-12 animate-fade-in">
            <SystemVisualization />
          </div>

          {/* Title & Value Proposition */}
          <h1 className="text-text-primary mb-6 animate-slide-up text-display font-semibold">
            AquaNexis
          </h1>
          <p
            className="mx-auto mb-10 max-w-2xl animate-slide-up text-body-lg text-text-secondary"
            style={{ animationDelay: '100ms' }}
          >
            Predictive Water Intelligence Platform — Sense → Validate → Understand → Detect →
            Predict → Alert → Protect → Assist
          </p>

          {/* CTAs */}
          <div
            className="flex animate-slide-up flex-col items-center justify-center gap-4 sm:flex-row"
            style={{ animationDelay: '200ms' }}
          >
            <Link
              to="/dashboard"
              className={cn('btn btn-primary btn-lg w-full sm:w-auto', 'group')}
            >
              Open Live System
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link to="/filter-health" className={cn('btn btn-secondary btn-lg w-full sm:w-auto')}>
              Filter Intelligence
            </Link>
          </div>

          {/* Trust indicators */}
          <div
            className="mt-16 flex animate-fade-in flex-wrap items-center justify-center gap-8 text-caption text-text-muted"
            style={{ animationDelay: '300ms' }}
          >
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-success" />
              WCAG 2.1 AA Accessible
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-success" />
              OpenAPI Documented
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-success" />
              TypeScript Strict
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-success" />
              Test Coverage {'>'} 80%
            </span>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-subtle border-y bg-surface px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <header className="mb-16 text-center">
            <h2 className="text-text-primary mb-4 text-h1 font-semibold">Core Capabilities</h2>
            <p className="mx-auto max-w-2xl text-body-lg text-text-secondary">
              Every component designed for engineering-grade reliability and transparency
            </p>
          </header>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <article
                key={feature.title}
                className={cn(
                  'card p-6 transition-all duration-300 hover:shadow-card-hover',
                  'animate-slide-up'
                )}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-info/10">
                  <feature.icon className="h-6 w-6 text-info" />
                </div>
                <h3 className="text-text-primary mb-2 text-h3 font-semibold">{feature.title}</h3>
                <p className="text-body text-text-secondary">{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Specs Section */}
      <section className="bg-base px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <header className="mb-16 text-center">
            <h2 className="text-text-primary mb-4 text-h1 font-semibold">Engineering Targets</h2>
            <p className="mx-auto max-w-2xl text-body-lg text-text-secondary">
              Measurable goals that define product quality
            </p>
          </header>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            {specs.map((spec, index) => (
              <div
                key={spec.label}
                className={cn(
                  'card hover:border-emphasis p-5 text-center transition-colors',
                  'animate-fade-in'
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <p className="text-text-primary mb-1 text-data-lg font-bold">{spec.value}</p>
                <p className="text-caption text-text-secondary">{spec.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-subtle border-t bg-surface px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-caption text-text-secondary">
            AquaNexis — Predictive Water Intelligence
          </p>
          <div className="flex items-center gap-6 text-caption text-text-muted">
            <Link to="/documentation" className="hover:text-text-primary transition-colors">
              Documentation
            </Link>
            <Link to="/documentation" className="hover:text-text-primary transition-colors">
              GitHub
            </Link>
            <Link to="/documentation" className="hover:text-text-primary transition-colors">
              Privacy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

// System Visualization Component
function SystemVisualization() {
  const nodes = [
    { id: 'source', label: 'Source Water', x: 50, y: 50, icon: Droplet },
    { id: 'sensor', label: 'Multi-Sensor', x: 200, y: 50, icon: Gauge },
    { id: 'filter', label: 'Purification', x: 350, y: 50, icon: Filter },
    { id: 'tank', label: 'Storage', x: 500, y: 50, icon: Database },
    { id: 'tap', label: 'Point of Use', x: 650, y: 50, icon: Droplet },
  ];

  const connections = [
    { from: 'source', to: 'sensor' },
    { from: 'sensor', to: 'filter' },
    { from: 'filter', to: 'tank' },
    { from: 'tank', to: 'tap' },
  ];

  return (
    <div className="relative mx-auto h-32 w-full max-w-4xl">
      {/* Flow lines */}
      <svg
        className="pointer-events-none absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2"
        aria-hidden="true"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="currentColor" />
          </marker>
        </defs>
        {connections.map((conn, i) => {
          const from = nodes.find(n => n.id === conn.from)!;
          const to = nodes.find(n => n.id === conn.to)!;
          return (
            <line
              key={i}
              x1={from.x + 40}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="currentColor"
              strokeWidth="2"
              strokeDasharray="8 4"
              markerEnd="url(#arrowhead)"
              className="animate-dash text-info/30"
              style={{ animationDelay: `${i * 200}ms` }}
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {nodes.map(node => (
        <div
          key={node.id}
          className="absolute flex flex-col items-center gap-2 transition-all duration-300"
          style={{ left: node.x, top: node.y, transform: 'translateX(-50%)' }}
        >
          <div
            className={cn(
              'flex h-16 w-16 items-center justify-center rounded-xl shadow-card',
              'border-subtle border-2 bg-surface'
            )}
          >
            <node.icon className="h-8 w-8 text-info" />
          </div>
          <span className="whitespace-nowrap text-caption font-medium text-text-secondary">
            {node.label}
          </span>
        </div>
      ))}

      {/* Intelligence layer overlay */}
      <div className="absolute bottom-0 left-1/2 flex -translate-x-1/2 gap-4">
        {[
          { icon: BarChart2, label: 'Analyze' },
          { icon: Zap, label: 'Predict' },
          { icon: Shield, label: 'Protect' },
        ].map((item, i) => (
          <div
            key={item.label}
            className={cn(
              'flex flex-col items-center gap-1 rounded-button bg-surface/80 px-3 py-2 backdrop-blur-sm',
              'border-subtle animate-slide-up border shadow-card'
            )}
            style={{ animationDelay: `${300 + i * 100}ms` }}
          >
            <item.icon className="h-5 w-5 text-info" />
            <span className="text-caption text-text-secondary">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
