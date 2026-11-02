# Troubleshooting Guide

## Frontend Issues

### `npm ci` fails with "package-lock.json out of sync"

**Symptom:**
```
npm error `npm ci` can only install packages when your package.json and package-lock.json or npm-shrinkwrap.json are in sync.
```

**Solution:**
```bash
cd frontend
npm install  # Updates package-lock.json
npm ci       # Now works
```

### ESLint: "Couldn't find an eslint.config.* file"

**Symptom:**
```
ESLint couldn't find an eslint.config.* file.
```

**Cause:** ESLint v9+ uses flat config by default, but project uses `.eslintrc.cjs`.

**Solution:** Ensure `.eslintrc.cjs` exists in `frontend/` and run eslint from local node_modules:
```bash
cd frontend
.\node_modules\.bin\eslint.cmd . --ext ts,tsx
```

### ESLint: "Couldn't find the config 'prettier' to extend from"

**Symptom:**
```
ESLint couldn't find the config "prettier" to extend from.
```

**Solution:**
```bash
cd frontend
npm install --save-dev eslint-config-prettier
```

### ESLint: "plugin:react-refresh/recommended is invalid"

**Symptom:**
```
ESLint configuration in .eslintrc.cjs » plugin:react-refresh/recommended is invalid:
  - Unexpected top-level property "name".
```

**Solution:** Remove `plugin:react-refresh/recommended` from extends in `.eslintrc.cjs` (incompatibility with ESLint 8.57).

### TypeScript: "ESLint was configured to run on tests/setup.ts but TSConfig doesn't include this file"

**Symptom:**
```
ESLint was configured to run on `<tsconfigRootDir>/tests\setup.ts`...
However, none of those TSConfigs include this file.
```

**Solution:** Add `tests/setup.ts` to `include` in `tsconfig.json` or add to `ignorePatterns` in `.eslintrc.cjs`:
```js
ignorePatterns: ['dist', '.eslintrc.cjs', 'tests/setup.ts'],
```

### Frontend dev server won't start

**Symptom:** `npm run dev` hangs or fails.

**Solutions:**
1. Check port 3000 is free: `netstat -ano | findstr :3000`
2. Kill process on port 3000: `taskkill /PID <pid> /F`
3. Clear Vite cache: `rm -rf node_modules/.vite`
4. Reinstall: `rm -rf node_modules package-lock.json && npm install`

### Frontend can't reach backend

**Symptom:** API calls fail with CORS or connection errors.

**Checklist:**
1. Backend running on `http://localhost:8000`
2. `frontend/.env` has `VITE_API_URL=http://localhost:8000`
3. Backend `ALLOWED_ORIGINS` includes `http://localhost:3000`
4. Vite proxy config in `vite.config.ts` points to `http://localhost:8000`

### WebSocket connection fails

**Symptom:** WebSocket connection to `ws://localhost:8000/ws/...` fails.

**Checklist:**
1. Backend running and WebSocket endpoint registered at `/ws/devices/{device_id}`
2. `frontend/.env` has `VITE_WS_URL=ws://localhost:8000`
3. Vite proxy config in `vite.config.ts` has `/ws` proxy to `ws://localhost:8000`

---

## Backend Issues

### PostgreSQL Connection Refused

**Symptom:**
```
ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
```

**Solutions:**
1. Start PostgreSQL service (as Administrator):
   ```powershell
   net start postgresql-x64-16
   ```
2. Check PostgreSQL is listening on port 5432:
   ```bash
   netstat -ano | findstr :5432
   ```
3. Verify `DATABASE_URL` in `.env` matches running instance:
   ```
   DATABASE_URL=postgresql+asyncpg://aquanexis:aquanexis@localhost:5432/aquanexis
   ```
4. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\16\data\log\`

### PostgreSQL Crashes with Exception 0xC0000142 (DLL Initialization Failure)

**Symptom:** PostgreSQL starts successfully, accepts connections for ~2-3 minutes, then crashes with:
```
LOG: server process (PID) was terminated by exception 0xC0000142
HINT: See C include file "ntstatus.h" for a description of the hexadecimal value.
```

**Log Indicators:**
```
LOG: could not open file "./postgresql.log": sharing violation
HINT: You might have antivirus, backup, or similar software interfering with the database system.
```

**Root Cause:** Antivirus/Windows Defender interfering with PostgreSQL data directory (`E:\postsql database\data`), causing DLL initialization failure (0xC0000142 = STATUS_DLL_INIT_FAILED).

**Solutions:**
1. **Exclude PostgreSQL data directory from antivirus scanning:**
   - Open Windows Security → Virus & threat protection → Manage settings → Exclusions
   - Add folder: `E:\postsql database\data`
2. **Run PostgreSQL in Docker** (requires Docker Desktop):
   ```bash
   docker run -d --name postgres -e POSTGRES_DB=aquanexis -e POSTGRES_USER=aquanexis -e POSTGRES_PASSWORD=aquanexis -p 5432:5432 -v pgdata:/var/lib/postgresql/data timescale/timescaledb:latest-pg16
   ```
3. **Install as Windows service with proper permissions** (requires Admin):
   ```powershell
   # Run PowerShell as Administrator
   & "E:\postsql database\bin\pg_ctl.exe" register -N "postgresql-x64-16" -D "E:\postsql database\data"
   net start postgresql-x64-16
   ```

### Alembic Migration Fails

**Symptom:** `alembic upgrade head` fails.

**Solutions:**
1. Ensure database exists and user has permissions
2. Check `alembic.ini` has correct `sqlalchemy.url`
3. Reset migrations (destructive):
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

### `pytest` fails with "ConnectionRefusedError"

**Symptom:** Tests fail with PostgreSQL connection errors.

**Cause:** Tests in `tests/unit/test_health.py` and `tests/unit/test_models.py` require PostgreSQL.

**Solution:** Run only tests that don't require DB:
```bash
pytest tests/unit/test_config.py tests/unit/test_security.py tests/unit/test_phase_d_services.py tests/unit/test_alert_state_machine.py tests/unit/test_auto_clear_integration.py tests/unit/test_notification_providers.py tests/unit/test_maintenance.py -v
```

### `ruff` or `mypy` not found

**Solution:**
```bash
cd backend
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### `alembic` command not found

