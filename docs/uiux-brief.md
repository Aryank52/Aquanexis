# AquaNexis — UI/UX Design Brief

## 1. Design Philosophy

**Engineering-Grade Clarity** — Every pixel serves understanding. No decoration. Data density with breathing room. Trust through precision.

### Core Principles
| Principle | Application |
|-----------|-------------|
| **Hierarchy First** | AquaScore > Filter Health > System State > Details |
| **Restrained Color** | Semantic only (green/amber/red for state), neutral grays otherwise |
| **Compact Density** | Information-dense cards, 8px base grid, no wasted space |
| **Strong Typography** | Inter/Mono for data, clear scale (32/24/18/14/12px) |
| **Accessible States** | Color + icon + label for every status, WCAG AA contrast |
| **Purposeful Motion** | Only for state transitions, incoming alerts, value changes |

## 2. Color System

### 2.1 Semantic Colors (Only Colors with Meaning)
```css
:root {
  /* Status - ONLY use for state communication */
  --color-success: #059669;      /* Emerald 600 - GOOD, healthy, resolved */
  --color-warning: #d97706;      /* Amber 600 - WARNING, attention needed */
  --color-critical: #dc2626;     /* Red 600 - CRITICAL, immediate action */
  --color-info: #2563eb;         /* Blue 600 - INFO, neutral information */
  
  /* Backgrounds - Neutral hierarchy */
  --bg-base: #ffffff;            /* Page background */
  --bg-surface: #f8fafc;         /* Card/surface (slate 50) */
  --bg-elevated: #ffffff;        /* Modals, dropdowns */
  --bg-hover: #f1f5f9;           /* Hover states (slate 100) */
  --bg-active: #e2e8f0;          /* Active/pressed (slate 200) */
  
  /* Borders */
  --border-subtle: #e2e8f0;      /* Default borders (slate 200) */
  --border-emphasis: #94a3b8;    /* Focus, emphasis (slate 400) */
  
  /* Text */
  --text-primary: #0f172a;       /* Slate 900 - Primary text */
  --text-secondary: #475569;     /* Slate 600 - Secondary text */
  --text-muted: #94a3b8;         /* Slate 400 - Placeholders, disabled */
  --text-inverse: #ffffff;       /* On dark backgrounds */
  
  /* Data Visualization - Categorical (colorblind safe) */
  --chart-1: #0ea5e9;   /* Sky 500 - TDS/Primary */
  --chart-2: #22c55e;   /* Green 500 - pH/Health */
  --chart-3: #f59e0b;   /* Amber 500 - Turbidity/Warning */
  --chart-4: #ef4444;   /* Red 500 - Temperature/Critical */
  --chart-5: #8b5cf6;   /* Violet 500 - Flow */
  --chart-6: #ec4899;   /* Pink 500 - Pressure */
  --chart-7: #06b6d4;   /* Cyan 500 - Tank */
  --chart-8: #84cc16;   /* Lime 500 - Pump */
  
  /* Gauge Bands */
  --gauge-good: #059669;      /* 70-100 */
  --gauge-warn: #d97706;      /* 40-69 */
  --gauge-crit: #dc2626;      /* 0-39 */
}

/* Dark mode (opt-in) */
[data-theme="dark"] {
  --bg-base: #020617;          /* Slate 950 */
  --bg-surface: #0f172a;       /* Slate 900 */
  --bg-elevated: #1e293b;      /* Slate 800 */
  --bg-hover: #1e293b;
  --bg-active: #334155;
  --border-subtle: #1e293b;
  --border-emphasis: #475569;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
}
```

### 2.2 Usage Rules
- **Never** use semantic colors for decoration
- **Never** use red/green for anything except state
- Charts use categorical palette; gauges use semantic bands
- Text on colored backgrounds must meet 4.5:1 contrast

## 3. Typography

