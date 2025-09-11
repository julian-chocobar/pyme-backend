from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from models.database import PaginatedResponse
from typing import Optional
from services.acceso_service import AccesoService
from models.enums import TipoAccesoEnum

router = APIRouter(prefix="/accesos", tags=["accesos"])

@router.get("", response_model=PaginatedResponse)
async def obtener_accesos(
    empleado_id: Optional[int] = None,
    area_id: Optional[str] = None,
    tipo_acceso: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)")
):
    """
    Obtiene lista de accesos con filtros opcionales y paginación
    
    Parámetros:
    - empleado_id: Filtrar por ID de empleado
    - area_id: Filtrar por ID de área
    - tipo_acceso: Filtrar por tipo de acceso (Ingreso/Salida)
    - fecha_inicio: Filtrar desde esta fecha (formato YYYY-MM-DD)
    - fecha_fin: Filtrar hasta esta fecha (formato YYYY-MM-DD)
    - page: Número de página (comienza en 1)
    - page_size: Cantidad de elementos por página (máx. 100)
    
    Los resultados se ordenan por fecha y hora de acceso en orden descendente (más recientes primero)
    """
    service = AccesoService()
    offset = (page - 1) * page_size
    return service.get_all_accesos(
        empleado_id=empleado_id,
        area_id=area_id,
        tipo_acceso=tipo_acceso,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        limit=page_size,
        offset=offset,
        page=page,
        page_size=page_size
    )

@router.get("/{acceso_id}")
async def obtener_acceso(acceso_id: int):
    """
    Obtiene un acceso específico por ID
    """
    service = AccesoService()
    return service.get_acceso(acceso_id)

@router.post("/crear")
async def crear_acceso(
    file: UploadFile = File(...),
    tipo_acceso: TipoAccesoEnum = Form(...),
    area_id: str = Form(...),
    dispositivo: str = Form("Dispositivo1"),
):
    """
    Crea un nuevo acceso después de reconocer facialmente al empleado.
    Solo registra accesos cuando son permitidos.
    Si el empleado no es reconocido o no tiene permisos para el área, devuelve error sin crear registro.
    """
    # Leer imagen subida
    contents = await file.read()
    
    service = AccesoService()
    return service.create_facial_access(contents, tipo_acceso, area_id, dispositivo)

@router.post("/crear_pin")
async def crear_acceso_pin(
    pin: str = Form(...),
    tipo_acceso: TipoAccesoEnum = Form(...),
    area_id: str = Form(...),
    dispositivo: str = Form("Dispositivo1"),
):
    """
    Crea un nuevo acceso mediante PIN.
    Solo registra accesos cuando son permitidos.
    """
    service = AccesoService()
    return service.create_pin_access(pin, tipo_acceso, area_id, dispositivo)
