"""
FastAPI - Backend del sistema de gestion CrossFit Box.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Usuario, RolUsuario,
    Producto,
    Venta,
    WOD,
    Plan, Pago,
    Asistencia,
)

# ════════════════════════════ App ════════════════════════════

app = FastAPI(
    title="CrossFit Box System",
    description="API para la gestion integral de un box de CrossFit",
    version="0.1.0",
)

# ════════════════════════════ CORS ═══════════════════════════

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    SCHEMAS  PYDANTIC                         ║
# ╚══════════════════════════════════════════════════════════════╝

# ─── Usuarios ─────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=6)
    rol: RolUsuario = RolUsuario.CLIENTE
    huella_id: Optional[str] = None

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: RolUsuario
    huella_id: Optional[str]
    fecha_vencimiento: Optional[date]
    esta_en_gym: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# ─── Productos ────────────────────────────────────────────────

class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None
    precio: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    categoria: Optional[str] = None

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = None
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    categoria: Optional[str] = None
    activo: Optional[bool] = None

class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    stock: int
    categoria: Optional[str]
    activo: bool

    model_config = {"from_attributes": True}

# ─── Ventas ───────────────────────────────────────────────────

class VentaCreate(BaseModel):
    producto_id: int
    usuario_id: Optional[int] = None
    cantidad: int = Field(1, ge=1)

class VentaResponse(BaseModel):
    id: int
    producto_id: int
    usuario_id: Optional[int]
    cantidad: int
    precio_unitario: float
    total: float
    fecha_venta: datetime

    model_config = {"from_attributes": True}

# ─── WODs ─────────────────────────────────────────────────────

class WODCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    descripcion: str = Field(..., min_length=1)
    fecha: date
    coach_id: Optional[int] = None

class WODResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    fecha: date
    coach_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}

# ─── Planes / Pagos ──────────────────────────────────────────

class PagoCreate(BaseModel):
    usuario_id: int
    plan_id: int
    monto: float = Field(..., gt=0)
    metodo_pago: Optional[str] = None

class PagoResponse(BaseModel):
    id: int
    usuario_id: int
    plan_id: int
    fecha_pago: datetime
    monto: float
    metodo_pago: Optional[str]
    nueva_fecha_vencimiento: Optional[date] = None

    model_config = {"from_attributes": True}

# ─── Asistencia ──────────────────────────────────────────────

class AsistenciaCreate(BaseModel):
    huella_id: str

class AsistenciaResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    fecha_hora: datetime
    nombre_usuario: str = ""

    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║                         RUTAS                                ║
# ╚══════════════════════════════════════════════════════════════╝

# ─── Health ───────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Ruta de prueba para verificar que el servidor esta activo."""
    return {"status": "ok", "message": "Gym System Online"}


# ═══════════════════════ USUARIOS ═════════════════════════════

@app.post(
    "/usuarios/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo cliente o entrenador en la base de datos."""
    existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email.",
        )

    nuevo = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=payload.password,  # TODO: hashear con bcrypt
        rol=payload.rol,
        huella_id=payload.huella_id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get("/usuarios/", response_model=List[UsuarioResponse], tags=["Usuarios"])
def listar_usuarios(db: Session = Depends(get_db)):
    """Devuelve todos los usuarios registrados."""
    return db.query(Usuario).all()