### 3.1 Font Stack
```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  --font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

### 3.2 Type Scale
| Token | Size | Weight | Line Height | Use Case |
|-------|------|--------|-------------|----------|
| `--text-display` | 48px / 3rem | 600 | 1.1 | Landing hero |
| `--text-h1` | 32px / 2rem | 600 | 1.2 | Page titles |
| `--text-h2` | 24px / 1.5rem | 600 | 1.3 | Section headers |
| `--text-h3` | 20px / 1.25rem | 600 | 1.3 | Card titles |
| `--text-body-lg` | 18px / 1.125rem | 400 | 1.5 | Body emphasis |
| `--text-body` | 16px / 1rem | 400 | 1.5 | Default body |
| `--text-body-sm` | 14px / 0.875rem | 400 | 1.5 | Dense info |
| `--text-caption` | 12px / 0.75rem | 500 | 1.4 | Labels, badges |
| `--text-data` | 16px / 1rem | 500 | 1.2 | **Mono** - Sensor values |
| `--text-data-lg` | 32px / 2rem | 600 | 1.1 | **Mono** - Gauge values |
| `--text-data-xl` | 48px / 3rem | 700 | 1.0 | **Mono** - Hero metrics |

## 4. Spacing & Layout

### 4.1 Spacing Scale (8px Base)
```css
:root {
  --space-1: 4px;   /* 0.25rem */
  --space-2: 8px;   /* 0.5rem  - Base unit */
  --space-3: 12px;  /* 0.75rem */
  --space-4: 16px;  /* 1rem    - Card padding */
  --space-5: 20px;  /* 1.25rem */
  --space-6: 24px;  /* 1.5rem  - Section gap */
  --space-8: 32px;  /* 2rem    - Page padding */
  --space-10: 40px; /* 2.5rem */
  --space-12: 48px; /* 3rem */
  --space-16: 64px; /* 4rem */
}
```

### 4.2 Layout Grid
- **Container max-width**: 1440px (dashboard), 1200px (content pages)
- **Sidebar**: 280px fixed (collapsible to 72px icon-only)
- **Header**: 64px fixed
- **Card border-radius**: 12px
- **Button border-radius**: 8px
- **Input border-radius**: 8px

### 4.3 Breakpoints
```css
:root {
  --bp-sm: 640px;   /* Mobile landscape */
  --bp-md: 768px;   /* Tablet */
  --bp-lg: 1024px;  /* Desktop */
  --bp-xl: 1280px;  /* Wide desktop */
  --bp-2xl: 1536px; /* Ultra-wide */
}
```

## 5. Component Library

### 5.1 Primitive Components (`components/ui/`)

#### Button
```tsx
// Variants: primary, secondary, ghost, danger, success
// Sizes: sm (32px), md (40px), lg (48px)
// States: default, hover, active, disabled, loading
<Button variant="primary" size="md">Replace Filter</Button>
<Button variant="ghost" size="sm" icon={<ChevronLeft />}>Back</Button>
<Button variant="danger" loading>Executing...</Button>
```

#### Card
```tsx
// Elevation: flat (border), raised (shadow), outlined
<Card className="p-4">
  <CardHeader>
    <CardTitle>Filter Health</CardTitle>
    <CardSubtitle>Last updated 3 min ago</CardSubtitle>
  </CardHeader>
  <CardContent>...</CardContent>
  <CardFooter>...</CardFooter>
</Card>
```

#### Badge
```tsx
// Variants: default, success, warning, critical, info, outline
<Badge variant="success">GOOD</Badge>
<Badge variant="warning">SUSPECT</Badge>
<Badge variant="critical">CRITICAL</Badge>
<Badge variant="info">CALIBRATING</Badge>
```

#### SensorValueCard
```tsx
// Specialized for dashboard sensor grid
<SensorValueCard
  label="TDS"
  value={45.2}
  unit="ppm"
  quality="GOOD"
  trend={-2.1}
  freshness={3}
/>
```

#### Gauge (Circular)
```tsx
// AquaScore, FSI, FHI, RUL
<Gauge
  value={92}
  max={100}
  size={160}
  strokeWidth={12}
  bands={[
    { min: 0, max: 39, color: 'var(--gauge-crit)' },
    { min: 40, max: 69, color: 'var(--gauge-warn)' },
    { min: 70, max: 100, color: 'var(--gauge-good)' }
  ]}
  label="AquaScore"
  showValue
  animate={true}
