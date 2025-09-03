from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from services.acceso_service import AccesoService
from models.enums import TipoAccesoEnum

router = APIRouter(prefix="/accesos", tags=["accesos"])

@router.get("")
async def obtener_accesos(
    empleado_id: Optional[int] = None,
    area_id: Optional[str] = None,
    tipo_acceso: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Obtiene lista de accesos con filtros opcionales
    """
    service = AccesoService()
    return service.get_all_accesos(
        empleado_id, area_id, tipo_acceso, fecha_inicio, fecha_fin, limit, offset
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
