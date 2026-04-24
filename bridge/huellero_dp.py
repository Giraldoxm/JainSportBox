"""
JainSportBox – Bridge DigitalPersona U.are.U 4500
Servidor HTTP en puerto 8001.

Flujo de identificación (automático):
  Dedo en lector → captura FID → extrae FMD → compara contra templates en cache
  → si coincide y membresía vigente → POST /asistencia/por-usuario/{id}

Flujo de enrolamiento (iniciado desde la web):
  POST /enroll/{usuario_id} → captura 4 muestras → crea template de enrolamiento
  → POST /usuarios/{id}/huella-template → modo identificación

Endpoints:
  GET  /status                 – estado del dispositivo y último evento
  POST /enroll/{usuario_id}    – iniciar enrolamiento
  DELETE /enroll               – cancelar enrolamiento en curso
  POST /sim/scan/{usuario_id}  – (solo simulación) inyectar escaneo manual

Requisitos del sistema:
  - Drivers DigitalPersona One Touch para Windows
  - SDK DLLs: dpfpdd.dll, dpfj.dll (se instalan con el SDK)
  - pip install fastapi uvicorn requests python-dotenv
  - Servicio WbioSrvc de Windows debe estar detenido/deshabilitado
"""

import base64
import ctypes
import os
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Configuración ──────────────────────────────────────────────────────────────
API_BASE        = "http://127.0.0.1:8000"
BRIDGE_PORT     = 8001
SAMPLES_ENROL   = 4        # capturas para crear un template de enrolamiento
CACHE_REFRESH_S = 60       # segundos entre refresco de templates
THRESHOLD_1_N   = 2290     # disimilaridad máxima para identificación 1:N (FAR 1:100.000)

# ── Constantes SDK ─────────────────────────────────────────────────────────────
DPFPDD_SUCCESS         = 0
DPFJ_SUCCESS           = 0
DPFPDD_IMG_FMT_ANSI381 = 0x001B0401
DPFJ_FMD_ANSI378       = 0x001B0001
DPFPDD_MAX_STR_LEN     = 1024
MAX_IMG_SIZE           = 500_000
MAX_FMD_SIZE           = 10_000
DPFPDD_TIMEOUT_INF     = 0xFFFFFFFF


# ── Estructuras ctypes ─────────────────────────────────────────────────────────

class DPFPDD_DEV_INFO(ctypes.Structure):
    _fields_ = [
        ("size",    ctypes.c_uint),
        ("name",    ctypes.c_char * DPFPDD_MAX_STR_LEN),
        ("descr",   ctypes.c_char * DPFPDD_MAX_STR_LEN),
        ("id",      ctypes.c_char * DPFPDD_MAX_STR_LEN),
        ("is_open", ctypes.c_int),
    ]

class DPFPDD_CAPTURE_PARAM(ctypes.Structure):
    _fields_ = [
        ("size",       ctypes.c_uint),
        ("image_fmt",  ctypes.c_uint),
        ("image_proc", ctypes.c_uint),
        ("image_res",  ctypes.c_uint),
    ]

class DPFPDD_IMAGE_INFO(ctypes.Structure):
    _fields_ = [
        ("size",   ctypes.c_uint),
        ("width",  ctypes.c_uint),
        ("height", ctypes.c_uint),
        ("res",    ctypes.c_uint),
        ("bpp",    ctypes.c_uint),
    ]

class DPFPDD_CAPTURE_RESULT(ctypes.Structure):
    _fields_ = [
        ("size",    ctypes.c_uint),
        ("success", ctypes.c_int),
        ("quality", ctypes.c_uint),
        ("score",   ctypes.c_uint),
        ("info",    DPFPDD_IMAGE_INFO),  # struct embebido, no puntero
    ]

class DPFPDD_DEV_CAPS(ctypes.Structure):
    _fields_ = [
        ("size",                 ctypes.c_uint),
        ("can_capture_image",    ctypes.c_int),
        ("can_stream_image",     ctypes.c_int),
        ("can_extract_features", ctypes.c_int),
        ("can_match",            ctypes.c_int),
        ("can_identify",         ctypes.c_int),
        ("has_fp_storage",       ctypes.c_int),
        ("indicator_type",       ctypes.c_uint),
        ("has_pwr_mgmt",         ctypes.c_int),
        ("has_calibration",      ctypes.c_int),
        ("piv_compliant",        ctypes.c_int),
        ("resolution_cnt",       ctypes.c_uint),
        ("resolutions",          ctypes.c_uint * 16),
    ]