/>
```

#### StatusBadge (System State)
```tsx
<StatusBadge state="healthy" pulse={false}>SYSTEM HEALTHY</StatusBadge>
<StatusBadge state="degraded" pulse={true}>DEGRADED</StatusBadge>
<StatusBadge state="critical" pulse={true}>CRITICAL</StatusBadge>
```

### 5.2 Composite Components

#### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Header (64px) - Logo, Device Selector, User, Notifications  │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  Sidebar     │  Main Content                                │
│  (280px)     │  ┌────────────────────────────────────────┐  │
│              │  │ AquaScore Gauge    │ Filter Health     │  │
│  - Dashboard │  │ (320px)            │ Card (320px)      │  │
│  - Water Q.  │  ├────────────────────────────────────────┤  │
│  - Perform.  │  │ System State  │ Active Alert Banner   │  │
│  - Filter H. │  │ Badge         │ (if any)              │  │
│  - Diagnost. │  ├────────────────────────────────────────┤  │
│  - Alerts    │  │ Sensor Grid (9 x SensorValueCard)     │  │
│  - Maint.    │  │                                              │  │
│  - Device H. │  │ Key Trend Sparkline                     │  │
│  - Readiness │  └────────────────────────────────────────┘  │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

#### Active Alert Banner
```tsx
// Appears at top of dashboard when critical/warning alert active
<AlertBanner
  alert={activeAlert}
  onAcknowledge={handleAcknowledge}
  onDismiss={handleDismiss}
  pulse={alert.severity === 'CRITICAL'}
/>
// Animation: slide down + pulse (critical only)
// Auto-dismiss after acknowledge, or manual dismiss
```

#### Trend Sparkline
```tsx
// Small inline chart for dashboard
<Sparkline
  data={trendPoints}
  color="var(--chart-1)"
  showArea
  height={48}
  width={200}
/>
```

#### AlertTimeline
```tsx
// Vertical timeline showing state transitions
<AlertTimeline
  alerts={alerts}
  onAcknowledge={handleAcknowledge}
  onResolve={handleResolve}
/>
// Each row: timestamp, type badge, severity dot, message, state, actions
```

#### MaintenanceWizard
```tsx
// Stepper with validation
<MaintenanceWizard
  type="filter_replacement"
  steps={[
    { id: 'confirm', title: 'Confirm Replacement', component: ConfirmStep },
    { id: 'serial', title: 'New Filter Serial', component: SerialStep },
    { id: 'verify', title: 'Verification', component: VerificationStep },
    { id: 'complete', title: 'Complete', component: CompleteStep }
  ]}
  onComplete={handleComplete}
/>
// Progress bar at top, previous/next navigation, skip optional steps
```

#### ReadinessChecklist
```tsx
// Engineering board - not a project board
<ReadinessChecklist
  checks={[
    { id: 'device', label: 'Device Connected', status: 'pass', detail: 'Last seen 3s ago' },
    { id: 'sensors', label: 'Sensors Ready', status: 'pass', detail: '9/9 GOOD' },
    { id: 'calibration', label: 'Calibration Current', status: 'warn', detail: 'pH due in 3 days' },
    { id: 'freshness', label: 'Data Fresh', status: 'pass', detail: '3 seconds' },
    { id: 'backend', label: 'Backend Healthy', status: 'pass', detail: 'All services up' },
    { id: 'database', label: 'Database Healthy', status: 'pass', detail: 'Primary + replica' },
    { id: 'models', label: 'Models Ready', status: 'pass', detail: 'v1.2.0 loaded' },
    { id: 'alerts', label: 'Alert System Ready', status: 'pass', detail: 'Channels configured' },
    { id: 'safety', label: 'Safety System Ready', status: 'pass', detail: 'Valves responsive' },
    { id: 'tests', label: 'Last Test Passed', status: 'pass', detail: '2026-10-30 02:00' },
  ]}
