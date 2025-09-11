import base64
import json
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from database.connection import SessionLocal
from database.repositories import EmpleadoRepository, AreaRepository
from models.database import EmpleadoCreate, EmpleadoResponse, Empleado
from datetime import datetime, timezone
from fastapi import HTTPException, status
from utils.crypto_utils import VectorEncryption

class EmpleadoService:
    def __init__(self):
        self.session = SessionLocal()
        self.empleado_repo = EmpleadoRepository(self.session)
        self.area_repo = AreaRepository(self.session)
    
    def get_all_empleados(self, nombre: str = None, include_inactive: bool = False, 
                         page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Obtiene todos los empleados con paginación y filtrado opcional.
        
        Args:
            nombre: Filtro opcional para buscar por nombre o apellido (búsqueda parcial)
            include_inactive: Incluir empleados inactivos
            page: Número de página (comenzando en 1)
            page_size: Cantidad de elementos por página
            
        Returns:
            Dict con la lista de empleados y metadatos de paginación
        """
        # Calcular offset basado en la página y el tamaño de página
        offset = (page - 1) * page_size
        
        # Obtener empleados con paginación
        empleados, total = self.empleado_repo.get_all(
            nombre=nombre,
            include_inactive=include_inactive,
            limit=page_size,
            offset=offset
        )
        
        # Construir la respuesta con los datos necesarios
        items = []
        for emp in empleados:
            # Verificar si el empleado tiene datos biométricos
            tiene_biometricos = emp.vector_cifrado is not None and emp.iv is not None
            
            # Obtener el nombre del área si existe
            area_nombre = emp.area.Nombre if emp.area else "Sin área asignada"
            
            item = {
                "EmpleadoID": emp.EmpleadoID,
                "DNI": emp.DNI,
                "Nombre": emp.Nombre,
                "Apellido": emp.Apellido,
                "Email": emp.Email,
                "FechaNacimiento": emp.FechaNacimiento if emp.FechaNacimiento else None,
                "AreaID": emp.AreaID,
                "AreaNombre": area_nombre,
                "Rol": emp.Rol.value if hasattr(emp.Rol, 'value') else emp.Rol,
                "Estado": emp.estado,
                "TieneBiometricos": tiene_biometricos,
                "FechaRegistro": emp.FechaRegistro if emp.FechaRegistro else None,
            }
            items.append(item)
        
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
            "items": items,
            "pagination": pagination
        }
    
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
    
    def get_empleado_completo(self, empleado_id: int, include_facial_vector: bool = False) -> Dict[str, Any]:
        """Obtiene un empleado completo con datos sensibles.
        
        Args:
            empleado_id: ID del empleado
            include_facial_vector: Si es True, incluye el vector facial desencriptado
            
        Returns:
            Dict con los datos del empleado, incluyendo el vector facial si se solicita
        """
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Empleado no encontrado"
            )
            
        result = {
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
            "estado": empleado.estado,
            "FechaRegistro": empleado.FechaRegistro,
            "tiene_vector_facial": bool(empleado.vector_cifrado and empleado.iv)
        }
        
        # Solo desencriptar el vector facial si se solicita explícitamente
        if include_facial_vector and empleado.vector_cifrado and empleado.iv:
            result["vector_facial"] = self._decrypt_facial_vector(
                empleado.vector_cifrado, empleado.iv
            )
            
        return result
    
    def _encrypt_facial_vector(self, vector: List[float]) -> Dict[str, str]:
        """Encrypt a facial vector and return the encrypted data and IV."""
        if not vector:
            return {"vector_cifrado": None, "iv": None}
            
        crypto = VectorEncryption()
        encrypted_data, iv = crypto.encrypt_vector(vector)
        
        # Convert binary data to base64 for storage in Text field
        return {
            "vector_cifrado": base64.b64encode(encrypted_data).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8')
        }
    
    def _decrypt_facial_vector(self, encrypted_b64: str, iv_b64: str) -> Optional[List[float]]:
        """Decrypt a facial vector from base64-encoded encrypted data and IV."""
        if not encrypted_b64 or not iv_b64:
            return None
            
        try:
            crypto = VectorEncryption()
            encrypted_data = base64.b64decode(encrypted_b64)
            iv = base64.b64decode(iv_b64)
            return crypto.decrypt_vector(encrypted_data, iv)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error decrypting facial vector: {str(e)}")
            return None
    
    def create_empleado(self, empleado_data: EmpleadoCreate, facial_vector: Optional[List[float]] = None):
        """Crea un nuevo empleado con vector facial opcional.
        
        Args:
            empleado_data: Datos básicos del empleado
            facial_vector: Vector facial opcional (lista de floats)
        """
        # Verificar si el DNI o Email ya existen
        existing_employee = self.empleado_repo.get_by_dni_or_email(
            empleado_data.DNI, empleado_data.Email
        )
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="DNI o Email ya registrados"
            )
        
        # Verificar si el AreaID existe
        if not self.area_repo.exists(empleado_data.AreaID):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Área con ID '{empleado_data.AreaID}' no encontrada"
            )
        
        # Encriptar el vector facial si se proporciona
        encrypted_data = {}
        if facial_vector is not None:
            encrypted_data = self._encrypt_facial_vector(facial_vector)
        
        # Crear empleado
        now = datetime.now(timezone.utc).isoformat()  # Hora en UTC con offset +00:00
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
            "FechaRegistro": now,
            "estado": "activo",
            **encrypted_data
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
    
    def update_empleado(
        self, 
        empleado_id: int, 
        empleado_data: dict, 
        facial_vector: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Actualiza un empleado existente con opción de actualizar el vector facial.
        
        Args:
            empleado_id: ID del empleado a actualizar
            empleado_data: Diccionario con los campos a actualizar
            facial_vector: Vector facial opcional para actualizar
            
        Returns:
            Dict con el mensaje y los datos del empleado actualizado
        """
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Empleado no encontrado"
            )
        
        # Verificar si el DNI o Email ya existen (excluyendo al empleado actual)
        if 'DNI' in empleado_data or 'Email' in empleado_data:
            dni = empleado_data.get('DNI', empleado.DNI)
            email = empleado_data.get('Email', empleado.Email)
            existing = self.empleado_repo.get_by_dni_or_email(dni, email)
            if existing and existing.EmpleadoID != empleado_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="DNI o Email ya registrados"
                )
        
        # Verificar si el AreaID existe
        if 'AreaID' in empleado_data and not self.area_repo.exists(empleado_data['AreaID']):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Área con ID '{empleado_data['AreaID']}' no encontrada"
            )
        
        # Actualizar el vector facial si se proporciona
        if facial_vector is not None:
            encrypted_data = self._encrypt_facial_vector(facial_vector)
            empleado_data.update(encrypted_data)
        
        # Actualizar empleado
        try:
            updated_empleado = self.empleado_repo.update(empleado_id, empleado_data)
            
            # Construir respuesta
            response_data = {
                "message": "Empleado actualizado correctamente",
                "empleado": {
                    "EmpleadoID": updated_empleado.EmpleadoID,
                    "Nombre": updated_empleado.Nombre,
                    "Apellido": updated_empleado.Apellido,
                    "DNI": updated_empleado.DNI,
                    "Email": updated_empleado.Email,
                    "Rol": updated_empleado.Rol.value if hasattr(updated_empleado.Rol, 'value') else str(updated_empleado.Rol),
                    "EstadoEmpleado": updated_empleado.EstadoEmpleado.value if hasattr(updated_empleado.EstadoEmpleado, 'value') else str(updated_empleado.EstadoEmpleado),
                    "AreaID": updated_empleado.AreaID,
                    "estado": updated_empleado.estado,
                    "tiene_vector_facial": bool(updated_empleado.vector_cifrado and updated_empleado.iv)
                }
            }
            
            return response_data
            
        except Exception as e:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error al actualizar empleado: {str(e)}"
            )
    
    def register_face(self, empleado_id: int, face_encoding_json: str):
        """Registra el rostro de un empleado"""
        empleado = self.empleado_repo.get_by_id(empleado_id)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
        # Encrypt the face encoding
        face_encoding = json.loads(face_encoding_json)
        encrypted_result = self._encrypt_facial_vector(face_encoding)
        
        if not encrypted_result["vector_cifrado"] or not encrypted_result["iv"]:
            raise HTTPException(status_code=500, detail="Error al encriptar el vector facial")
            
        encrypted_data_b64 = encrypted_result["vector_cifrado"]
        iv_b64 = encrypted_result["iv"]
        
        success = self.empleado_repo.update_biometric_data(empleado_id, encrypted_data_b64, iv_b64)
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