class DPFJ_FMD(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_uint),
    ]


# ── Estado global ──────────────────────────────────────────────────────────────

_lock = threading.Lock()

estado = {
    "dispositivo":  "iniciando",
    "modo":         "iniciando",
    "ultimo_evento": None,
    "enrolamiento": {
        "activo":         False,
        "usuario_id":     None,
        "usuario_nombre": None,
        "paso":           0,
        "total":          SAMPLES_ENROL,
        "mensaje":        "",
        "completado":     False,
        "error":          None,
    },
}

_admin_token: Optional[str] = None
_templates_cache: list = []
_last_cache_time: float = 0

_stop_event     = threading.Event()
_cancel_enrol   = threading.Event()
_sim_scan_event = threading.Event()
_sim_scan_uid: Optional[int] = None

_dpfpdd = None
_dpfj   = None
_dev    = None

# Resolución preferida (actualizada por _diagnosticar_dispositivo)
_img_res = 0


# ── Auth backend ───────────────────────────────────────────────────────────────

def _login_admin() -> Optional[str]:
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    creds = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                creds[k.strip()] = v.strip()
    email    = creds.get("ADMIN_EMAIL", "")
    password = creds.get("ADMIN_PASSWORD", "")
    if not email or not password:
        return None
    try:
        r = requests.post(
            f"{API_BASE}/login",
            data={"username": email, "password": password},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception:
        pass
    return None


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_admin_token}"} if _admin_token else {}


# ── Cache de templates ─────────────────────────────────────────────────────────

def _refrescar_cache():
    global _templates_cache, _last_cache_time
    try:
        r = requests.get(
            f"{API_BASE}/usuarios/con-template/lista",
            headers=_auth_headers(),
            timeout=5,
        )
        if r.status_code == 200:
            nuevos = []
            for u in r.json():
                try:
                    fmd = base64.b64decode(u["template"])
                    nuevos.append((u["id"], u["nombre"], fmd))
                except Exception:
                    pass
            with _lock:
                _templates_cache = nuevos
            _last_cache_time = time.time()
    except Exception:
        pass


# ── SDK DigitalPersona ─────────────────────────────────────────────────────────

def _cargar_sdk() -> bool:
    global _dpfpdd, _dpfj
    rutas = [
        Path("C:/Program Files/DigitalPersona/U.are.U SDK/Windows/Lib/x64"),
        Path("C:/Windows/System32"),
        Path(__file__).parent,
    ]
    for ruta in rutas:
        try:
            os.add_dll_directory(str(ruta))
            _dpfpdd = ctypes.CDLL(str(ruta / "dpfpdd.dll"))
            _dpfj   = ctypes.CDLL(str(ruta / "dpfj.dll"))
            print(f"[OK] SDK cargado desde: {ruta}")
            return True
        except OSError as e:
            print(f"[DEBUG] Falló {ruta}: {e}")
    return False

def _abrir_dispositivo() -> bool:
    global _dev

    # Valores reales del SDK (dpfpdd.h)
    DPFPDD_PRIORITY_COOPERATIVE = 2
    DPFPDD_PRIORITY_EXCLUSIVE   = 4

    _dpfpdd.dpfpdd_init.restype          = ctypes.c_int
    _dpfpdd.dpfpdd_query_devices.restype = ctypes.c_int
    _dpfpdd.dpfpdd_open_ext.restype      = ctypes.c_int
    _dpfpdd.dpfpdd_open_ext.argtypes     = [
        ctypes.c_char_p,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_void_p),
    ]

    rc = _dpfpdd.dpfpdd_init()
    if rc != DPFPDD_SUCCESS:
        print(f"[ERROR] dpfpdd_init falló: 0x{rc:08X}")
        return False

    cnt = ctypes.c_int(0)
    _dpfpdd.dpfpdd_query_devices(ctypes.byref(cnt), None)
    if cnt.value == 0:
        print("[ERROR] No hay lectores conectados.")
        return False

    devs = (DPFPDD_DEV_INFO * cnt.value)()
    for d in devs:
        d.size = ctypes.sizeof(DPFPDD_DEV_INFO)
    _dpfpdd.dpfpdd_query_devices(ctypes.byref(cnt), devs)

    handle = ctypes.c_void_p()
    rc = _dpfpdd.dpfpdd_open_ext(
        devs[0].name,
        DPFPDD_PRIORITY_COOPERATIVE,
        ctypes.byref(handle),
    )
    print(f"[DEBUG] dpfpdd_open_ext() = 0x{rc:08X}")
    if rc != DPFPDD_SUCCESS:
        print(f"[ERROR] dpfpdd_open_ext falló: 0x{rc:08X}")
        return False

    _dev = handle
    # Configurar argtypes de captura una sola vez
    _dpfpdd.dpfpdd_capture.restype  = ctypes.c_int
    _dpfpdd.dpfpdd_capture.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(DPFPDD_CAPTURE_PARAM),
        ctypes.c_uint,
        ctypes.POINTER(DPFPDD_CAPTURE_RESULT),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_char_p,
    ]
    print(f"[OK] Lector conectado: {devs[0].descr.decode(errors='ignore')}")
    return True