/>
// Each row: icon (check/warning/x), label, status badge, detail text
// Overall readiness badge at top
```

## 6. Page Specifications

### 6.1 Landing Page (Public)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│        [System Visualization - Static SVG]                  │
│        (Clean vector: water drop → filter → tap)            │
│                                                             │
│        AquaNexis                                            │
│        Predictive Water Intelligence                        │
│                                                             │
│        [Open Live System]        [Filter Intelligence]      │
│           Primary CTA              Secondary CTA             │
│                                                             │
│        Trusted by engineers. Built for reliability.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
- No hero video, no carousel
- Static SVG system diagram (responsive, animated on scroll)
- Two CTAs only
- Footer: docs, github, privacy

### 6.2 Dashboard Page (Authenticated)
As shown in Layout above. Key behaviors:
- WebSocket connected → live updates (values fade transition 300ms)
- AquaScore gauge animates on value change (600ms ease-out)
- Alert banner slides down (300ms), pulses if critical
- Sensor cards show quality badge (GOOD/SUSPECT/BAD)
- Freshness indicator: green dot < 10s, amber 10-60s, red > 60s
- Keyboard navigable, screen reader announces critical changes

### 6.3 Water Quality Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Water Quality                    [Export CSV]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ TDS Score    │ │ pH Score     │ │ Turbidity    │        │
│  │ 94/100       │ │ 98/100       │ │ 87/100       │        │
│  │ 45 ppm       │ │ 7.2          │ │ 0.3 NTU      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Trend Chart: 1h | 24h | 7d | 30d  [Dropdown]         │   │
│  │ (Multi-line: TDS, pH, Turbidity, Temp)               │   │
│  │ Downsampled, hover for values, legend toggle         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Anomaly Timeline                                      │   │
│  │ 2026-10-31 10:15 - TDS spike (z-score 3.2)           │   │
│  │ 2026-10-30 22:40 - pH drift (rate 0.15/hr)           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Filter Health Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Filter Intelligence              [Model Info]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ FSI Gauge    │ │ FHI Gauge    │ │ RUL Chart        │    │
│  │ 23/100       │ │ 87/100       │ │ 145 days         │    │
│  │ LOW STRESS   │ │ GOOD HEALTH  │ │ [80 - 210] 95% CI│    │
│  └──────────────┘ └──────────────┘ └──────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Explanation Panel                                     │   │
│  │ Top Contributing Factors:                             │   │
│  │ 1. Feed TDS (+35%) ──────────────────▶ Increases FSI │   │
│  │ 2. Operating Pressure (+12%) ───────▶ Increases FSI  │   │
│  │ 3. Runtime (+200h) ─────────────────▶ Increases FSI  │   │
│  │ 4. Cleaning Cycles (2) ─────────────▶ Decreases FSI  │   │
│  │                                                       │   │
│  │ Model: baseline_v1 | Dataset: 2026-10-15 | MAE: 11d  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ RUL History (30d) - Line chart with confidence band  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  [Replace Filter]  (Primary CTA if FHI < 40)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 Diagnostics Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: System Diagnostics                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐ ┌─────────────────────────────┐   │
│  │ Pressure Panel      │ │ Flow Panel                  │   │
│  │ Current: 350 kPa    │ │ Current: 1.2 L/min          │   │
│  │ Trend 1h: +5 kPa    │ │ Trend 1h: -0.05 L/min       │   │
│  │ Fouling: 0.12       │ │ Recovery: 83%               │   │
│  │ [Chart: 24h]        │ │ [Chart: 24h]                │   │
│  └─────────────────────┘ └─────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────┐ ┌─────────────────────────────┐   │
│  │ Leak Panel          │ │ Tank Panel                  │   │
│  │ Status: DRY         │ │ Level: 78%                  │   │
│  │ Probability: 0.01   │ │ Fill Rate: 1.1 L/min        │   │
│  │ Sensor: OK          │ │ Stagnation: 2.3h            │   │
│  │ [Chart: 24h]        │ │ [Chart: 24h]                │   │
│  └─────────────────────┘ └─────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Pump Energy Panel                                    │   │
│  │ Current: 0.85A | Power: 195W | Efficiency: -2.1%/wk │   │
│  │ Runtime: 2,847h | Starts: 1,203                     │   │
│  │ [Chart: 7d]                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.6 Alerts Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Alerts                    [Filter: All ▼] [Export]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Active Alerts (3)                                    │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🔴 CRITICAL  leak_detected        2 min ago        │   │
│  │    Leak confirmed via sensor + flow delta           │   │
│  │    [Acknowledge] [View Details]                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🟡 WARNING   filter_health_critical  1 hour ago    │   │
│  │    FHI 18, RUL 5 days                              │   │
│  │    [Acknowledge] [View Details]                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🔵 INFO      calibration_due         2 days ago    │   │
│  │    pH sensor calibration overdue by 3 days         │   │
│  │    [Acknowledge] [View Details]                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Alert History (click row for timeline)              │   │
│  ├──────┬──────────┬──────────┬──────────┬────────────┤   │
│  │ Time │ Type     │ Severity │ State    │ Action     │   │
│  ├──────┼──────────┼──────────┼──────────┼────────────┤   │
│  │ 10:15│ leak     │ CRITICAL │ RESOLVED │ View       │   │
│  │ 09:30│ fhi_low  │ WARNING  │ RESOLVED │ View       │   │
│  │ ...  │ ...      │ ...      │ ...      │ ...        │   │
│  └──────┴──────────┴──────────┴──────────┴────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.7 Maintenance Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Maintenance                              [+ New]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Quick Actions                                        │   │
│  │ [Replace Filter] [Calibrate Sensor] [Verify System]  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Maintenance History                                  │   │
│  ├──────────┬────────────┬──────────┬────────┬─────────┤   │
│  │ Date     │ Type       │ By       │ Verified│ Details │   │
│  ├──────────┼────────────┼──────────┼────────┼─────────┤   │
│  │ 10/28    │ Filter Rep │ J. Smith │ ✓      │ View    │   │
│  │ 10/15    │ Calibration│ M. Chen  │ ✓      │ View    │   │
│  │ 10/01    │ Verification│ System  │ ✓      │ View    │   │
│  └──────────┴────────────┴──────────┴────────┴─────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.8 Device Health Page
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Device Health                  [Firmware: 2.1.4]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Sensor Health Grid                                  │   │
│  ├──────────┬────────┬────────┬────────┬──────────────┤   │
│  │ Sensor   │ Value    │ Quality  │ Calibration   │     │
│  ├──────────┼────────┼────────┼────────┼──────────────┤   │
│  │ TDS      │ 45.2 ppm │ 🟢 GOOD  │ 2026-10-15    │     │
│  │ pH       │ 7.1      │ 🟡 SUSPECT│ 2026-09-20 ⚠ │     │
│  │ Turbidity│ 0.3 NTU  │ 🟢 GOOD  │ 2026-10-10    │     │
│  │ Temp     │ 23.5°C   │ 🟢 GOOD  │ Factory       │     │
│  │ Flow     │ 1.2 L/m  │ 🟢 GOOD  │ 2026-10-01    │     │
│  │ Pressure │ 350 kPa  │ 🟢 GOOD  │ 2026-10-01    │     │
│  │ Tank     │ 78%      │ 🟢 GOOD  │ 2026-10-01    │     │
│  │ Leak     │ Dry      │ 🟢 GOOD  │ N/A           │     │
│  │ Pump I   │ 0.85A    │ 🟢 GOOD  │ 2026-10-01    │     │
│  └──────────┴────────┴────────┴────────┴──────────────┘   │
│                                                             │
│  ┌──────────────────┐ ┌────────────────────────────────┐   │
│  │ Firmware         │ │ Connectivity                   │   │
│  │ Version: 2.1.4   │ │ WiFi: -42 dBm (Excellent)      │   │
│  │ Latest: 2.1.5    │ │ Last Ping: 3s ago              │   │
│  │ [Update Available]│ │ Uptime: 14d 6h                │   │
│  └──────────────────┘ └────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.9 Readiness Page (Engineering Board)
```
┌─────────────────────────────────────────────────────────────┐
│ Header: System Readiness                    [Run Tests]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall: READY  🟢 (10/10 checks passing)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Readiness Checklist                                 │   │
│  ├──────────────────────────┬────────┬────────────────┤   │
│  │ Device Connected         │ 🟢 PASS │ Last seen 3s   │   │
│  │ Sensors Ready (9/9)      │ 🟢 PASS │ All GOOD       │   │
│  │ Calibration Current      │ 🟡 WARN │ pH due in 3d   │   │
│  │ Data Fresh (<10s)        │ 🟢 PASS │ 3 seconds      │   │
│  │ Backend Healthy          │ 🟢 PASS │ All services   │   │
│  │ Database Healthy         │ 🟢 PASS │ Primary + repl │   │
│  │ Models Ready             │ 🟢 PASS │ v1.2.0 loaded  │   │
│  │ Alert System Ready       │ 🟢 PASS │ Email+Webhook  │   │
│  │ Safety System Ready      │ 🟢 PASS │ Valves respond │   │
│  │ Last Test Suite Passed   │ 🟢 PASS │ 2026-10-30     │   │
│  └──────────────────────────┴────────┴────────────────┘   │
│                                                             │
│  [Run Full Diagnostic]  [View Test Results]                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 7. Motion & Animation

