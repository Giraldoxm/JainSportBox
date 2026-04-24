# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JainSportBox is a CrossFit Box Management System with a Python/FastAPI backend and Vue.js 3 frontend. It handles members, memberships, attendance (via fingerprint sensor), WODs, finances, health metrics, and a product shop.

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
- `backend/main.py` — FastAPI app creation, CORS config, router registration, APScheduler setup (daily membership alerts at 9 AM Bogotá time)
- `backend/models.py` — All SQLAlchemy models (11 tables)
- `backend/database.py` — SQLite session factory
- `backend/security.py` — BCrypt password hashing, JWT creation/validation (HS256, 7-day expiry)
- `backend/routers/` — One file per domain: `auth`, `usuarios`, `pagos`, `planes`, `productos`, `ventas`, `wods`, `asistencia`, `finanzas`, `salud`, `alertas`
- `backend/schemas/` — Pydantic request/response models mirroring each router domain
- `backend/seed.py` — Creates default plans and admin user (runs on app startup via `main.py`)

**Frontend layout:**
- `frontend/src/main.js` — Vue app init; Axios interceptor adds `Authorization: Bearer {token}` from `localStorage`
- `frontend/src/api.js` — Axios instance with `baseURL: http://127.0.0.1:8000`
- `frontend/src/router/index.js` — Route guards using `meta.requiresAuth` and `meta.roles`; clients default to `/wods`, admin/coach to `/usuarios`
- `frontend/src/composables/useAuth.js` — Reactive role helpers: `isAdmin`, `isCoach`, `isCliente`, `canManage`
- `frontend/src/views/` — One large SFC per page (LoginView, UsuariosView, TiendaView, WodsView, FinanzasView, SaludView, AlertasView, MonitorAccesoView, PlanesView)
- `frontend/src/components/Dashboard.vue` — Main layout shell (sidebar + navigation)

## Key Patterns

**Auth flow:** POST `/login` returns a JWT → stored in `localStorage.token` → injected via Axios interceptor → backend validates via `get_current_user()` dependency → user role checked per-route.

**Role-based access:**
- Roles: `admin`, `coach`, `cliente` (enum `RolUsuario` in `models.py`)
- Backend: route-level `Depends(_require_admin_or_coach)` or `Depends(_require_admin)` pattern in each router
- Frontend: `meta.roles` on routes + `useAuth` composable in components

**Financial movements:** Payments and sales auto-generate `movimientos_financieros` rows with `fuente = "pago_membresia"` or `"venta_tienda"`. Manual entries use `"manual"`.

**Fingerprint integration:** `asistencias` table stores entrada/salida events by `huella_id`. The bridge reads the fingerprint sensor via serial and calls `POST /asistencia/huella/{huella_id}`.

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