def _diagnosticar_dispositivo():
    """Lee las capabilities del lector y actualiza los parámetros de captura."""
    global _img_res

    caps = DPFPDD_DEV_CAPS()
    caps.size = ctypes.sizeof(DPFPDD_DEV_CAPS)
    _dpfpdd.dpfpdd_get_device_capabilities.restype = ctypes.c_int
    rc = _dpfpdd.dpfpdd_get_device_capabilities(_dev, ctypes.byref(caps))
    print(f"[DIAG] get_device_capabilities rc=0x{rc:08X}")
    print(f"[DIAG] can_capture_image={caps.can_capture_image} piv_compliant={caps.piv_compliant}")
    print(f"[DIAG] resolution_cnt={caps.resolution_cnt}")
    for i in range(min(caps.resolution_cnt, 16)):
        print(f"[DIAG]   res[{i}] = {caps.resolutions[i]} DPI")

    if caps.resolution_cnt > 0:
        _img_res = caps.resolutions[0]
        print(f"[DIAG] Usando res = {_img_res} DPI")


def _init_dpfj_argtypes():
    """Configura restype/argtypes de dpfj una sola vez tras cargar el SDK."""
    _dpfj.dpfj_create_fmd_from_fid.restype  = ctypes.c_int
    _dpfj.dpfj_create_fmd_from_fid.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint),
    ]
    _dpfj.dpfj_compare.restype  = ctypes.c_int
    _dpfj.dpfj_compare.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_int, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
    ]
    _dpfj.dpfj_create_enrollment_fmd.restype  = ctypes.c_int
    _dpfj.dpfj_create_enrollment_fmd.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(DPFJ_FMD), ctypes.c_uint,
        ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint),
    ]


def _capturar_fmd_sdk(timeout: int = 3000) -> Optional[bytes]:
    """Captura una huella y retorna el FMD.

    timeout=3000        en identificacion (retorna None si no hay dedo/timeout)
    timeout=0xFFFFFFFF  en enrolamiento (espera indefinidamente hasta dedo)
    """
    cap_p = DPFPDD_CAPTURE_PARAM()
    cap_p.size       = ctypes.sizeof(DPFPDD_CAPTURE_PARAM)
    cap_p.image_fmt  = DPFPDD_IMG_FMT_ANSI381
    cap_p.image_proc = 0          # DPFPDD_IMG_PROC_DEFAULT
    cap_p.image_res  = _img_res   # resolucion detectada del lector

    cap_r = DPFPDD_CAPTURE_RESULT()
    cap_r.size = ctypes.sizeof(DPFPDD_CAPTURE_RESULT)

    img_buf  = ctypes.create_string_buffer(MAX_IMG_SIZE)
    img_size = ctypes.c_uint(MAX_IMG_SIZE)

    rc = _dpfpdd.dpfpdd_capture(
        _dev,
        ctypes.byref(cap_p),
        ctypes.c_uint(timeout),
        ctypes.byref(cap_r),
        ctypes.byref(img_size),
        img_buf,
    )

    if rc != DPFPDD_SUCCESS or not cap_r.success:
        return None

    fmd_buf  = ctypes.create_string_buffer(MAX_FMD_SIZE)
    fmd_size = ctypes.c_uint(MAX_FMD_SIZE)
    rc2 = _dpfj.dpfj_create_fmd_from_fid(
        DPFPDD_IMG_FMT_ANSI381,
        img_buf, img_size.value,
        DPFJ_FMD_ANSI378,
        fmd_buf, ctypes.byref(fmd_size),
    )
    if rc2 != DPFJ_SUCCESS:
        print(f"[WARN] create_fmd_from_fid rc=0x{rc2:08X}")
        return None

    return bytes(fmd_buf.raw[: fmd_size.value])


