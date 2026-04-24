# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JainSportBox is a CrossFit Box Management System with a Python/FastAPI backend and Vue.js 3 frontend. It handles members, memberships, attendance (via fingerprint sensor), WODs, finances, health metrics, personal records (1RM), and a product shop.

## Development Commands

### Backend
```bash
# From project root
cd backend
pip install -r requirements.txt          # or: pip install -r ../requirements.txt

# Create .env from template (required before first run)
cp .env.example .env

# Start backend (auto-creates DB tables and seeds admin on startup)
uvicorn main:app --reload --port 8000

# Or from project root:
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server at http://localhost:5173 (strictPort)
npm run build    # Production build → dist/
npm run preview  # Preview production build
```

There are no test commands — no test suite exists in this project.

## Architecture

**Two-process stack:**
- Backend: FastAPI on port 8000, SQLite database (`backend/crossfit.db`)
- Frontend: Vue 3 SPA on port 5173, talks to backend via Axios
- Bridge: `bridge/processor.py` — separate script for Arduino fingerprint sensor serial communication

**Backend layout:**
- `backend/main.py` — FastAPI app creation, CORS config, router registration. Runs SQLite migrations on startup (ALTER TABLE in try/except; table reconstruction for nullability changes via PRAGMA table_info). Mounts `backend/uploads/` as `/uploads` for static files (user profile photos). Starts APScheduler: alerts job runs at 9 AM Bogotá time AND immediately on startup.
- `backend/models.py` — All SQLAlchemy models (12 tables): `usuarios`, `planes`, `pagos`, `wods`, `resultados_wod`, `productos`, `ventas`, `asistencias`, `movimientos_financieros`, `medidas_salud`, `marcas_rm`, `alertas_membresia`
- `backend/database.py` — SQLite session factory
- `backend/security.py` — BCrypt password hashing, JWT creation/validation (HS256, 7-day expiry)
- `backend/routers/` — One file per domain: `auth`, `usuarios`, `pagos`, `planes`, `productos`, `ventas`, `wods`, `asistencia`, `finanzas`, `salud`, `alertas`, `marcas`
- `backend/schemas/` — Pydantic request/response models; one file per domain except `planes` (schemas defined inline in router): `asistencia`, `alerta`, `finanza`, `pago`, `producto`, `venta`, `wod`, `usuario`, `salud`, `marcas`
- `backend/seed.py` — Creates default plans and admin user (runs on app startup via `main.py`)

**Frontend layout:**
- `frontend/src/main.js` — Vue app init; Axios interceptor adds `Authorization: Bearer {token}` from `localStorage`
- `frontend/src/api.js` — Axios instance with `baseURL: http://127.0.0.1:8000`
- `frontend/src/router/index.js` — Route guards using `meta.requiresAuth` and `meta.roles`; clients default to `/wods`, admin/coach to `/usuarios`
- `frontend/src/composables/useAuth.js` — Reactive role helpers: `isAdmin`, `isCoach`, `isCliente`, `canManage`
- `frontend/src/views/` — One large SFC per page: `LoginView`, `UsuariosView`, `TiendaView`, `WodsView`, `FinanzasView`, `PlanesView`, `AlertasView`, `SaludView`, `SaludMedidaView`, `MarcasView`, `MarcasEjercicioView`. (`MonitorAccesoView.vue` exists but is not registered in the router.)
- `frontend/src/components/Dashboard.vue` — Main layout shell (sidebar + navigation)
- `frontend/src/data/` — Shared config files: `saludTipos.js` (5 measurement configs), `ejerciciosMarcas.js` (12 fixed exercises)

## Key Patterns

**Auth flow:** POST `/login` returns a JWT → stored in `localStorage.token` → injected via Axios interceptor → backend validates via `get_current_user()` dependency → user role checked per-route.

**Role-based access:**
- Roles: `admin`, `coach`, `cliente`, `pendiente` (enum `RolUsuario` in `models.py`)
- Backend: route-level `Depends(_require_admin_or_coach)` or `Depends(_require_admin)` pattern in each router
- Frontend: `meta.roles` on routes + `useAuth` composable in components
- `pendiente` users are redirected to `/planes` by the router guard

**Financial movements:** Payments and sales auto-generate `movimientos_financieros` rows with `fuente = "pago_membresia"` or `"venta_tienda"`. Manual entries use `"manual"`.

