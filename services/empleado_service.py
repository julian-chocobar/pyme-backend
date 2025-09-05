from database.connection import SessionLocal
from database.repositories import EmpleadoRepository, AreaRepository
from models.database import EmpleadoCreate, EmpleadoResponse
from datetime import datetime, timezone
from fastapi import HTTPException

class EmpleadoService:
    def __init__(self):
        self.session = SessionLocal()
        self.empleado_repo = EmpleadoRepository(self.session)
        self.area_repo = AreaRepository(self.session)
    
    def get_all_empleados(self):
        """Obtiene todos los empleados"""
        empleados = self.empleado_repo.get_all()
        return [EmpleadoResponse(
            EmpleadoID=emp.EmpleadoID,
            Nombre=emp.Nombre,
            Apellido=emp.Apellido,
            DNI=emp.DNI,
            FechaNacimiento=emp.FechaNacimiento,
            Email=emp.Email,
            Rol=emp.Rol.value if hasattr(emp.Rol, 'value') else str(emp.Rol),
            EstadoEmpleado=emp.EstadoEmpleado.value if hasattr(emp.EstadoEmpleado, 'value') else str(emp.EstadoEmpleado),
            AreaID=emp.AreaID,
            FechaRegistro=emp.FechaRegistro
        ) for emp in empleados]
    
    def get_empleado(self, empleado_id: int):
        """Obtiene un empleado por ID"""
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return EmpleadoResponse(
            EmpleadoID=empleado.EmpleadoID,
            Nombre=empleado.Nombre,
            Apellido=empleado.Apellido,
            DNI=empleado.DNI,
            FechaNacimiento=empleado.FechaNacimiento,
            Email=empleado.Email,
            Rol=empleado.Rol.value if hasattr(empleado.Rol, 'value') else str(empleado.Rol),
            EstadoEmpleado=empleado.EstadoEmpleado.value if hasattr(empleado.EstadoEmpleado, 'value') else str(empleado.EstadoEmpleado),
            AreaID=empleado.AreaID,
            FechaRegistro=empleado.FechaRegistro
        )
    
    def get_empleado_completo(self, empleado_id: int):
        """Obtiene un empleado completo (incluye datos sensibles)"""
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return {
            "EmpleadoID": empleado.EmpleadoID,
            "Nombre": empleado.Nombre,
            "Apellido": empleado.Apellido,
            "DNI": empleado.DNI,
            "FechaNacimiento": empleado.FechaNacimiento,
            "Email": empleado.Email,
            "Rol": empleado.Rol.value if hasattr(empleado.Rol, 'value') else str(empleado.Rol),
            "EstadoEmpleado": empleado.EstadoEmpleado.value if hasattr(empleado.EstadoEmpleado, 'value') else str(empleado.EstadoEmpleado),
            "AreaID": empleado.AreaID,
            "PIN": empleado.PIN,
            "DatosBiometricos": empleado.DatosBiometricos,
            "FechaRegistro": empleado.FechaRegistro
        }
    
    def create_empleado(self, empleado_data: EmpleadoCreate):
        """Crea un nuevo empleado"""
        # Verificar si el DNI o Email ya existen
        existing_employee = self.empleado_repo.get_by_dni_or_email(
            empleado_data.DNI, empleado_data.Email
        )
        if existing_employee:
            raise HTTPException(status_code=400, detail="DNI o Email ya registrados")
        
        # Verificar si el AreaID existe
        if not self.area_repo.exists(empleado_data.AreaID):
            raise HTTPException(status_code=404, detail=f"Área con ID '{empleado_data.AreaID}' no encontrada")
        
        # Crear empleado
        # Usar UTC en lugar de la hora local
        now = datetime.now(timezone.utc).isoformat()  # Genera la hora en UTC con offset +00:00
        empleado_dict = {
            "Nombre": empleado_data.Nombre,
            "Apellido": empleado_data.Apellido,
            "DNI": empleado_data.DNI,
            "FechaNacimiento": empleado_data.FechaNacimiento,
            "Email": empleado_data.Email,
            "Rol": empleado_data.Rol.value,
            "EstadoEmpleado": empleado_data.EstadoEmpleado.value,
            "AreaID": empleado_data.AreaID,
            "PIN": empleado_data.PIN,
            "FechaRegistro": now
        }
        
        try:
            empleado = self.empleado_repo.create(empleado_dict)
            return {
                "message": "Empleado creado correctamente",
                "empleado": EmpleadoResponse(
                    EmpleadoID=empleado.EmpleadoID,
                    Nombre=empleado.Nombre,
                    Apellido=empleado.Apellido,
                    DNI=empleado.DNI,
                    FechaNacimiento=empleado.FechaNacimiento,
                    Email=empleado.Email,
                    Rol=empleado.Rol.value if hasattr(empleado.Rol, 'value') else str(empleado.Rol),
                    EstadoEmpleado=empleado.EstadoEmpleado.value if hasattr(empleado.EstadoEmpleado, 'value') else str(empleado.EstadoEmpleado),
                    AreaID=empleado.AreaID,
                    FechaRegistro=empleado.FechaRegistro
                ).dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear empleado: {str(e)}")
    
    def register_face(self, empleado_id: int, face_encoding_json: str):
        """Registra el rostro de un empleado"""
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
        success = self.empleado_repo.update_biometric_data(empleado_id, face_encoding_json)
        if success:
            return {"message": "Rostro registrado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al registrar rostro")
    
    def delete_empleado(self, empleado_id: int):
        """Elimina un empleado"""
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
        try:
            # Eliminar accesos del empleado
            from database.repositories import AccesoRepository
            acceso_repo = AccesoRepository(self.session)
            acceso_repo.delete_by_empleado_id(empleado_id)
            
            # Eliminar empleado
            self.empleado_repo.delete(empleado_id)
            
            return {
                "message": "Empleado eliminado correctamente",
                "empleado_eliminado": EmpleadoResponse(
                    EmpleadoID=empleado.EmpleadoID,
                    Nombre=empleado.Nombre,
                    Apellido=empleado.Apellido,
                    DNI=empleado.DNI,
                    FechaNacimiento=empleado.FechaNacimiento,
                    Email=empleado.Email,
                    Rol=empleado.Rol.value if hasattr(empleado.Rol, 'value') else str(empleado.Rol),
                    EstadoEmpleado=empleado.EstadoEmpleado.value if hasattr(empleado.EstadoEmpleado, 'value') else str(empleado.EstadoEmpleado),
                    AreaID=empleado.AreaID,
                    FechaRegistro=empleado.FechaRegistro
                ).dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar empleado: {str(e)}")
    
    def __del__(self):
        self.session.close()
