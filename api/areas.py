from fastapi import APIRouter
from services.area_service import AreaService

router = APIRouter(prefix="/areas", tags=["areas"])

@router.get("")
async def obtener_areas():
    """
    Obtiene lista de todas las áreas disponibles
    """
    service = AreaService()
    return service.get_all_areas()

@router.get("/{area_id}")
async def obtener_area(area_id: str):
    """
    Obtiene información de un área específica
    """
    service = AreaService()
    return service.get_area(area_id)
