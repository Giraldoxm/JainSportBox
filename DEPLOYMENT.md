# Plan de Despliegue — JainSportBox

Despliegue de JainSportBox como **página web pública (PWA instalable)** con **estación de huella local** en el gym.

**Escenario elegido:**
- **Alcance:** Mixto — clientes entran por internet + estación de huella/recepción en la PC del gym.
- **Hosting backend:** **Render Starter** ($7/mes). El sistema se vende a un gimnasio, y el plan Hobby de Railway es explícitamente **no-comercial** (Pro son $20/mes con crédito que no se acumula, para un consumo real de ~$3). Los planes free que suspenden el proceso quedan descartados: la primera huella del día esperaría el cold start y la palanquera no abriría a tiempo.
- **Base de datos:** **Postgres en Supabase**, plan free (permite uso comercial).
- **Fotos:** **Supabase Storage** vía protocolo S3.

**Costo total: ~$7/mes (~28k COP).**

---

## Arquitectura objetivo

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│  Clientes (celular/web) │  HTTPS  │  Frontend PWA (Vercel/Netlify)│
│  instalan la PWA        │────────▶│  app.tudominio.com            │
└─────────────────────────┘         └───────────────┬──────────────┘
                                                     │ HTTPS (axios)
                                                     ▼
                                     ┌──────────────────────────────┐
                                     │  Backend FastAPI (Render)     │
                                     │  jainsportbox-api.onrender.com│
                                     └───────┬───────────────▲──────┘
                                             │ SSL            │ HTTPS
                                             ▼                │
                              ┌──────────────────────────┐    │
                              │  Supabase (plan free)     │    │
                              │  • Postgres (session pool)│    │
                              │  • Storage (fotos, S3)    │    │
                              └──────────────────────────┘    │
                       ┌─────────────────────────────────────┴───────┐
                       │  PC del gym (recepción)                       │
                       │  • Bridge .NET (huella + Arduino) → cloud API │
                       │  • Frontend LOCAL en http://localhost (huella)│
                       │  • backup-db.ps1 diario → OneDrive            │
                       └───────────────────────────────────────────────┘
```

**Razón del diseño "doble entrega" del frontend:** un navegador con página `https://` **no puede** llamar a `http://localhost:8001` (bloqueo *mixed content*). La estación de huella corre una copia **local** del frontend en `http://localhost`, que sí puede hablar con el bridge (`http://localhost` → `http://localhost`) y con el backend cloud (`http://localhost` → `https://api`, permitido). Los clientes usan la PWA en la nube y nunca tocan el bridge.

---

## Capa 1 — Base de datos (PostgreSQL)

Base de todo lo demás. Se hace y prueba en local con Postgres en Docker antes de subir nada.

### 1.1 `backend/database.py` — leer `DATABASE_URL` del entorno
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///crossfit.db")
# Railway entrega "postgres://"; SQLAlchemy 2.x exige "postgresql+psycopg://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 1.2 `backend/requirements.txt`
- Añadir `psycopg[binary]`.

### 1.3 `backend/main.py` — guard de migraciones SQLite
Las migraciones de arranque son 100% SQLite (`PRAGMA`, reconstrucción de tablas, `ALTER TABLE … ADD COLUMN`). En Postgres revientan. Envolver **todo el bloque**:
```python
if engine.url.get_backend_name() == "sqlite":
    # ... todo el bloque actual de ALTER TABLE + PRAGMA + reconstrucción ...
```
En Postgres fresco no hace falta: `Base.metadata.create_all()` ya crea el esquema final con la nulabilidad correcta (los modelos reflejan el estado final).

### 1.4 (Opcional, recomendado) Alembic
Para cambios de esquema **futuros** en Postgres, introducir Alembic en vez de seguir con el patrón de `ALTER TABLE` en el arranque.

**Entregable de la capa:** backend corriendo local contra Postgres en Docker, esquema creado, login admin funcional.

---

## Capa 2 — Migración de datos (SQLite → Postgres)

Script Python de una sola corrida:
1. `create_all()` en Postgres.
2. Dos sesiones SQLAlchemy: lee de SQLite, escribe en Postgres.
3. Copiar tablas respetando el orden de claves foráneas.
4. Resetear las secuencias de IDs (`setval`) al final.