**Solution:**
```bash
cd backend
.\.venv\Scripts\Activate.ps1
pip install alembic
```

---

## Database Issues

### TimescaleDB Extension Missing

**Symptom:** Migration fails with "extension 'timescaledb' not found".

**Solution:**
```sql
-- Connect as postgres superuser
psql -U postgres -d aquanexis -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### Permission Denied for Database

**Symptom:** `permission denied for database aquanexis`

**Solution:**
```sql
-- Connect as postgres superuser
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE aquanexis TO aquanexis;"
psql -U postgres -d aquanexis -c "GRANT ALL ON SCHEMA public TO aquanexis;"
```

---

## Docker Issues

### `docker compose up` fails

**Symptom:** Various Docker Compose errors.

**Solutions:**
1. Ensure Docker Desktop is running
2. Check WSL 2 backend is enabled
3. Run `docker compose down -v` to clean up
4. Check port conflicts: `netstat -ano | findstr "3000\|8000\|5432"`

### Frontend container can't reach backend

**Symptom:** Frontend in Docker can't proxy to backend.

**Cause:** In Docker, `localhost` refers to the container, not host.

**Solution:** Use service names in Docker Compose:
```yaml
# In frontend nginx.conf or Vite proxy
proxy_pass http://backend:8000;  # Not localhost:8000
```

---

## Simulator Issues

### Simulator fails to connect to backend

**Symptom:** `Error creating device: All connection attempts failed`

**Solutions:**
1. Ensure backend is running on `http://localhost:8000`
2. Check `BACKEND_URL` in simulator environment
3. Verify device JWT is valid (simulator generates one automatically)

### Simulator profile not found

**Symptom:** `error: argument --profile: invalid choice`

**Solution:** Use valid profile names:
```bash
python simulator.py --profile normal
python simulator.py --profile filter_stress
python simulator.py --profile high_turbidity
python simulator.py --profile low_flow
python simulator.py --profile high_pressure_drop
python simulator.py --profile leak
python simulator.py --profile sensor_fault
python simulator.py --profile device_offline
```

---

## Windows-Specific Issues

### "Access is denied" when starting PostgreSQL

**Cause:** Requires Administrator privileges.

**Solution:** Run PowerShell as Administrator:
```powershell
Start-Process powershell -Verb RunAs
# Then in the new window:
net start postgresql-x64-16
```

### `npm ci` fails with EPERM on Windows

**Symptom:** `Error: EPERM: operation not permitted, unlink '...esbuild.exe'`

**Cause:** Antivirus or file locking.

**Solutions:**
1. Exclude `node_modules` from antivirus scanning
2. Close VS Code and other editors
3. Run as Administrator
4. Use `npm install` instead of `npm ci` for development

### Path too long errors

**Solution:** Enable long paths in Windows:
```powershell
# Run as Administrator
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
```

Or use shorter paths: `C:\AquaNexis` instead of `C:\Users\...\Documents\Projects\AquaNexis`

---

## CI/CD Issues

### GitHub Actions: Frontend lint fails

**Solution:** Ensure all ESLint configs are committed:
- `.eslintrc.cjs`
- `.prettierrc`
- `package.json` with correct eslint dependencies

### GitHub Actions: Backend tests fail

**Solution:** Ensure PostgreSQL service is configured in workflow:
```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    env:
      POSTGRES_DB: aquanexis_test
      POSTGRES_USER: aquanexis
      POSTGRES_PASSWORD: aquanexis
    ports: ["5432:5432"]
    options: --health-cmd "pg_isready -U aquanexis -d aquanexis_test" --health-interval 10s --health-timeout 5s --health-retries 5
```

### GitHub Actions: Docker build fails

**Solution:** Ensure Dockerfiles are valid:
```bash
# Test locally
docker build -t test-backend ./backend
docker build -t test-frontend ./frontend
```

---

## Getting Help

If issues persist:

1. Check the logs:
   - Frontend: Browser DevTools Console
   - Backend: `docker compose logs backend` or terminal output
   - Database: `docker compose logs postgres` or PostgreSQL logs

2. Verify versions:
   ```bash
   python --version
   node --version
   npm --version
   docker --version
   psql --version
   ```

3. Check the documentation:
   - [LOCAL_SETUP.md](LOCAL_SETUP.md)
   - [README.md](../README.md)

4. Run the full test suite to isolate issues:
   ```bash
   # Frontend
   cd frontend && npm run typecheck && npm test -- --run && npm run build
   
   # Backend (no DB)
   cd backend && pytest tests/unit/test_config.py tests/unit/test_security.py tests/unit/test_phase_d_services.py tests/unit/test_alert_state_machine.py tests/unit/test_auto_clear_integration.py tests/unit/test_notification_providers.py tests/unit/test_maintenance.py -v
   ```