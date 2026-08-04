"""
Almacenamiento de archivos subidos (fotos de perfil y de productos).

Dos backends, elegidos por entorno:
  • Object storage S3-compatible (Cloudflare R2 / AWS S3) — si S3_BUCKET está
    definido. Necesario en la nube porque el filesystem de Railway/Render es
    efímero (se borra en cada deploy).
  • Filesystem local (carpeta backend/uploads) — fallback para desarrollo.

La elección es transparente para los routers: usan guardar_archivo() y
eliminar_archivo() sin saber qué backend hay detrás.

Toda imagen se guarda normalizada: redimensionada y re-encodeada a WebP. Las URLs
viejas (.jpg/.png) siguen sirviéndose sin cambios; la normalización aplica a lo
que se sube de ahora en más.

URLs almacenadas en la BD:
  • Local: ruta relativa "/uploads/...". El backend la sirve vía StaticFiles.
  • S3/R2: URL pública absoluta "https://.../uploads/...".
eliminar_archivo() reconoce ambos formatos, así que los registros antiguos
(creados en local) se siguen pudiendo borrar tras migrar a S3.

Variables de entorno (S3/R2):
  S3_BUCKET            nombre del bucket (su sola presencia activa el modo S3)
  S3_PUBLIC_URL        base pública para construir las URLs (ej. https://pub-xxx.r2.dev
                       o un dominio propio enlazado al bucket)
  S3_ENDPOINT_URL      endpoint del servicio (R2: https://<accountid>.r2.cloudflarestorage.com;
                       AWS S3: dejar vacío)
  S3_ACCESS_KEY_ID     credencial
  S3_SECRET_ACCESS_KEY credencial
  S3_REGION            región (default "auto", válido para R2)
"""

import io
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

UPLOADS_DIR = Path(__file__).parent / "uploads"

# Límite de tamaño y validación de tipo real por magic bytes (no se confía en
# el filename ni en el Content-Type que envía el cliente, ambos falsificables).
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# Toda imagen se guarda re-encodeada a WebP y redimensionada. El ahorro grande no
# lo da el formato sino los píxeles: una foto de celular de 4000x3000 pesa MB en
# cualquier formato; a 512 px queda en decenas de KB. Con el bucket de Supabase en
# 1 GB, guardar los originales dejaría al gimnasio sin espacio en pocos cientos de
# subidas y ahí fallarían también las fotos legítimas.
LADO_MAX_AVATAR = 512
LADO_MAX_PRODUCTO = 1024
WEBP_QUALITY = 82

# Techo de píxeles al decodificar: un PNG de 200 KB puede expandirse a 30000x30000
# y comerse la RAM del contenedor (512 MB en Render Starter). El tope de 5 MB de
# entrada no protege de eso, porque el peligro está en el tamaño descomprimido.
MAX_PIXELES = 50_000_000  # 50 MP, muy por encima de cualquier cámara de celular


def _detectar_imagen(data: bytes) -> Optional[Tuple[str, str]]:
    """Devuelve (extension, content_type) según los magic bytes, o None si no
    es una imagen de un tipo permitido (jpg/png/webp/gif)."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpg", "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif", "image/gif"
    return None


def _leer_y_validar(foto: UploadFile) -> Tuple[bytes, str, str]:
    """Lee el archivo subido (con tope de tamaño) y valida que sea una imagen
    real de un tipo permitido. Devuelve (bytes, extension, content_type).
    Lanza HTTPException 400/413 si no cumple."""
    data = foto.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="La imagen supera el tamaño máximo de 5 MB.")
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío.")
    detectado = _detectar_imagen(data)
    if detectado is None:
        raise HTTPException(status_code=400, detail="Formato de imagen no permitido. Usa JPG, PNG, WEBP o GIF.")
    extension, content_type = detectado
    return data, extension, content_type


def _procesar_imagen(data: bytes, lado_max: int) -> bytes:
    """Redimensiona y re-encodea a WebP. Devuelve los bytes a guardar.

    Los GIF animados quedan como WebP estático (primer frame): son avatares y
    fotos de producto, no hace falta conservar la animación.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError
    from PIL.Image import DecompressionBombError

    # Pillow avisa con un warning a la mitad de este valor y levanta
    # DecompressionBombError al pasarlo.
    Image.MAX_IMAGE_PIXELS = MAX_PIXELES

    try:
        img = Image.open(io.BytesIO(data))
        # Sin esto las fotos sacadas con el celular en vertical salen acostadas:
        # la orientación vive en el EXIF, que al re-encodear se pierde.
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img.thumbnail((lado_max, lado_max))
        salida = io.BytesIO()
        img.save(salida, "WEBP", quality=WEBP_QUALITY, method=4)
    except DecompressionBombError:
        raise HTTPException(status_code=400, detail="La imagen tiene dimensiones desproporcionadas.")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="No se pudo procesar la imagen.")

    return salida.getvalue()

S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "").rstrip("/")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "") or None
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_REGION = os.getenv("S3_REGION", "auto")

USA_S3 = bool(S3_BUCKET)

_cliente_s3 = None


def _s3():
    """Cliente boto3 perezoso y cacheado."""
    global _cliente_s3
    if _cliente_s3 is None:
        import boto3
        _cliente_s3 = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        )
    return _cliente_s3


def guardar_archivo(foto: UploadFile, subcarpeta: str = "") -> str:
    """Guarda el archivo subido y devuelve la URL para persistir en la BD.

    subcarpeta: prefijo opcional (ej. "productos").
    """
    # Los magic bytes son el primer filtro: descartan lo que ni siquiera es una
    # imagen antes de gastar CPU (y RAM) decodificándola.
    data, _extension, _content_type = _leer_y_validar(foto)
    lado_max = LADO_MAX_PRODUCTO if subcarpeta == "productos" else LADO_MAX_AVATAR
    data = _procesar_imagen(data, lado_max)
    content_type = "image/webp"
    nombre = f"{uuid.uuid4().hex}.webp"
    rel = f"{subcarpeta}/{nombre}" if subcarpeta else nombre

    if USA_S3:
        key = f"uploads/{rel}"
        _s3().upload_fileobj(
            io.BytesIO(data),
            S3_BUCKET,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return f"{S3_PUBLIC_URL}/{key}"

    destino = UPLOADS_DIR / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb") as f:
        f.write(data)
    return f"/uploads/{rel}"


def eliminar_archivo(url: Optional[str]) -> None:
    """Borra el archivo apuntado por la URL almacenada. Tolera URLs de ambos
    backends para soportar registros creados antes de migrar a S3."""
    if not url:
        return

    if USA_S3 and S3_PUBLIC_URL and url.startswith(S3_PUBLIC_URL + "/"):
        key = url[len(S3_PUBLIC_URL) + 1:]
        try:
            _s3().delete_object(Bucket=S3_BUCKET, Key=key)
        except Exception:
            pass
        return

    if url.startswith("/uploads/"):
        archivo = UPLOADS_DIR / url[len("/uploads/"):]
        if archivo.exists():
            archivo.unlink()