### 7.1 Approved Animations (Only These)
| Trigger | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Page transition | Fade + slide up | 200ms | ease-out |
| Gauge value change | Arc sweep | 600ms | ease-out |
| Sensor value update | Number count + color fade | 300ms | ease-out |
| Alert banner appear | Slide down + fade | 300ms | ease-out |
| Alert banner pulse (critical) | Scale 1.0 → 1.02 | 1000ms | infinite, ease-in-out |
| Panel expand/collapse | Height + fade | 250ms | ease-out |
| Tab switch | Cross-fade | 150ms | ease-out |
| Toast/notification | Slide in from right | 250ms | ease-out |
| Button press | Scale 0.98 | 100ms | ease-out |
| Loading skeleton | Pulse shimmer | 1500ms | infinite |

### 7.2 Forbidden Animations
- Parallax, particle effects, background videos
- Decorative hover transforms on static elements
- Auto-playing carousels
- Page load spinners (use skeletons instead)
- Any animation without functional purpose

## 8. Responsive Behavior

### 8.1 Dashboard Breakpoints
| Breakpoint | Sidebar | Sensor Grid | Gauges |
|------------|---------|-------------|--------|
| ≥ 1280px | Full (280px) | 3×3 (9 cards) | Side by side |
| 1024-1279px | Collapsed (72px) | 3×3 | Stacked |
| 768-1023px | Drawer | 2×5 (10th spans) | Stacked |
| < 768px | Drawer | 1×9 (scroll) | Stacked |

