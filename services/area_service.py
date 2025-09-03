from database.connection import SessionLocal
from database.repositories import AreaRepository
from fastapi import HTTPException

class AreaService:
    def __init__(self):
        self.session = SessionLocal()
        self.area_repo = AreaRepository(self.session)
    
    def get_all_areas(self):
        """Obtiene todas las áreas"""
        areas = self.area_repo.get_all()
        return [{
            "AreaID": area.AreaID,
            "Nombre": area.Nombre,
            "Descripcion": area.Descripcion,
            "Estado": area.Estado
        } for area in areas]
    
    def get_area(self, area_id: str):
        """Obtiene un área por ID"""
        area = self.area_repo.get_by_id(area_id)
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada")
        return {
            "AreaID": area.AreaID,
            "Nombre": area.Nombre,
            "Descripcion": area.Descripcion,
            "Estado": area.Estado
        }
    
    def __del__(self):
        self.session.close()
