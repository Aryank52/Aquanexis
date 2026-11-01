# AquaNexis Frontend

React + TypeScript + Vite frontend for the AquaNexis Predictive Water Intelligence Platform.

## Quick Start

### Prerequisites
- Node.js 20+
- npm 10+

### Local Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Type check
npm run typecheck

# Lint & format
npm run lint
npm run format
```

### With Docker Compose (from project root)
```bash
docker compose up -d frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # App shell, routing, providers
│   │   ├── components/         # Layout components (Layout, Header, Sidebar)
│   │   └── routes.tsx          # Route definitions
│   ├── pages/                  # Page components (one per route)
│   │   ├── landing/            # Public landing page
│   │   ├── dashboard/          # Main dashboard
│   │   ├── water-quality/      # Water quality analysis
│   │   ├── purification-performance/
│   │   ├── filter-health/      # FSI, FHI, RUL
│   │   ├── diagnostics/        # Pressure, flow, leak, tank, pump
│   │   ├── alerts/             # Alert management
│   │   ├── maintenance/        # Filter replacement, calibration
│   │   ├── device-health/      # Sensor status, firmware
│   │   └── readiness/          # Engineering readiness checklist
│   ├── components/
│   │   ├── ui/                 # Primitive components (Button, Card, Badge, etc.)
│   │   ├── layout/             # Layout components
│   │   ├── charts/             # Chart components (Gauge, Sparkline, etc.)
│   │   └── dashboard/          # Dashboard-specific composites
│   ├── features/               # Feature-specific components & logic
│   ├── api/                    # API client, endpoints, WebSocket
│   ├── hooks/                  # Custom React hooks
│   ├── state/                  # Client state (theme, UI)
│   ├── types/                  # TypeScript types
│   ├── utils/                  # Utility functions
│   └── styles/                 # Global styles, Tailwind
├── public/                     # Static assets
├── tests/                      # Test setup
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── nginx.conf
```

## Key Technologies

| Layer | Technology |
|-------|------------|
| Framework | React 18 + TypeScript (strict) |
| Build | Vite 5 |
| Routing | React Router 6 |
| Server State | TanStack Query (React Query) 5 |
| Styling | Tailwind CSS 3 + CSS Variables |
| Charts | uPlot (time-series) + Custom SVG (gauges) |
| Forms | React Hook Form + Zod |
| Icons | Lucide React |
| Testing | Vitest + React Testing Library + Playwright |

## Design System

### Colors (Semantic Only)
- **Success** (`#059669`) - Good states, healthy
- **Warning** (`#d97706`) - Attention needed
- **Critical** (`#dc2626`) - Immediate action required
- **Info** (`#2563eb`) - Neutral information

### Typography
- **Sans**: Inter (UI text)
- **Mono**: JetBrains Mono (data values, code)

### Spacing
- Base unit: 8px (Tailwind `2`)
- Scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px

### Motion (Approved Only)
- Page transitions: 200ms fade + slide
- Gauge animations: 600ms ease-out
- Value transitions: 300ms
- Alert banner: 300ms slide down
- Critical pulse: 1000ms infinite

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## API Integration

### TanStack Query Configuration
```typescript
// Default options in main.tsx
staleTime: 5000      // 5 seconds
gcTime: 60000        // 1 minute
retry: 3             // Except 4xx errors
refetchOnWindowFocus: false
```

### Query Keys Structure
```typescript
// Device-scoped keys
['device', deviceId, 'telemetry', 'latest']
['device', deviceId, 'water-quality']
['device', deviceId, 'filter-health']
['device', deviceId, 'diagnostics']
['device', deviceId, 'alerts']
['device', deviceId, 'maintenance']
```

## WebSocket Integration

Real-time updates via WebSocket at `/ws/realtime/{deviceId}`:

```typescript
// Message types received
{ type: 'telemetry', device_id, data }
{ type: 'alert_created', device_id, alert }
{ type: 'alert_updated', device_id, alert }
{ type: 'safety_action', device_id, action, trigger }
{ type: 'device_status', device_id, status, last_seen }
```

## Testing

```bash
# Unit tests
npm test

# With coverage
npm run test:coverage

# E2E tests (requires running services)
npm run test:e2e

# Watch mode
npm run test -- --watch
```

## Building for Production

```bash
npm run build
```

Output in `dist/` - ready for Nginx or any static host.

## Docker

```bash
# Build
docker build -t aquanexis-frontend ./frontend

# Run
docker run -p 3000:3000 aquanexis-frontend
```

## Development Guidelines

### Component Patterns
1. **Primitive components** in `components/ui/` - no business logic
2. **Composite components** in `components/dashboard/`, etc. - compose primitives
3. **Page components** in `pages/` - compose composites, handle routing
4. **Hooks** for data fetching - one per domain (telemetry, alerts, etc.)

### State Management
- **Server state** → TanStack Query (never in local state)
- **Client state** → React Context + useReducer (theme, modals, toasts)
- **URL state** → React Router (filters, pagination, tabs)

### Performance
- Lazy-load feature pages with `React.lazy()`
- Prefetch predictable navigations
- Downsample chart data (uPlot handles automatically)
- Use `React.memo` for expensive list items

### Accessibility
- Semantic HTML always
- ARIA labels on icon-only buttons
- Live regions for alerts (`aria-live="assertive"`)
- Focus visible outlines
- Color + icon + text for all status indicators
- WCAG AA contrast ratios

## Code Quality

```bash
# Type check
npm run typecheck

# Lint
npm run lint

# Format
npm run format

# All checks
npm run lint && npm run format:check && npm run typecheck && npm test
```