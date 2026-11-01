# AquaNexis — Technology Stack Decisions

## Decision Framework
Each decision follows: **Context → Options → Decision → Rationale → Consequences**

---

## 1. Backend Framework: FastAPI

**Context**: Need modern, async, type-safe Python API with OpenAPI generation.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| FastAPI | Async native, Pydantic integration, OpenAPI auto, fast, growing ecosystem | Younger than Flask/Django |
| Flask | Mature, huge ecosystem, flexible | Sync by default, no built-in validation, manual OpenAPI |
| Django + DRF | Batteries included, admin, auth, ORM | Heavy, sync-first, ORM coupling |
| Starlette | FastAPI's foundation, minimal | More boilerplate, no validation layer |

**Decision**: **FastAPI**

**Rationale**:
- Async-first matches telemetry ingestion throughput needs
- Pydantic schemas = single source of truth for validation + docs
- Automatic OpenAPI = contract-first development
- Type hints enable mypy checking across layers
- Growing production adoption (Microsoft, Netflix, Uber)

**Consequences**:
- Requires Python 3.10+
- Async SQLAlchemy required (not sync ORM)
- Team must be comfortable with async patterns

---

## 2. Database: PostgreSQL + TimescaleDB

**Context**: Time-series sensor data (immutable, high write volume) + relational domain data.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| PostgreSQL + TimescaleDB | Native SQL, hypertables, compression, continuous aggregates, PG ecosystem | Extension dependency |
| InfluxDB | Purpose-built TSDB, Flux/InfluxQL | Separate query language, no relational joins, TSM engine limits |
| TimescaleDB alone | Same as PG+Timescale | Same |
| ClickHouse | Incredible OLAP compression, speed | No transactions, mutable data harder, separate system |
| MongoDB | Flexible schema, time-series collections | No ACID across collections, aggregation pipeline complexity |

**Decision**: **PostgreSQL 16 + TimescaleDB 2.14+**

**Rationale**:
- Single database for relational + time-series
- Hypertables = automatic partitioning by time
- Compression policies reduce storage 90%+
- Continuous aggregates = precomputed trends
- Standard SQL for all queries
- ACID for devices, alerts, maintenance
- Mature tooling (pgAdmin, pg_dump, logical replication)

**Consequences**:
- Must run TimescaleDB image (not vanilla PG)
- Chunk time interval tuning needed (1 day default)
- Compression requires `timescaledb.compress` segmentby on device_id

---

## 3. ORM: SQLAlchemy 2.0 (Async)

**Context**: Type-safe database access with async support.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| SQLAlchemy 2.0 async | Mature, flexible, async, type stubs, migration support | Verbose, learning curve |
| Tortoise ORM | Django-like, async native | Less mature, fewer features |
| Prisma (Python) | Type-safe, modern | Early stage, Python support limited |
| Raw asyncpg | Maximum control | Boilerplate, no migration integration |

**Decision**: **SQLAlchemy 2.0 with asyncpg driver**

**Rationale**:
- Industry standard, battle-tested
- AsyncSession + async engine = proper concurrency
- Alembic integration first-class
- Type stubs support mypy checking
- Flexible query building for complex time-series queries

**Consequences**:
- Must use `select()` / `insert()` modern API (not legacy Query)
- Relationship loading strategies (selectinload, joinedload) critical for N+1 prevention
- Domain models separate from ORM models (repository pattern)

---

## 4. Migration Tool: Alembic

**Context**: Schema evolution with version control.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| Alembic | SQLAlchemy native, Python migrations, autogenerate, downgrade support | Manual review required |
| Django migrations | Auto-generated, integrated | Django-only |
| Raw SQL files | Full control | No tracking, no downgrade, error-prone |

**Decision**: **Alembic**

**Rationale**:
- Integrates with SQLAlchemy metadata
- Autogenerate from model changes (review required)
- Python migrations = logic + data migrations possible
- Version tracking in DB (`alembic_version` table)
- Works with any SQLAlchemy-supported DB