> ~60 líneas. Se ejecuta una sola vez para llevar los datos de producción actuales.

**Entregable de la capa:** datos actuales (usuarios, pagos, marcas, etc.) visibles en Postgres.

---

## Capa 3 — Backend en Render + datos en Supabase

### 3.1 Conexión a Supabase — usar el **session pooler**

En Supabase: *Connect → Session pooler* (puerto **5432**). **No** usar el transaction pooler (6543): `_debo_correr_scheduler()` en `backend/main.py` toma un `pg_try_advisory_lock` **a nivel de sesión** sobre una conexión persistente, y el modo transaction lo liberaría al terminar cada consulta (además de romper los prepared statements de psycopg3). El pooler también resuelve que la conexión directa de Supabase sea IPv6-only.

`backend/database.py` normaliza la URI a `postgresql+psycopg://` y le agrega `sslmode=require` (el default de psycopg es `prefer`, que aceptaría caer a texto plano). El pool está dimensionado para el free tier: `DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=2`, `pool_recycle=300`.

### 3.2 Comando de arranque

Sale del `CMD` del `Dockerfile`: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`. **1 worker** porque Render Starter da 0.5 CPU / 512 MB; además mantiene chico el pool contra Supabase y evita que los jobs de APScheduler se dupliquen.

### 3.3 Variables de entorno en Render
| Variable | Origen |
|---|---|
| `DATABASE_URL` | URI del **session pooler** de Supabase |
| `SECRET_KEY` | **la misma que tenía Railway**, o se invalidan los JWT vigentes y todos los socios quedan deslogueados |
| `ADMIN_NOMBRE`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_TELEFONO`, `ADMIN_DOCUMENTO` | seed admin |
| `BRIDGE_SECRET` | clave compartida con el bridge |
| `CORS_ORIGINS` | dominios del frontend, sin barra final |
| `S3_*` (6) | Supabase Storage, ver 3.4 |

Todas van con `sync: false` en `render.yaml` — se cargan a mano en el dashboard para que ningún secreto quede en git.

### 3.4 Almacenamiento de `/uploads` (fotos de perfil) — Supabase Storage
El filesystem de Render es **efímero** (se borra en cada deploy → se pierden las fotos), así que las fotos van a object storage.

Implementado en `backend/storage.py`: abstracción `guardar_archivo()` / `eliminar_archivo()` usada por los routers `usuarios`, `auth` (registro) y `productos`. Si `S3_BUCKET` está definido sube al bucket vía boto3; si no, cae al filesystem local (dev). Como Supabase Storage expone endpoint **S3-compatible**, funciona sin cambios de código — solo variables de entorno. `eliminar_archivo()` tolera URLs de ambos backends, así que los registros viejos se siguen pudiendo borrar tras migrar.

Dos detalles que rompen si se pasan por alto:
- El bucket debe crearse **público**, o las fotos devuelven 400 en el navegador.
- `S3_REGION` debe ser la **región real del proyecto**; `"auto"` solo valía para R2.

### 3.5 Archivos de despliegue (raíz del repo)
- `render.yaml` — blueprint: `runtime: docker`, `plan: starter`, `healthCheckPath: /`, env vars con `sync: false`.
- `Dockerfile` — imagen del backend. Explícito para que el autodetector no vea el proyecto .NET de `servicio_biometrico/` y corra `dotnet restore`.
- `railway.toml` — **legado**, se borra cuando Railway se apague definitivamente.

**Entregable de la capa:** `https://<app>.onrender.com/docs` accesible, login funcional contra Supabase.

---

## Capa 3-bis — Migración Railway → Render + Supabase (una sola vez)

1. **Crear el proyecto Supabase** (región más cercana a Colombia) y guardar la contraseña de la DB.
2. **Volcar Railway** (conexión directa, no el pooler):
   ```
   pg_dump "<RAILWAY_URL>" --schema=public --no-owner --no-privileges --clean --if-exists -Fc -f jsb.dump
   ```