def _crear_template_enrolamiento(muestras: list) -> Optional[bytes]:
    """Crea template de enrolamiento a partir de N FMDs de muestra."""
    n    = len(muestras)
    bufs = [ctypes.create_string_buffer(s) for s in muestras]

    arr = (DPFJ_FMD * n)()
    for i, (buf, sample) in enumerate(zip(bufs, muestras)):
        arr[i].type = DPFJ_FMD_ANSI378
        arr[i].data = ctypes.cast(buf, ctypes.c_void_p)
        arr[i].size = len(sample)

    out_buf  = ctypes.create_string_buffer(MAX_FMD_SIZE)
    out_size = ctypes.c_uint(MAX_FMD_SIZE)

    rc = _dpfj.dpfj_create_enrollment_fmd(
        DPFJ_FMD_ANSI378,
        arr, n,
        out_buf, ctypes.byref(out_size),
    )
    if rc != DPFJ_SUCCESS:
        return muestras[0]

    return bytes(out_buf.raw[: out_size.value])


def _identificar(probe: bytes) -> Optional[dict]:
    """Compara probe FMD 1:N contra todos los templates en cache."""
    with _lock:
        templates = list(_templates_cache)

    best_score = None
    best_user  = None

    for uid, nombre, tmpl in templates:
        score = ctypes.c_uint(0)
        # dpfj_compare(fmd1_type, fmd1, fmd1_size, fmd1_view,
        #              fmd2_type, fmd2, fmd2_size, fmd2_view, &score)
        rc = _dpfj.dpfj_compare(
            DPFJ_FMD_ANSI378, probe, len(probe), 0,
            DPFJ_FMD_ANSI378, tmpl,  len(tmpl),  0,
            ctypes.byref(score),
        )
        if rc == DPFJ_SUCCESS:
            if best_score is None or score.value < best_score:
                best_score = score.value
                best_user  = {"usuario_id": uid, "nombre": nombre}

    if best_score is not None and best_score <= THRESHOLD_1_N:
        return best_user
    return None


# ── Llamadas al backend ────────────────────────────────────────────────────────

def _registrar_asistencia(usuario_id: int) -> Optional[dict]:
    try:
        r = requests.post(
            f"{API_BASE}/asistencia/por-usuario/{usuario_id}",
            headers=_auth_headers(),
            timeout=5,
        )
        if r.status_code == 201:
            return r.json()
        if r.status_code == 403:
            return {"error": r.json().get("detail", "Membresía vencida")}
    except Exception as e:
        return {"error": str(e)}
    return None