**Consequences**:
- Every schema change = migration file in `alembic/versions/`
- Never edit production schema manually
- Review autogenerate output (often misses indexes, constraints)

---

## 5. Configuration: Pydantic Settings v2

**Context**: Type-safe, validated configuration from environment.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| Pydantic Settings | Type validation, nested models, env file, secrets dir, computed fields | v2 breaking changes from v1 |
| python-dotenv + manual | Simple | No validation, no types |
| Dynaconf | Layered config, multiple sources | More complex API |

**Decision**: **Pydantic Settings v2**

**Rationale**:
- Same validation engine as API schemas
- Nested settings models (DatabaseSettings, AuthSettings, MLSettings)
- `.env` file support + environment variable override
- `SecretStr` for sensitive values (never logged)
- Computed fields for derived config

**Consequences**:
- All config accessed via `settings` singleton
- Validation fails fast on startup
- `.env.example` must be maintained

---

## 6. API Documentation: OpenAPI (Built-in)

**Context**: Contract-first development, client generation.

**Decision**: **FastAPI native OpenAPI** → Swagger UI at `/docs`, ReDoc at `/redoc`

**Rationale**:
- Zero configuration
- Pydantic models = schema definitions
- Automatic request/response examples
- Client SDK generation (openapi-generator, orval)

**Consequences**:
- Keep schemas in `schemas/` package
- Use `Field(description=...)` for documentation
- Tag endpoints for organized UI

---

## 7. Authentication: Device JWT + API Keys

**Context**: Device-to-backend (mutual TLS overkill), admin-to-backend.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| Device JWT (HS256) | Stateless, short expiry, rotatable, per-device claims | Secret rotation needed |
| mTLS | Strong identity, no shared secret | Cert provisioning complexity, ESP32 TLS stack limits |
| API Key (shared) | Simple | No expiry, no claims, rotation harder |
| OAuth2/OIDC | Standard, delegated auth | Overkill for device-to-server |

**Decision**: **Device JWT (HS256, 24h expiry) + Admin API Keys**

**Rationale**:
- ESP32 can handle HS256 JWT (libraries exist)
- Short expiry limits blast radius
- Claims: `device_id`, `iat`, `exp`, `scope`
- Admin API keys for provisioning, management
- JWT secret rotated quarterly via env var

**Consequences**:
- Device provisioning endpoint issues initial JWT
- Token refresh endpoint needed
- Revocation list for compromised devices (in-memory + DB)

---

## 8. Frontend Framework: React 18 + TypeScript + Vite

**Context**: Modern SPA with strong typing, fast dev server.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| React 18 + TS + Vite | Huge ecosystem, concurrent features, Vite speed, TS strict | Bundle size, learning curve |
| Vue 3 + TS + Vite | Similar benefits, Composition API | Smaller ecosystem |
| SvelteKit | Compiler-based, less runtime | Smaller ecosystem, younger |
| Next.js | SSR, RSC, file routing | Overkill for dashboard, Vercel lock-in |

**Decision**: **React 18 + TypeScript (strict) + Vite 5**

**Rationale**:
- TanStack Query native React hooks
- uPlot works well with React refs
- Vite = instant HMR, optimized builds
- TypeScript strict catches bugs early
- Large hiring pool, component library options

**Consequences**:
- `tsconfig.json` with `strict: true`
- Path aliases (`@/` → `src/`)
- ESLint + Prettier enforced in CI

---

## 9. Server State: TanStack Query (React Query) v5

**Context**: Server state ≠ client state. Need caching, deduping, invalidation.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| TanStack Query | Purpose-built, caching, deduping, prefetching, mutations, devtools | Learning curve |
| Redux Toolkit + RTK Query | Integrated with Redux | Redux boilerplate, overkill |
| SWR | Simpler, Vercel | Fewer features, no mutation helpers |
| Custom Context + useEffect | Full control | Re-inventing wheel poorly |