3. **Restaurar en Supabase**:
   ```
   pg_restore --no-owner --no-privileges -d "<SUPABASE_URL>" jsb.dump
   ```
   `--no-owner --no-privileges` es obligatorio: el rol `postgres` de Supabase no puede asignar ownership de Railway.
4. **Verificar conteos** por tabla (`usuarios`, `pagos`, `asistencias`, `marcas_rm`, `movimientos_financieros`) contra el origen antes de seguir.
5. **Archivos:** si las fotos estaban en R2, copiar los objetos a Supabase conservando el prefijo `uploads/` y reescribir las URLs guardadas — `UPDATE usuarios SET foto_url = replace(foto_url, '<viejo>', '<nuevo>')`, ídem `productos`. Son las dos únicas columnas de archivos.
6. **Cutover:** `VITE_API_URL` en Netlify → URL de Render; `JSB_API_BASE` en la PC del gym → URL de Render (ver Capa 5.1); `start-estacion.ps1 -ApiUrl <URL>`.
7. **No apagar Railway todavía** — dejarlo vivo unos días como rollback.

Las migraciones de arranque de `main.py` (`ADD COLUMN IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`) son idempotentes y corren solas en el primer arranque. No hay nada que adaptar.

---

## Capa 4 — Frontend web + PWA (Vercel/Netlify)

### 4.1 Base URL por entorno — `frontend/src/api.js`
```js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
})
```
- `.env.production` (build cloud): `VITE_API_URL=https://api.tudominio.com`
- `.env.local` (estación de huella): `VITE_API_URL=https://api.tudominio.com`

### 4.2 Configuración del host (Vercel/Netlify)
- Build command: `npm run build`
- Output dir: `dist/`
- **Rewrite SPA:** todas las rutas → `index.html` (para que el router de Vue no rompa al recargar).

### 4.3 PWA — `vite-plugin-pwa`
```js
// vite.config.js
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [vue(), VitePWA({
    registerType: 'autoUpdate',
    includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
    manifest: {
      name: 'JainSportBox', short_name: 'JainBox',
      theme_color: '#dc2626', background_color: '#ffffff',
      display: 'standalone', start_url: '/',
      icons: [
        { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
        { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
        { src: 'pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      navigateFallback: '/index.html',
      runtimeCaching: [{
        urlPattern: ({ url }) => url.origin === 'https://api.tudominio.com',
        handler: 'NetworkFirst',           // datos frescos, fallback offline
        options: { cacheName: 'api', networkTimeoutSeconds: 5 },
      }],
    },
  })],
})
```

### 4.4 Consideraciones PWA para esta app
- **No cachear** `/login` ni respuestas con token → usar `NetworkFirst`, nunca `CacheFirst` en la API.
- La PWA solo es **instalable sobre HTTPS** (por eso el frontend cloud va con dominio + TLS).
- Generar íconos `pwa-192.png`, `pwa-512.png`, `apple-touch-icon.png`.
- (Opcional) Botón "Instalar app" capturando el evento `beforeinstallprompt`.

### 4.5 Estado — ✅ IMPLEMENTADO
- `frontend/src/api.js` — `baseURL` por `VITE_API_URL` + helper `mediaUrl()` (resuelve fotos: absolutas de S3/R2 tal cual, locales con base del backend). Aplicado en `TiendaView`, `UsuariosView`, `UsuarioPerfilView`.
- `frontend/vite.config.js` — `vite-plugin-pwa` (autoUpdate). El origin del API se lee con `loadEnv` y se hornea como RegExp en el SW (NetworkFirst, no CacheFirst). Verificado en build: `registerRoute(/^https:\/\/api…/, NetworkFirst)`.
- Íconos generados en `frontend/public/`: `pwa-192.png`, `pwa-512.png`, `apple-touch-icon.png`, `favicon.ico` (rojo de marca).
- `index.html` — favicon, apple-touch-icon, theme-color, título.
- Config de host: `frontend/vercel.json` (rewrite SPA) y `netlify.toml` (base/publish + redirect SPA).
- `frontend/.env.example` documenta `VITE_API_URL`. Valores reales en el dashboard del host o `.env.production`/`.env.local` (gitignored).