### 8.2 Chart Responsiveness
- uPlot auto-downsamples to ~500 points max
- Container queries for chart sizing
- Legend collapses to dropdown on < 640px
- Tooltip follows finger on touch

## 9. Accessibility Checklist

- [ ] Semantic HTML (header, main, aside, section, article)
- [ ] ARIA labels on icon-only buttons
- [ ] Live regions for alert announcements (aria-live="assertive")
- [ ] Focus visible outlines (3px, --color-info)
- [ ] Skip to main content link
- [ ] Color-blind safe palette (tested with Coblis)
- [ ] 4.5:1 contrast all text
- [ ] 3:1 contrast UI elements
- [ ] Keyboard navigation: Tab, Enter, Escape, Arrow keys
- [ ] Screen reader tested (NVDA, VoiceOver)
- [ ] Reduced motion respected (prefers-reduced-motion)
- [ ] Dark mode supported (system preference + manual toggle)

## 10. Icon System

### 10.1 Icon Set: Lucide React (tree-shakeable, consistent)
```tsx
// Key icons used
import {
  Droplet,        // Water, TDS
  Filter,         // Filter health
  Gauge,          // AquaScore, diagnostics
  AlertTriangle,  // Warning
  AlertCircle,    // Critical
  CheckCircle,    // Success, resolved
  Info,           // Info
  Zap,            // Pump energy
  Waves,          // Flow
  Mountain,       // Pressure
  Database,       // Tank
  Shield,         // Safety
  Settings,       // Config
  RefreshCw,      // Refresh, recalibrate
  Download,       // Export
  Upload,         // Firmware update
  Wifi,           // Connectivity
  Cpu,            // Device health
  History,        // Trends
  Search,         // Anomaly
  Brain,          // ML/AI
  Wrench,         // Maintenance
  RotateCcw,      // Verification
  Clock,          // RUL, freshness
  Eye,            // View details
  Mail,           // Notifications
  Bell,           // Alerts
  Menu,           // Sidebar toggle
  ChevronLeft,    // Collapse
  ChevronRight,   // Expand
  X,              // Close
  Plus,           // Add
  Edit,           // Edit
  Trash,          // Delete
  ArrowUpRight,   // External link
} from 'lucide-react';
```