**Decision**: **TanStack Query v5**

**Rationale**:
- Designed exactly for this: server state synchronization
- Stale-while-revalidate = fast perceived performance
- Request deduping = no duplicate fetches
- Prefetching = instant navigation
- Mutation helpers = optimistic updates
- Devtools for debugging

**Consequences**:
- No Redux/Zustand for server state
- Client-only state (UI, modals) → React Context + useReducer
- Query keys structured: `['device', deviceId, 'telemetry', 'latest']`

---

## 10. Styling: Tailwind CSS v3

**Context**: Utility-first, design token integration, no runtime overhead.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| Tailwind CSS | Design tokens → config, JIT compiler, small bundle, responsive utilities | Learning curve, HTML verbosity |
| CSS Modules + CSS Variables | Standard, scoped, variables | Manual utility creation |
| Styled Components / Emotion | Colocated, dynamic | Runtime overhead, bundle size |
| Plain CSS + BEM | Zero deps | Verbose, no token system |

**Decision**: **Tailwind CSS v3 with custom design tokens**

**Rationale**:
- Design tokens from uiux-brief map directly to `tailwind.config.js`
- JIT compiler = only used utilities in bundle
- Dark mode via `class` strategy + CSS variables
- Responsive utilities = mobile-first without media queries
- `@apply` for component patterns (Button, Card)

**Consequences**:
- `globals.css` imports Tailwind base/components/utilities
- Custom CSS variables for semantic colors (gauge bands, charts)
- Component classes built with `@apply` in `components/ui/*.css`

---

## 11. Charting: uPlot + Custom SVG Gauges

**Context**: High-frequency time-series (10k+ points), gauges, sparklines.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| uPlot | 100k+ points @ 60fps, downsampling built-in, tiny (25kb), no VDOM | Imperative API, learning curve |
| Recharts | Declarative, React-native, composable | Slow > 1k points, VDOM overhead |
| Chart.js | Canvas, decent performance | Larger, plugin system complex |
| Victory / VisX | React-native, flexible | Performance limits |
| Custom Canvas | Full control | Reinventing interaction |

**Decision**: **uPlot for time-series + Custom SVG for gauges**

**Rationale**:
- uPlot handles 10k+ points with automatic downsampling
- 25kb gzipped = negligible bundle impact
- Imperative API fits React `useEffect` + ref pattern
- Gauges = simple SVG arcs (animated with CSS/SMIL)
- No chart library for gauges = lighter, more controllable

**Consequences**:
- Chart components wrap uPlot instance lifecycle
- Downsampling configured per chart (max 500 points visible)
- Tooltip / crosshair via uPlot hooks
- Gauges use CSS custom properties for colors

---

## 12. Icon Library: Lucide React

**Context**: Consistent, tree-shakeable, React-native icons.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| Lucide React | 1000+ icons, tree-shakeable, consistent stroke, React components | None significant |
| Heroicons | Tailwind official, two styles | Fewer icons |
| Phosphor | Many weights, large | Larger bundle |
| Material Icons | Comprehensive | Google branding, not tree-shakeable easily |

**Decision**: **Lucide React**

**Rationale**:
- Tree-shaking = only imported icons in bundle
- Consistent 2px stroke weight
- React components (no wrapper needed)
- MIT license

**Consequences**:
- Import individually: `import { Gauge } from 'lucide-react'`
- Size controlled via `size` prop (default 24)

---

## 13. Forms: React Hook Form + Zod

**Context**: Type-safe forms with validation.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| React Hook Form + Zod | Uncontrolled (fast), Zod schema = single source, resolver integration | Two libraries |
| Formik + Yup | Mature | Controlled (slower), larger bundle |
| React Final Form | Subscription-based | Smaller community |

**Decision**: **React Hook Form + Zod**

**Rationale**:
- Uncontrolled inputs = fast rendering
- Zod schemas shared with backend (or mirrored)
- `zodResolver` = seamless integration
- Type inference from schema

