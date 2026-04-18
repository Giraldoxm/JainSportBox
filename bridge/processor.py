"""
Bridge Processor - Puente entre el sensor de huella y el backend FastAPI.

Modos de operacion:
  - SERIAL: Lee IDs de huella desde un puerto COM (ej. COM3 con Arduino).
  - SIMULACION: Lee IDs desde el teclado para pruebas sin hardware.

Flujo:
  1. Recibe un huella_id.
  2. GET /usuarios/huella/{huella_id} -> busca al usuario.
  3. Valida membresia vigente.
  4. Si OK -> POST /asistencia/ y muestra ACCESO CONCEDIDO.
  5. Si falla -> muestra el motivo (Vencido / No encontrado).
"""

import sys
import time
from datetime import date

import requests

# ─── Configuracion ───────────────────────────────────────────

API_BASE = "http://127.0.0.1:8000"
SERIAL_PORT = "COM3"
SERIAL_BAUD = 9600
SERIAL_TIMEOUT = 1  # segundos


# ─── Intentar conexion serial ────────────────────────────────

def intentar_serial():
    """Intenta abrir el puerto serial. Retorna el objeto o None."""
    try:
        import serial
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
        print(f"[SERIAL] Conectado a {SERIAL_PORT} a {SERIAL_BAUD} baudios")
        return ser
    except ImportError:
        print("[WARN] pyserial no esta instalado. Usando modo simulacion.")
        return None
    except Exception as e:
        print(f"[WARN] No se pudo abrir {SERIAL_PORT}: {e}")
        print("[INFO] Cambiando a modo simulacion (teclado).")
        return None


# ─── Procesar huella ─────────────────────────────────────────

def procesar_huella(huella_id: str):
    """
    Busca al usuario por huella, valida membresia y registra asistencia.
    Retorna True si el acceso fue concedido, False en caso contrario.
    """
    huella_id = huella_id.strip()
    if not huella_id:
        return False

    print(f"\n{'='*50}")
    print(f"  Huella detectada: {huella_id}")
    print(f"{'='*50}")

    # 1) Buscar usuario por huella
    try:
        resp = requests.get(f"{API_BASE}/usuarios/huella/{huella_id}", timeout=5)
    except requests.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor. Verifica que el backend este corriendo.")
        return False
    except requests.Timeout:
        print("[ERROR] Timeout al conectar con el servidor.")
        return False

    if resp.status_code == 404:
        print("[ACCESO DENEGADO] Usuario NO ENCONTRADO con esa huella.")
        return False

    if resp.status_code != 200:
        print(f"[ERROR] Respuesta inesperada del servidor: {resp.status_code}")
        return False

    usuario = resp.json()
    nombre = usuario.get("nombre", "Desconocido")
    fecha_venc = usuario.get("fecha_vencimiento")

    # 2) Validar membresia
    if not fecha_venc:
        print(f"[ACCESO DENEGADO] {nombre} no tiene un plan asignado.")
        return False

    fecha_venc_date = date.fromisoformat(fecha_venc)
    if fecha_venc_date < date.today():
        print(f"[ACCESO DENEGADO] Membresia VENCIDA para {nombre}.")
        print(f"  Fecha de vencimiento: {fecha_venc}")
        print(f"  Debe renovar su plan para poder ingresar.")
        return False

    # 3) Registrar asistencia
    try:
        resp_asist = requests.post(
            f"{API_BASE}/asistencia/",
            json={"huella_id": huella_id},
            timeout=5,
        )
    except requests.ConnectionError:
        print("[ERROR] No se pudo registrar la asistencia (sin conexion).")
        return False

    if resp_asist.status_code == 201:
        data = resp_asist.json()
        tipo = data.get("tipo", "entrada")
        print(f"  >>> ACCESO CONCEDIDO <<<")
        print(f"  Usuario: {nombre}")
        print(f"  Tipo:    {tipo.upper()}")
        print(f"  Vence:   {fecha_venc}")
        return True
    else:
        print(f"[ERROR] No se pudo registrar asistencia: {resp_asist.status_code}")
        print(f"  Detalle: {resp_asist.text}")
        return False


# ─── Loop principal ──────────────────────────────────────────

def loop_serial(ser):
    """Lee continuamente del puerto serial."""
    print("\n[SERIAL] Esperando lectura de huellas...")
    print("  (Presiona Ctrl+C para salir)\n")

    while True:
        try:
            linea = ser.readline().decode("utf-8", errors="ignore").strip()
            if linea:
                procesar_huella(linea)
        except KeyboardInterrupt:
            print("\n[INFO] Deteniendo procesador...")
            break
        except Exception as e:
            print(f"[ERROR] Error leyendo serial: {e}")
            time.sleep(1)


def loop_simulacion():
    """Modo simulacion: lee IDs de huella desde el teclado."""
    print("\n" + "="*50)
    print("  MODO SIMULACION (sin hardware)")
    print("  Escribe un huella_id y presiona Enter.")
    print("  Escribe 'salir' para terminar.")
    print("="*50 + "\n")

    while True:
        try:
            huella_id = input("[SIM] huella_id > ")
            if huella_id.strip().lower() in ("salir", "exit", "q"):
                print("[INFO] Cerrando procesador...")
                break
            procesar_huella(huella_id)
        except (KeyboardInterrupt, EOFError):
            print("\n[INFO] Deteniendo procesador...")
            break


# ─── Main ────────────────────────────────────────────────────

def main():
    print("="*50)
    print("  CrossFit Box - Bridge Processor v1.0")
    print("  Puente Sensor de Huella <-> Backend API")
    print("="*50)

    ser = intentar_serial()

    if ser:
        try:
            loop_serial(ser)
        finally:
            ser.close()
            print("[SERIAL] Puerto cerrado.")
    else:
        loop_simulacion()


if __name__ == "__main__":
    main()