## 11. Design Tokens Export (for Tailwind)
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Semantic
        success: '#059669',
        warning: '#d97706',
        critical: '#dc2626',
        info: '#2563eb',
        // Neutral
        base: '#ffffff',
        surface: '#f8fafc',
        elevated: '#ffffff',
        hover: '#f1f5f9',
        active: '#e2e8f0',
        border: '#e2e8f0',
        'border-emphasis': '#94a3b8',
        text: '#0f172a',
        'text-secondary': '#475569',
        'text-muted': '#94a3b8',
        // Charts
        chart: {
          1: '#0ea5e9', 2: '#22c55e', 3: '#f59e0b', 4: '#ef4444',
          5: '#8b5cf6', 6: '#ec4899', 7: '#06b6d4', 8: '#84cc16',
        },
        gauge: {
          good: '#059669', warn: '#d97706', crit: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        display: ['3rem', { lineHeight: '1.1', fontWeight: '600' }],
        h1: ['2rem', { lineHeight: '1.2', fontWeight: '600' }],
        h2: ['1.5rem', { lineHeight: '1.3', fontWeight: '600' }],
        h3: ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],
        'body-lg': ['1.125rem', { lineHeight: '1.5' }],
        body: ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        caption: ['0.75rem', { lineHeight: '1.4', fontWeight: '500' }],
        data: ['1rem', { lineHeight: '1.2', fontWeight: '500' }],
        'data-lg': ['2rem', { lineHeight: '1.1', fontWeight: '600' }],
        'data-xl': ['3rem', { lineHeight: '1', fontWeight: '700' }],
      },
      spacing: {
        1: '4px', 2: '8px', 3: '12px', 4: '16px', 5: '20px',
        6: '24px', 8: '32px', 10: '40px', 12: '48px', 16: '64px',
      },
      borderRadius: {
        card: '12px',
        button: '8px',
        input: '8px',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-up': 'slideUp 200ms ease-out',
        'slide-down': 'slideDown 300ms ease-out',
        'pulse-critical': 'pulseCritical 1000ms ease-in-out infinite',
        'gauge-sweep': 'gaugeSweep 600ms ease-out',
        'value-transition': 'valueTransition 300ms ease-out',
        'shimmer': 'shimmer 1500ms linear infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        slideUp: { '0%': { opacity: 0, transform: 'translateY(8px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        slideDown: { '0%': { opacity: 0, transform: 'translateY(-8px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        pulseCritical: { '0%, 100%': { transform: 'scale(1)' }, '50%': { transform: 'scale(1.02)' } },
        gaugeSweep: { '0%': { strokeDashoffset: '100%' }, '100%': { strokeDashoffset: '0%' } },
        valueTransition: { '0%': { opacity: 0.5 }, '100%': { opacity: 1 } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
    },
  },
};
```

## 12. Implementation Notes

- **CSS-in-JS**: None. Tailwind + CSS variables for theming
- **Component Library**: Build primitives, no external UI kit
- **Charts**: uPlot (primary), custom SVG gauges
- **Icons**: Lucide React (tree-shakeable)
- **Forms**: React Hook Form + Zod validation
- **State**: TanStack Query (server), React Context (client UI)
- **Testing**: Vitest + React Testing Library (unit), Playwright (e2e)