**Consequences**:
- Form schemas in `schemas/forms/` or co-located
- Backend Pydantic ↔ Frontend Zod parity maintained manually (or codegen later)

---

## 14. Testing

### Backend: pytest + pytest-asyncio + httpx
- Unit: domain logic, services, validators (fast, no DB)
- Integration: API endpoints with test DB (Testcontainers or local PG)
- Coverage target: > 80% domain/services

### Frontend: Vitest + React Testing Library + MSW
- Unit: components, hooks, utils
- Integration: page flows with mocked API (MSW)
- Coverage target: > 70% components

### E2E: Playwright
- One critical journey: Dashboard → anomaly → alert → filter health → maintenance
- Run in CI against staged docker-compose

---

## 15. Code Quality

| Tool | Purpose | Config |
|------|---------|--------|
| **ruff** | Python linting + formatting (replaces flake8, black, isort) | `ruff.toml` |
| **mypy** | Static type checking (strict) | `mypy.ini` |
| **pytest** | Testing | `pytest.ini` |
| **ESLint** | JS/TS linting (typescript-eslint, react-hooks, jsx-a11y) | `.eslintrc.json` |
| **Prettier** | Formatting | `.prettierrc` |
| **TypeScript** | Type checking | `tsconfig.json` (strict) |
| **Vitest** | Unit testing | `vitest.config.ts` |

---

## 16. Containerization

| Component | Base Image | Strategy |
|-----------|------------|----------|
| Backend | `python:3.12-slim` | Multi-stage: build deps → runtime |
| Frontend | `node:20-alpine` (build) → `nginx:alpine` (serve) | Multi-stage: npm build → nginx static |
| Database | `timescale/timescaledb:latest-pg16` | Official image |
| Simulator | `python:3.12-slim` | Same as backend |

---

## 17. CI/CD: GitHub Actions

**Workflows**:
1. `backend.yml` — lint, typecheck, test, build, migration check
2. `frontend.yml` — lint, typecheck, test, build
3. `integration.yml` — docker compose up, health checks, API smoke tests
4. `release.yml` — tag → build images → push to registry

**Quality Gates**:
- All checks must pass to merge
- Coverage thresholds enforced
- No `mypy`/`ruff`/`eslint` errors
- Migration check: `alembic check` (no pending migrations)

---

## 18. Observability Stack (Future)

| Layer | Tool | Status |
|-------|------|--------|
| Metrics | Prometheus + Grafana | Planned |
| Logs | Loki + Grafana | Planned |
| Traces | Tempo + Grafana | Planned |
| Alerting | Alertmanager | Planned |
| Uptime | Uptime Kuma | Planned |

**Current**: Structured JSON logs to stdout, `/metrics` endpoint (prometheus-client)

---

## 19. Firmware: ESP-IDF (C) / Arduino ESP32

**Context**: ESP32-S3 target, multiple sensors, HTTPS, JWT.

**Decision**: **ESP-IDF v5.x (C) with esp-tls, mbedTLS, cJSON**

**Rationale**:
- Full control over memory, TLS, tasks
- ESP-IDF mature, supported by Espressif
- Arduino framework = larger binary, less control
- FreeRTOS tasks for sensor polling, network, safety

**Consequences**:
- C development environment needed
- Component-based (sensor drivers, telemetry, auth, safety)
- OTA updates via HTTPS
- Local safety fallback independent of cloud

---

## 20. Simulator: Python (FastAPI Test Client Pattern)

**Context**: Develop without hardware.

**Decision**: **Python asyncio service mimicking device API**

**Rationale**:
- Same language as backend = shared schemas (Pydantic)
- Generates realistic sensor patterns (diurnal, noise, drift, anomalies)
- Configurable device count, interval, anomaly injection
- Runs in docker-compose alongside backend

**Consequences**:
- Simulator imports backend schemas (shared package or copy)
- Not a digital twin — statistical approximation
- Used for CI integration tests