**Pendiente (acción externa):** setear `VITE_API_URL` con el dominio real del API en Vercel/Netlify una vez exista (decisión de dominio aún abierta).

**Entregable de la capa:** `https://app.tudominio.com` instalable como app en Android/iOS, conectada al backend cloud.

---

## Capa 5 — Bridge biométrico (.NET, PC del gym)

### 5.1 Apuntar al backend cloud — ✅ IMPLEMENTADO
`ApiBase` y `BridgeSecret` estaban hardcodeados en `FingerprintCapture.cs` y `HttpApi.cs`. Se centralizaron en **`servicio_biometrico/BridgeConfig.cs`**, que los lee de variables de entorno con default local:
```csharp
public static readonly string ApiBase =
    (Environment.GetEnvironmentVariable("JSB_API_BASE") ?? "<backend de producción>").TrimEnd('/');
public static readonly string BridgeSecret =
    Environment.GetEnvironmentVariable("BRIDGE_SECRET") ?? "jain_bridge_secret_2024";
```
Ambos archivos ahora referencian `BridgeConfig.*` (fuente única, sin riesgo de desincronizar el secreto). Compila OK (verificado vía `dotnet build`).

**Configurar en la PC del gym** (env vars de máquina, requieren reabrir la sesión/proceso):
```powershell
setx JSB_API_BASE "https://<app>.onrender.com" /M
setx BRIDGE_SECRET "<mismo valor que el backend>" /M
```

> **Al migrar de host:** `ApiBase` es `static readonly` — se lee **una sola vez al arrancar**, así que hay que **reiniciar el bridge**. Confirmar en `bridge.log` la línea `[CONFIG] ApiBase`. Y actualizar también el default hardcodeado en `BridgeConfig.cs`, o una compilación limpia sin la env var apuntaría al backend viejo (ya apagado).

### 5.2 Notas
- El bridge sigue exponiendo `localhost:8001` (HTTP API) y `localhost:8765` (WebSocket) para la estación local.
- El header `X-Bridge-Secret` viaja igual contra el cloud → **debe ser HTTPS** para no mandar el secreto en claro (por eso `JSB_API_BASE` debe ser `https://`).
- El bridge sigue corriendo como Administrador (acceso al driver USB) en la PC del gym.
- Recompilar requiere detener el bridge en ejecución (bloquea `bin\Debug\net48\HuelleroBridge.exe`).

**Entregable de la capa:** enrolamiento y verificación de huella funcionando contra el backend cloud.

---

## Capa 6 — Estación de huella local (recepción) — ✅ IMPLEMENTADO

Resuelve el bloqueo *mixed content*: una página `http://localhost` sí puede llamar al bridge (`http://localhost:8001`, mismo esquema) y al backend cloud (`http→https` permitido). Los clientes usan la PWA en la nube y nunca tocan esta ruta.

**Launcher `start-estacion.ps1`** (raíz; wrapper `start-estacion.cmd`):
```powershell
.\start-estacion.ps1 -ApiUrl https://api.tudominio.com
```
Hace: `npm install` (si falta) → `npm run build` con `VITE_API_URL` → sirve `dist/` con `vite preview` en `http://localhost:80` (fallback SPA incluido) → arranca el bridge si no corre.

Flags: `-Port <n>` (default 80; 80 requiere admin), `-SkipBuild` (sirve el `dist/` existente), `-NoBridge`. Si `VITE_API_URL` no es HTTPS, avisa (el `X-Bridge-Secret` viajaría en claro).

Verificado: `vite preview` sirve `/`, deep routes (`/usuarios` → 200 vía fallback SPA), `sw.js` y `manifest.webmanifest`.

- El recepcionista abre `http://localhost` en el navegador de la PC del gym.
- Los URLs del bridge (`localhost:8001`, `ws://localhost:8765`) ya están fijados a local en el frontend; el resto de llamadas van al API cloud (`VITE_API_URL`).

**Entregable de la capa:** flujo completo de recepción (marcar huella → abre palanquera → registra asistencia en cloud) operativo.

---

## Capa 7 — Respaldo de la base de datos

