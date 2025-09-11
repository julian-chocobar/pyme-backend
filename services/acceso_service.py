from database.connection import SessionLocal
from database.repositories import AccesoRepository, EmpleadoRepository
from services.face_recognition_service import FaceRecognitionService
from models.enums import TipoAccesoEnum
from datetime import datetime, timezone
from fastapi import HTTPException

class AccesoService:
    def __init__(self):
        self.session = SessionLocal()
        self.acceso_repo = AccesoRepository(self.session)
        self.empleado_repo = EmpleadoRepository(self.session)
        self.face_service = FaceRecognitionService(threshold=0.6)
    
    def get_all_accesos(self, empleado_id=None, area_id=None, tipo_acceso=None, 
                       fecha_inicio=None, fecha_fin=None, limit=10, offset=0, 
                       page=1, page_size=10):
        """Obtiene todos los accesos con filtros y paginación
        
        Args:
            empleado_id: Filtrar por ID de empleado
            area_id: Filtrar por ID de área
            tipo_acceso: Filtrar por tipo de acceso
            fecha_inicio: Filtrar desde esta fecha
            fecha_fin: Filtrar hasta esta fecha
            limit: Número máximo de registros a devolver
            offset: Número de registros a omitir
            page: Número de página actual (comienza en 1)
            page_size: Tamaño de la página
            
        Returns:
            Dict con la lista de accesos y metadatos de paginación
        """
        from datetime import datetime
        
        # Convert string dates to datetime objects
        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio)
            except (ValueError, TypeError):
                fecha_inicio = None
                
        if isinstance(fecha_fin, str):
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin)
            except (ValueError, TypeError):
                fecha_fin = None
        
        # Obtener accesos con paginación
        accesos, total = self.acceso_repo.get_all_with_employee_info(
            empleado_id=empleado_id,
            area_id=area_id,
            tipo_acceso=tipo_acceso,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit,
            offset=offset
        )
        
        # Calcular metadatos de paginación
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        # Asegurar que la página actual sea válida
        current_page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        pagination = {
            "total": total,
            "page": current_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_previous": current_page > 1,
            "has_next": current_page < total_pages
        }
        
        return {
            "items": accesos,
            "pagination": pagination
        }
    
    def get_acceso(self, acceso_id: int):
        """Obtiene un acceso por ID"""
        acceso = self.acceso_repo.get_by_id(acceso_id)
        if not acceso:
            raise HTTPException(status_code=404, detail="Acceso no encontrado")
        return {
            "AccesoID": acceso.AccesoID,
            "EmpleadoID": acceso.EmpleadoID,
            "AreaID": acceso.AreaID,
            "FechaHora": acceso.FechaHora,
            "TipoAcceso": acceso.TipoAcceso.value if hasattr(acceso.TipoAcceso, 'value') else str(acceso.TipoAcceso),
            "MetodoAcceso": acceso.MetodoAcceso.value if hasattr(acceso.MetodoAcceso, 'value') else str(acceso.MetodoAcceso),
            "DispositivoAcceso": acceso.DispositivoAcceso,
            "ConfianzaReconocimiento": acceso.ConfianzaReconocimiento,
            "AccesoPermitido": acceso.AccesoPermitido
        }
    
    def create_facial_access(self, image_bytes, tipo_acceso: TipoAccesoEnum, 
                           area_id: str, dispositivo: str = "Dispositivo1"):
        """Crea un acceso por reconocimiento facial"""
        try:
            # Extraer encoding facial
            face_encoding = self.face_service.extract_face_encoding(image_bytes)
            
            # Obtener empleados con datos biométricos
            empleados = self.empleado_repo.get_with_biometric_data()
            
            # Buscar coincidencia
            mejor_empleado, confianza = self.face_service.compare_faces(face_encoding, empleados)
            
            if mejor_empleado is None:
                raise HTTPException(status_code=403, detail="Empleado no reconocido")
            
            # Verificar si el empleado pertenece al área
            if mejor_empleado.AreaID != area_id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Empleado {mejor_empleado.Nombre} {mejor_empleado.Apellido} no tiene acceso al área {area_id}"
                )
            
            # Crear registro de acceso
            # Usar UTC en lugar de la hora local
            ahora = datetime.now(timezone.utc).isoformat()  # Genera la hora en UTC con offset +00:00
            acceso_data = {
                "EmpleadoID": mejor_empleado.EmpleadoID,
                "AreaID": area_id,
                "FechaHora": ahora,
                "TipoAcceso": tipo_acceso.value,
                "MetodoAcceso": "Facial",
                "DispositivoAcceso": dispositivo,
                "ConfianzaReconocimiento": float(confianza),  # Convertir np.float64 a float de Python
                "AccesoPermitido": "Permitido"
            }
            
            self.acceso_repo.create(acceso_data)
            
            return {
                "message": f"Acceso {tipo_acceso.value} registrado correctamente",
                "empleado": {
                    "id": mejor_empleado.EmpleadoID,
                    "nombre": mejor_empleado.Nombre,
                    "apellido": mejor_empleado.Apellido,
                    "rol": mejor_empleado.Rol
                },
                "area_id": area_id,
                "tipo_acceso": tipo_acceso.value,
                "confianza": float(confianza),  # Convertir np.float64 a float de Python
                "acceso_permitido": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    
    def create_pin_access(self, pin: str, tipo_acceso: TipoAccesoEnum, 
                         area_id: str, dispositivo: str = "Dispositivo1"):
        """Crea un acceso por PIN"""
        try:
            # Buscar empleado por PIN y área
            empleado = self.empleado_repo.get_by_pin_and_area(pin, area_id)
            
            if not empleado:
                raise HTTPException(
                    status_code=403, 
                    detail="PIN incorrecto o empleado no tiene acceso a esta área"
                )
            
            # Verificar que el empleado esté activo
            if empleado.EstadoEmpleado != "Activo":
                raise HTTPException(
                    status_code=403,
                    detail="Empleado no está activo en el sistema"
                )
            
            # Crear registro de acceso
            ahora = datetime.now(timezone.utc).isoformat()  # Usar UTC
            acceso_data = {
                "EmpleadoID": empleado.EmpleadoID,
                "AreaID": area_id,
                "FechaHora": ahora,
                "TipoAcceso": tipo_acceso.value,
                "MetodoAcceso": "PIN",
                "DispositivoAcceso": dispositivo,
                "ConfianzaReconocimiento": 1.0,  # PIN es 100% confiable
                "AccesoPermitido": "Permitido"
            }
            
            self.acceso_repo.create(acceso_data)
            
            return {
                "message": f"Acceso {tipo_acceso.value} por PIN registrado correctamente",
                "empleado": {
                    "id": empleado.EmpleadoID,
                    "nombre": empleado.Nombre,
                    "apellido": empleado.Apellido,
                    "rol": empleado.Rol
                },
                "area_id": area_id,
                "tipo_acceso": tipo_acceso.value,
                "metodo_acceso": "PIN",
                "acceso_permitido": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    
    def __del__(self):
        self.session.close()