---

## 21. ML Stack (Future-Proofing)

| Layer | Current | Future |
|-------|---------|--------|
| Experiment Tracking | Local files + JSON | MLflow |
| Model Registry | PostgreSQL table | MLflow / BentoML |
| Training | Scripts (scikit-learn, XGBoost) | Kubeflow / Airflow |
| Inference | In-process (joblib/ONNX) | Triton / BentoML |
| Features | Python functions | Feast |

**Current Decision**: **In-process inference with joblib artifacts, PostgreSQL registry**

**Rationale**:
- No model serving infrastructure needed yet
- joblib = fast, no dependencies
- Registry in DB = versioned, queryable
- Scikit-learn / XGBoost = deterministic, explainable

---

## 22. Notification Providers (Extensible)

**Interface**: `NotificationProvider` protocol with `send(alert, channels)`

**Implemented**:
- **Console** (dev) — logs to stdout
- **Email** (SMTP) — via aiosmtplib
- **Webhook** — POST JSON to configured URL

**Future**: Push (Firebase), SMS (Twilio), Slack, PagerDuty

---

## 23. Summary: Core Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language (Backend) | Python | 3.12 |
| API Framework | FastAPI | 0.110+ |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL + TimescaleDB | 16 / 2.14 |
| Migrations | Alembic | 1.13 |
| Config | Pydantic Settings | 2.0 |
| Auth | PyJWT (HS256) | 2.8 |
| Logging | structlog | 24.1 |
| Testing | pytest, pytest-asyncio, httpx | Latest |
| Language (Frontend) | TypeScript | 5.4 |
| Framework | React | 18.2 |
| Build | Vite | 5.1 |
| State | TanStack Query | 5.20 |
| Styling | Tailwind CSS | 3.4 |
| Charts | uPlot | 1.6 |
| Icons | Lucide React | 0.44 |
| Forms | React Hook Form + Zod | 7.5 / 3.22 |
| Testing | Vitest, RTL, Playwright | Latest |
| Container | Docker | 24+ |
| Orchestration | Docker Compose (dev) | 2.24 |
| CI/CD | GitHub Actions | - |

---

## 24. Rejected Alternatives (With Reasons)

| Rejected | Reason |
|----------|--------|
| GraphQL | Overkill for known query patterns; REST + OpenAPI sufficient |
| gRPC (external) | No polyglot clients yet; REST + WebSocket simpler |
| Redis (caching) | Not needed yet; TanStack Query + PG indexes sufficient |
| Kubernetes (dev) | Docker Compose sufficient; k8s for production only |
| MongoDB | Relational domain data + time-series = PG better fit |
| Next.js | SSR not needed; dashboard is authenticated SPA |
| Redux | TanStack Query + Context covers all state needs |
| WebSockets (raw) | Need connection management, reconnection, multiplexing → use library |
| Socket.io | Adds custom protocol; native WebSocket + JSON sufficient |
| Material UI / Ant Design | Bundle size, customization overhead; build primitives instead |
| Chart.js / Recharts | Performance insufficient for 10k+ point time-series |
| InfluxDB | Separate system; TimescaleDB gives SQL + TS in one |
| Celery | Background tasks via FastAPI BackgroundTasks + scheduled jobs sufficient |
| Kafka | Ingestion volume not yet justified; HTTP + PG write path simple |

---

## 25. Decision Log

| Date | Decision | Author | Link |
|------|----------|--------|------|
| 2026-10-31 | FastAPI + PostgreSQL + TimescaleDB | Lead Engineer | This doc |
| 2026-10-31 | React + TanStack Query + uPlot | Lead Engineer | This doc |
| 2026-10-31 | Deterministic ML first | Lead Engineer | This doc |
| 2026-10-31 | Safety as isolated subsystem | Lead Engineer | This doc |
| 2026-10-31 | Modular monolith architecture | Lead Engineer | architecture.md |

*Update this log when stack decisions change.*