El plan free de Supabase **no ofrece point-in-time recovery ni restauración bajo demanda garantizada**. Para datos de un cliente que paga (pagos, membresías, asistencias) hace falta una copia que no dependa del proveedor.

**Dónde corre:** la PC de recepción del gym, ya encendida 24/7 para el bridge. Cuesta $0 y no agrega servicios al despliegue (un cron job en Render sería un servicio aparte con costo extra).

**`backup-db.ps1`** (raíz del repo): `pg_dump -Fc` del esquema `public` → carpeta en **OneDrive**, que al sincronizar deja el respaldo fuera del sitio sin pagar almacenamiento. Nombre con timestamp, **retención de los últimos 14**, log propio. Descarta dumps de menos de 1 KB en vez de rotar sobre ellos (un dump vacío no debe pisar copias buenas).

```powershell
.\backup-db.ps1                          # usa JSB_BACKUP_URL y OneDrive
.\backup-db.ps1 -DestDir D:\Backups -Retener 30
```

**Requisitos:**
- Client tools de PostgreSQL instaladas (`pg_dump` / `pg_restore`); no vienen con Windows. El script las busca en el PATH y en `C:\Program Files\PostgreSQL\*\bin\`.
- Variable de entorno de sistema `JSB_BACKUP_URL` con la URI de Supabase. **Nunca** dentro del script: ese archivo va a git.
  ```powershell
  setx JSB_BACKUP_URL "postgresql://postgres.<ref>:<pwd>@aws-1-<region>.pooler.supabase.com:5432/postgres" /M
  ```

**Agendarlo:** Task Scheduler, diario 3 AM (fuera del horario del gym), con *"ejecutar aunque el usuario no haya iniciado sesión"* y *"ejecutar apenas sea posible si se perdió una ejecución programada"* (cubre que la PC estuviera apagada):
```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<ruta>\backup-db.ps1"
```

**Restaurar:**
```
pg_restore --no-owner --no-privileges -d "<URI destino>" jsb-YYYYMMDD.dump
```

> Un backup que nunca se restauró no es un backup. Probar la restauración **una vez, de entrada**, contra un proyecto Supabase descartable, y comparar conteos de tablas.

**Entregable de la capa:** dump diario en OneDrive, con la restauración verificada al menos una vez.

---

## Orden de ejecución recomendado

| # | Capa | Depende de |
|---|---|---|
| 1 | Base de datos (Postgres) | — |
| 2 | Migración de datos | Capa 1 |
| 3 | Backend en la nube | Capas 1–2 |
| 4 | Frontend web + PWA | Capa 3 |
| 5 | Bridge biométrico | Capa 3 |
| 6 | Estación de huella local | Capas 4–5 |
| 7 | Respaldo de la base | Capa 3 |

---

## Decisiones pendientes

1. ~~**Fotos de perfil (`/uploads`):**~~ ✅ RESUELTO → object storage (Supabase Storage, ver Capa 3.4).
2. **Dominio:** ¿dominio propio, o los subdominios gratis de Render/Netlify al inicio?
3. **Alembic:** ¿introducirlo ahora (capa 1.4) o dejar el patrón actual de migraciones?

---

## Límites del plan free de Supabase (a vigilar)

- **500 MB de base** y **1 GB de Storage**. Holgados para un box, pero las fotos de perfil admiten hasta 5 MB c/u: conviene revisar el consumo cada tanto.
- **5 GB de egress/mes.**
- **Pausa tras 7 días sin actividad.** No aplica mientras el backend corra: `_job_reset_gym` consulta la DB cada 3 minutos. Sí aplicaría si el gimnasio cierra una semana y se apaga el servicio — se despausa a mano desde el dashboard.

---

## Notas de seguridad

- Forzar **HTTPS** en backend y frontend (TLS automático en Render/Netlify).
- La conexión a Supabase va con `sslmode=require` (forzado en `database.py`).
- `BRIDGE_SECRET` y `SECRET_KEY` solo en variables de entorno, nunca en el repo.
- Revisar que CORS no quede en `*` en producción.
- El bridge habla con el cloud por HTTPS para proteger `X-Bridge-Secret`.