@app.get("/usuarios/huella/{huella_id}", response_model=UsuarioResponse, tags=["Usuarios"])
def buscar_por_huella(huella_id: str, db: Session = Depends(get_db)):
    """Busca un usuario por su ID de huella digital."""
    usuario = db.query(Usuario).filter(Usuario.huella_id == huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")
    return usuario


# ═══════════════════════ PRODUCTOS (CRUD) ═════════════════════

@app.get("/productos/", response_model=List[ProductoResponse], tags=["Productos"])
def listar_productos(
    solo_activos: bool = Query(True, description="Filtrar solo productos activos"),
    db: Session = Depends(get_db),
):
    """Devuelve la lista de productos de la tienda."""
    query = db.query(Producto)
    if solo_activos:
        query = query.filter(Producto.activo == True)
    return query.all()


@app.get("/productos/{producto_id}", response_model=ProductoResponse, tags=["Productos"])
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    """Obtiene un producto por su ID."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return producto


@app.post(
    "/productos/",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(payload: ProductoCreate, db: Session = Depends(get_db)):
    """Agrega un nuevo producto al inventario."""
    nuevo = Producto(
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        precio=payload.precio,
        stock=payload.stock,
        categoria=payload.categoria,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.put("/productos/{producto_id}", response_model=ProductoResponse, tags=["Productos"])
def editar_producto(producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)):
    """Edita los datos de un producto existente (nombre, precio, stock, etc.)."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    datos = payload.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(producto, campo, valor)

    db.commit()
    db.refresh(producto)
    return producto


# ═══════════════════════ VENTAS ═══════════════════════════════

@app.post(
    "/ventas/",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ventas"],
)
def registrar_venta(payload: VentaCreate, db: Session = Depends(get_db)):
    """Registra una venta y descuenta automaticamente del stock."""

    # Validar producto
    producto = db.query(Producto).filter(Producto.id == payload.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    if not producto.activo:
        raise HTTPException(status_code=400, detail="El producto no esta activo.")

    # Validar stock suficiente
    if producto.stock < payload.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {producto.stock}, solicitado: {payload.cantidad}.",
        )

    # Validar usuario si se proporciona
    if payload.usuario_id:
        usuario = db.query(Usuario).filter(Usuario.id == payload.usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Crear venta
    precio_unitario = producto.precio
    total = precio_unitario * payload.cantidad

    venta = Venta(
        producto_id=payload.producto_id,
        usuario_id=payload.usuario_id,
        cantidad=payload.cantidad,
        precio_unitario=precio_unitario,
        total=total,
    )
    db.add(venta)

    # Descontar stock
    producto.stock -= payload.cantidad

    db.commit()
    db.refresh(venta)
    return venta


@app.get("/ventas/", response_model=List[VentaResponse], tags=["Ventas"])
def listar_ventas(db: Session = Depends(get_db)):
    """Devuelve el historial completo de ventas."""
    return db.query(Venta).order_by(Venta.fecha_venta.desc()).all()


# ═══════════════════════ WODs ═════════════════════════════════

@app.post(
    "/wods/",
    response_model=WODResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["WODs"],
)
def crear_wod(payload: WODCreate, db: Session = Depends(get_db)):
    """El Coach sube la rutina del dia (WOD)."""

    # Validar que no exista un WOD para esa fecha
    existe = db.query(WOD).filter(WOD.fecha == payload.fecha).first()
    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un WOD para la fecha {payload.fecha}.",
        )

    # Validar coach si se proporciona
    if payload.coach_id:
        coach = db.query(Usuario).filter(
            Usuario.id == payload.coach_id,
            Usuario.rol == RolUsuario.COACH,
        ).first()
        if not coach:
            raise HTTPException(status_code=404, detail="Coach no encontrado o el usuario no tiene rol de Coach.")

    wod = WOD(
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        fecha=payload.fecha,
        coach_id=payload.coach_id,
    )
    db.add(wod)
    db.commit()
    db.refresh(wod)
    return wod


@app.get("/wods/", response_model=List[WODResponse], tags=["WODs"])
def listar_wods(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Devuelve los WODs mas recientes."""
    return db.query(WOD).order_by(WOD.fecha.desc()).limit(limit).all()


@app.get("/wods/hoy", response_model=WODResponse, tags=["WODs"])
def wod_de_hoy(db: Session = Depends(get_db)):
    """Devuelve el WOD del dia actual."""
    hoy = date.today()
    wod = db.query(WOD).filter(WOD.fecha == hoy).first()
    if not wod:
        raise HTTPException(status_code=404, detail="No hay WOD programado para hoy.")
    return wod


# ═══════════════════════ PLANES / PAGOS ══════════════════════

@app.post(
    "/pagos/",
    response_model=PagoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Planes"],
)
def registrar_pago(payload: PagoCreate, db: Session = Depends(get_db)):
    """
    Registra el pago de un plan y actualiza automaticamente
    la fecha de vencimiento del usuario.
    """

    # Validar usuario
    usuario = db.query(Usuario).filter(Usuario.id == payload.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Validar plan
    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.activo == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado o inactivo.")

    # Crear registro de pago
    pago = Pago(
        usuario_id=payload.usuario_id,
        plan_id=payload.plan_id,
        monto=payload.monto,
        metodo_pago=payload.metodo_pago,
    )
    db.add(pago)

    # Calcular nueva fecha de vencimiento
    # Si el usuario ya tiene una fecha vigente, extender desde esa fecha
    # Si no, empezar desde hoy
    hoy = date.today()
    base = usuario.fecha_vencimiento if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy) else hoy
    nueva_fecha = base + timedelta(days=plan.duracion_dias)
    usuario.fecha_vencimiento = nueva_fecha

    db.commit()
    db.refresh(pago)

    # Respuesta con la nueva fecha de vencimiento incluida
    return PagoResponse(
        id=pago.id,
        usuario_id=pago.usuario_id,
        plan_id=pago.plan_id,
        fecha_pago=pago.fecha_pago,
        monto=pago.monto,
        metodo_pago=pago.metodo_pago,
        nueva_fecha_vencimiento=nueva_fecha,
    )


@app.get("/planes/", tags=["Planes"])
def listar_planes(db: Session = Depends(get_db)):
    """Devuelve los planes activos disponibles."""
    planes = db.query(Plan).filter(Plan.activo == True).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio,
            "duracion_dias": p.duracion_dias,
            "descripcion": p.descripcion,
        }
        for p in planes
    ]


# ═══════════════════════ ASISTENCIA ══════════════════════════

@app.post(
    "/asistencia/",
    response_model=AsistenciaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Asistencia"],
)
def registrar_asistencia(payload: AsistenciaCreate, db: Session = Depends(get_db)):
    """
    Registra entrada/salida al gym via huella digital.
    Alterna automaticamente entre 'entrada' y 'salida'.
    """
    usuario = db.query(Usuario).filter(Usuario.huella_id == payload.huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")

    # Determinar tipo: si esta_en_gym -> salida, si no -> entrada
    tipo = "salida" if usuario.esta_en_gym else "entrada"

    asistencia = Asistencia(
        usuario_id=usuario.id,
        tipo=tipo,
    )
    db.add(asistencia)

    # Toggle estado en gym
    usuario.esta_en_gym = not usuario.esta_en_gym

    db.commit()
    db.refresh(asistencia)

    return AsistenciaResponse(
        id=asistencia.id,
        usuario_id=asistencia.usuario_id,
        tipo=asistencia.tipo,
        fecha_hora=asistencia.fecha_hora,
        nombre_usuario=usuario.nombre,
    )