def _guardar_template(usuario_id: int, fmd_bytes: bytes) -> bool:
    template_b64 = base64.b64encode(fmd_bytes).decode()
    try:
        r = requests.post(
            f"{API_BASE}/usuarios/{usuario_id}/huella-template",
            json={"template": template_b64},
            headers=_auth_headers(),
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


# ── Loop principal (hilo de fondo) ────────────────────────────────────────────

def _set_ultimo_evento(tipo: str, nombre: str, acceso: bool, detalle: str = ""):
    with _lock:
        estado["ultimo_evento"] = {
            "tipo":    tipo,
            "nombre":  nombre,
            "acceso":  acceso,
            "detalle": detalle,
            "hora":    datetime.now().strftime("%H:%M:%S"),
        }


def _loop_enrolamiento(usuario_id: int, usuario_nombre: str):
    """Captura N muestras y guarda el template de enrolamiento."""
    enrol = estado["enrolamiento"]
    muestras = []

    for paso in range(1, SAMPLES_ENROL + 1):
        if _cancel_enrol.is_set() or _stop_event.is_set():
            with _lock:
                enrol["error"]  = "Enrolamiento cancelado."
                enrol["activo"] = False
                estado["modo"]  = "identificando"
            return

        with _lock:
            enrol["paso"]    = paso
            enrol["mensaje"] = f"Coloca el dedo firmemente ({paso}/{SAMPLES_ENROL})"

        print(f"[ENROL] Muestra {paso}/{SAMPLES_ENROL} - {usuario_nombre}")
        # DPFPDD_TIMEOUT_INF: bloquea hasta que el usuario ponga el dedo.
        # dpfpdd_cancel() (llamado desde DELETE /enroll) interrumpe la espera.
        fmd = _capturar_fmd_sdk(timeout=DPFPDD_TIMEOUT_INF)

        if fmd is None:
            # Captura interrumpida (cancelación o error de calidad)
            with _lock:
                if _cancel_enrol.is_set():
                    enrol["error"] = "Enrolamiento cancelado."
                else:
                    enrol["error"] = "Huella de baja calidad. Intenta de nuevo."
                enrol["activo"] = False
                estado["modo"]  = "identificando"
            return

        muestras.append(fmd)

        if paso < SAMPLES_ENROL:
            with _lock:
                enrol["mensaje"] = "Levanta el dedo..."
            time.sleep(1.5)

    with _lock:
        enrol["mensaje"] = "Procesando huella..."

    template = _crear_template_enrolamiento(muestras)
    if template is None:
        with _lock:
            enrol["error"]  = "Error al crear el template."
            enrol["activo"] = False
            estado["modo"]  = "identificando"
        return

    ok = _guardar_template(usuario_id, template)
    if not ok:
        with _lock:
            enrol["error"]  = "Error al guardar en el servidor."
            enrol["activo"] = False
            estado["modo"]  = "identificando"
        return

    _refrescar_cache()

    with _lock:
        enrol["completado"] = True
        enrol["mensaje"]    = f"Huella de {usuario_nombre} registrada correctamente."
        enrol["activo"]     = False
        estado["modo"]      = "identificando"

    print(f"[OK] Enrolamiento completado para {usuario_nombre}.")


def _hilo_principal():
    """Hilo de fondo que maneja identificación y enrolamiento."""
    global _admin_token

    print("[INFO] Conectando con el backend...")
    for _ in range(10):
        _admin_token = _login_admin()
        if _admin_token:
            print("[OK] Autenticado con el backend.")
            break
        time.sleep(2)
    else:
        print("[WARN] No se pudo autenticar. El bridge funcionará sin token.")

    _refrescar_cache()

    sim = False
    if _cargar_sdk():
        if _abrir_dispositivo():
            _init_dpfj_argtypes()
            _diagnosticar_dispositivo()
            with _lock:
                estado["dispositivo"] = "conectado"
                estado["modo"]        = "identificando"
        else:
            print("[WARN] No se pudo abrir el dispositivo. Modo simulación.")
            sim = True
    else:
        print("[WARN] SDK no encontrado. Modo simulación.")
        sim = True

    if sim:
        with _lock:
            estado["dispositivo"] = "simulacion"
            estado["modo"]        = "esperando"
        _loop_simulacion()
        return

    # Loop real
    while not _stop_event.is_set():
        modo_actual = estado.get("modo")

        if modo_actual == "identificando":
            fmd = _capturar_fmd_sdk()
            if fmd is None:
                time.sleep(0.3)
                continue

            if time.time() - _last_cache_time > CACHE_REFRESH_S:
                _refrescar_cache()

            usuario = _identificar(fmd)
            if usuario is None:
                _set_ultimo_evento("desconocido", "Huella no reconocida", False, "Sin coincidencia")
                print("[DENEGADO] Huella no reconocida.")
                continue

            resultado = _registrar_asistencia(usuario["usuario_id"])
            if resultado and "error" in resultado:
                _set_ultimo_evento("entrada", usuario["nombre"], False, resultado["error"])
                print(f"[DENEGADO] {usuario['nombre']}: {resultado['error']}")
            elif resultado:
                tipo = resultado.get("tipo", "entrada")
                _set_ultimo_evento(tipo, usuario["nombre"], True)
                print(f"[OK] {tipo.upper()} - {usuario['nombre']}")

        elif modo_actual == "enrolando":
            with _lock:
                uid    = estado["enrolamiento"]["usuario_id"]
                nombre = estado["enrolamiento"]["usuario_nombre"]
            _loop_enrolamiento(uid, nombre)

        else:
            time.sleep(0.2)


def _loop_simulacion():
    """Modo simulación: espera eventos inyectados por /sim/scan."""
    print("[SIM] Modo simulación activo. Usa POST /sim/scan/{usuario_id} para simular.")
    while not _stop_event.is_set():
        if estado["modo"] == "enrolando":
            with _lock:
                uid    = estado["enrolamiento"]["usuario_id"]
                nombre = estado["enrolamiento"]["usuario_nombre"]
            _sim_enrolamiento(uid, nombre)
            continue

        if _sim_scan_event.wait(timeout=0.5):
            _sim_scan_event.clear()
            uid = _sim_scan_uid
            if uid is not None:
                resultado = _registrar_asistencia(uid)
                nombre = "Usuario simulado"
                with _lock:
                    for tmpl_uid, tmpl_nombre, _ in _templates_cache:
                        if tmpl_uid == uid:
                            nombre = tmpl_nombre
                            break
                if resultado and "error" in resultado:
                    _set_ultimo_evento("entrada", nombre, False, resultado["error"])
                elif resultado:
                    _set_ultimo_evento(resultado.get("tipo", "entrada"), nombre, True)


def _sim_enrolamiento(usuario_id: int, usuario_nombre: str):
    """Enrolamiento simulado: genera un template falso."""
    enrol = estado["enrolamiento"]
    for paso in range(1, SAMPLES_ENROL + 1):
        if _cancel_enrol.is_set():
            with _lock:
                enrol["error"]  = "Cancelado."
                enrol["activo"] = False
                estado["modo"]  = "esperando"
            return
        with _lock:
            enrol["paso"]    = paso
            enrol["mensaje"] = f"Simulando captura {paso}/{SAMPLES_ENROL}..."
        time.sleep(2)

    import os as _os
    template_falso = _os.urandom(512)
    ok = _guardar_template(usuario_id, template_falso)

    with _lock:
        if ok:
            enrol["completado"] = True
            enrol["mensaje"]    = f"[SIM] Huella de {usuario_nombre} guardada."
        else:
            enrol["error"]  = "Error al guardar en el servidor."
        enrol["activo"] = False
        estado["modo"]  = "esperando"

    _refrescar_cache()


# ── FastAPI ────────────────────────────────────────────────────────────────────

app = FastAPI(title="JainSportBox – Bridge DP4500", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
def get_status():
    with _lock:
        return {
            "dispositivo":        estado["dispositivo"],
            "modo":               estado["modo"],
            "ultimo_evento":      estado["ultimo_evento"],
            "enrolamiento":       dict(estado["enrolamiento"]),
            "templates_en_cache": len(_templates_cache),
        }


@app.post("/enroll/{usuario_id}")
def iniciar_enrolamiento(usuario_id: int, nombre: str = ""):
    with _lock:
        if estado["enrolamiento"]["activo"]:
            return {"error": "Ya hay un enrolamiento en curso."}

        _cancel_enrol.clear()
        enrol = estado["enrolamiento"]
        enrol["activo"]         = True
        enrol["usuario_id"]     = usuario_id
        enrol["usuario_nombre"] = nombre or f"Usuario #{usuario_id}"
        enrol["paso"]           = 0
        enrol["mensaje"]        = "Iniciando enrolamiento..."
        enrol["completado"]     = False
        enrol["error"]          = None
        estado["modo"]          = "enrolando"

    return {"mensaje": "Enrolamiento iniciado.", "usuario_id": usuario_id}


@app.delete("/enroll")
def cancelar_enrolamiento():
    _cancel_enrol.set()
    if _dev and _dpfpdd:
        try:
            _dpfpdd.dpfpdd_cancel(_dev)
        except Exception:
            pass
    with _lock:
        estado["enrolamiento"]["activo"] = False
        estado["enrolamiento"]["error"]  = "Cancelado por el usuario."
        modo = "identificando" if estado["dispositivo"] == "conectado" else "esperando"
        estado["modo"] = modo
    return {"mensaje": "Enrolamiento cancelado."}


@app.post("/sim/scan/{usuario_id}")
def sim_scan(usuario_id: int):
    global _sim_scan_uid
    if estado["dispositivo"] != "simulacion":
        return {"error": "El dispositivo real está conectado. Este endpoint es solo para simulación."}
    _sim_scan_uid = usuario_id
    _sim_scan_event.set()
    return {"mensaje": f"Escaneo simulado para usuario #{usuario_id}."}


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    hilo = threading.Thread(target=_hilo_principal, daemon=True)
    hilo.start()

    print("=" * 55)
    print("  JainSportBox - Bridge DigitalPersona U.are.U 4500")
    print(f"  API Bridge: http://localhost:{BRIDGE_PORT}")
    print(f"  Backend:    {API_BASE}")
    print("=" * 55)

    try:
        uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT, log_level="warning")
    finally:
        _stop_event.set()
        if _dev and _dpfpdd:
            try:
                _dpfpdd.dpfpdd_close(_dev)
                _dpfpdd.dpfpdd_exit()
            except Exception:
                pass