**Fingerprint integration:** `asistencias` table stores entrada/salida events by `huella_id`. The bridge reads the fingerprint sensor via serial and calls `POST /asistencia/huella/{huella_id}`.

**SQLite migrations:** `backend/main.py` runs migrations on startup. New columns use `ALTER TABLE … ADD COLUMN` inside try/except. Changing nullability requires full table reconstruction (rename → CREATE → INSERT → DROP), guarded by a `PRAGMA table_info` check to avoid re-running.

**Chart lifecycle (Vue + Chart.js):** Always call `destruirChart()` before creating a new instance. Use `watch(registros, async () => { await nextTick(); await nextTick(); renderChart() })` to ensure the canvas is in the DOM after a `v-if` renders.

**Unit normalization (1RM):** All weight comparisons (PR detection, chart, esPR preview) are done in kg using `1 kg = 2.20462 lbs`. Values are converted back to the display unit (`ultimaUnidad`) only for rendering. Never compare `rm_calculado` values from different records without normalizing first.

## Mi Salud — health metrics

Per-measurement routing: each metric has its own page at `/salud/:tipo`.

**Measurement types** (defined in `frontend/src/data/saludTipos.js`):
`peso`, `altura`, `cintura`, `cuello`, `cadera`

**Backend router** (`backend/routers/salud.py`):
- `CAMPOS = { "peso": "peso_kg", "altura": "altura_cm", "cintura": "cintura_cm", "cuello": "cuello_cm", "cadera": "cadera_cm" }`
- `GET /salud/` — all records for the current user (overview)
- `GET /salud/{tipo}` — records filtered by measurement type
- `POST /salud/{tipo}` — creates a record with only that field set
- `DELETE /salud/{medida_id}` — deletes by integer ID

**Model** (`MedidaSalud` in `backend/models.py`): all measurement columns are nullable (`Optional[float]`). The `imc` column is computed by the POST endpoint when both `peso_kg` and `altura_cm` are present.

**Views:**
- `SaludView.vue` — overview; 5 RouterLink cards + IMC banner, no modal
- `SaludMedidaView.vue` — detail per tipo; Chart.js line chart, history table with delete, add modal

## Mis Marcas — 1RM personal records

Per-exercise routing: each exercise has its own page at `/marcas/:ejercicio`.

**Fixed exercise list** (defined in `frontend/src/data/ejerciciosMarcas.js`):
Back Squat, Deadlift, Clean, Clean and Jerk, Snatch, Bench Press, Press Militar, Dominadas, Push Up, Air Squat, Sit Up, Test de Léger

**1RM formulas** (7 used, averaged):
Brzycki, Epley, Lander, O'Connor, Lombardi, Mayhew, Wathen.
The average is stored as `rm_calculado` in the DB. The backend helper `_calcular_1rm(peso, reps)` lives in `backend/routers/marcas.py`.

**Backend router** (`backend/routers/marcas.py`):
- `GET /marcas/` — all records for the current user
- `GET /marcas/{ejercicio}` — records for a specific exercise (URL-encoded name)
- `POST /marcas/` — creates a record; auto-calculates `rm_calculado`
- `DELETE /marcas/{marca_id}`

**Model** (`MarcaRM` in `backend/models.py`): `usuario_id`, `ejercicio`, `peso`, `unidad` (kg/lbs), `repeticiones`, `rm_calculado`, `fecha`, `notas`.

**Views:**
- `MarcasView.vue` — grid of all 12 exercise cards; shows best 1RM and record count per exercise; no modal
- `MarcasEjercicioView.vue` — detail per exercise:
  - Summary card: last 1RM + PR + Registrar button
  - Chart.js line chart (values normalized to `ultimaUnidad`; PR points highlighted in gold)
  - Rep-max table (1–10 reps, promedio only)
  - Formula comparison section (individual result per formula + promedio footer)
  - History table with PR badge
  - Add modal: peso + unidad + reps + fecha + notas; live 1RM preview + "¡Nuevo PR!" indicator

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Required keys:
```
SECRET_KEY=
ADMIN_NOMBRE=
ADMIN_EMAIL=
ADMIN_PASSWORD=
ADMIN_TELEFONO=
ADMIN_DOCUMENTO=
```

## CORS

Backend allows origins `localhost:5173`, `localhost:5174`, `127.0.0.1:5173`, `127.0.0.1:5174`. If you add a new frontend port, update `origins` in `backend/main.py`.
