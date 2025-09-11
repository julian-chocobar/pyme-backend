from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from models.database import Empleado, Area, Acceso
from datetime import datetime, timezone

class EmpleadoRepository:
    """Repository for handling database operations for Empleado model."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, empleado_id: int, include_inactive: bool = False) -> Optional[Empleado]:
        """Retrieve an employee by their ID.
        
        Args:
            empleado_id: The ID of the employee to retrieve
            include_inactive: Whether to include inactive employees
            
        Returns:
            The employee if found, None otherwise
        """
        query = self.session.query(Empleado).filter_by(EmpleadoID=empleado_id)
        if not include_inactive:
            query = query.filter(Empleado.estado == 'activo')
        return query.first()
    
    def get_all(self, 
               nombre: Optional[str] = None, 
               include_inactive: bool = False,
               limit: int = 10,
               offset: int = 0) -> Tuple[List[Empleado], int]:
        """Retrieve all employees with pagination and filtering.
        
        Args:
            nombre: Filter by name or last name (case-insensitive partial match)
            include_inactive: Whether to include inactive employees
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Tuple of (list of employees, total count) ordered by last name and first name
        """
        query = self.session.query(Empleado).join(Area)
        
        # Apply filters
        if not include_inactive:
            query = query.filter(Empleado.estado == 'activo')
            
        if nombre:
            search = f"%{nombre}%"
            query = query.filter(
                or_(
                    Empleado.Nombre.ilike(search),
                    Empleado.Apellido.ilike(search)
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(Empleado.Apellido, Empleado.Nombre)\
                    .offset(offset)\
                    .limit(limit)\
                    .all()
                    
        return items, total
    
    def get_by_dni_or_email(self, dni: str, email: str, include_inactive: bool = False) -> Optional[Empleado]:
        """Find an employee by DNI or email.
        
        Args:
            dni: DNI to search for
            email: Email to search for
            include_inactive: Whether to include inactive employees
            
        Returns:
            The employee if found, None otherwise
        """
        query = self.session.query(Empleado).filter(
            or_(
                Empleado.DNI == dni,
                Empleado.Email == email
            )
        )
        if not include_inactive:
            query = query.filter(Empleado.estado == 'activo')
        return query.first()
    
    def get_by_pin_and_area(self, pin: str, area_id: str) -> Optional[Empleado]:
        """Find an employee by PIN and area.
        
        Args:
            pin: Employee's PIN
            area_id: Area ID to search in
            
        Returns:
            The employee if found, None otherwise
        """
        return self.session.query(Empleado).filter(
            and_(
                Empleado.PIN == pin,
                Empleado.AreaID == area_id,
                Empleado.estado == 'activo'
            )
        ).first()
    
    def get_with_biometric_data(self, include_inactive: bool = False) -> List[Empleado]:
        """Retrieve employees with registered biometric data.
        
        Args:
            include_inactive: Whether to include inactive employees
            
        Returns:
            List of employees with biometric data and their area information
        """
        query = self.session.query(Empleado).options(
            joinedload(Empleado.area)  # Ensure we load the related area
        ).filter(
            Empleado.vector_cifrado.isnot(None),
            Empleado.iv.isnot(None)
        )
        
        if not include_inactive:
            query = query.filter(Empleado.estado == 'activo')
            
        return query.all()
    
    def get_by_area(self, area_id: str, include_inactive: bool = False) -> List[Empleado]:
        """Retrieve employees by area.
        
        Args:
            area_id: The area ID to filter by
            include_inactive: Whether to include inactive employees
            
        Returns:
            List of employees in the specified area
        """
        query = self.session.query(Empleado).filter_by(AreaID=area_id)
        if not include_inactive:
            query = query.filter(Empleado.estado == 'activo')
        return query.order_by(Empleado.Apellido, Empleado.Nombre).all()
    
    def create(self, empleado_data: Dict[str, Any]) -> Empleado:
        """Create a new employee.
        
        Args:
            empleado_data: Dictionary containing employee data
            
        Returns:
            The created employee
            
        Raises:
            ValueError: If there's an error creating the employee
        """
        try:
            empleado = Empleado(**empleado_data)
            self.session.add(empleado)
            self.session.commit()
            self.session.refresh(empleado)
            return empleado
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error creating employee: {str(e)}")
    
    def update(self, empleado_id: int, update_data: Dict[str, Any]) -> Optional[Empleado]:
        """Update an existing employee.
        
        Args:
            empleado_id: ID of the employee to update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated employee if found, None otherwise
            
        Raises:
            ValueError: If there's an error updating the employee
        """
        try:
            empleado = self.get_by_id(empleado_id, include_inactive=True)
            if not empleado:
                return None
                
            for key, value in update_data.items():
                if hasattr(empleado, key):
                    setattr(empleado, key, value)
                    
            self.session.commit()
            self.session.refresh(empleado)
            return empleado
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error updating employee: {str(e)}")
    
    def update_biometric_data(self, empleado_id: int, vector_encrypted: str, iv: str) -> bool:
        """Update an employee's biometric data.
        
        Args:
            empleado_id: ID of the employee
            vector_encrypted: Encrypted facial vector as base64 string
            iv: Initialization vector as base64 string
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            empleado = self.get_by_id(empleado_id, include_inactive=True)
            if not empleado:
                return False
                
            empleado.vector_cifrado = vector_encrypted
            empleado.iv = iv
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False
    
    def delete(self, empleado_id: int, soft_delete: bool = True) -> bool:
        """Delete an employee.
        
        Args:
            empleado_id: ID of the employee to delete
            soft_delete: If True, mark as inactive instead of deleting
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            empleado = self.get_by_id(empleado_id, include_inactive=True)
            if not empleado:
                return False
                
            if soft_delete:
                empleado.estado = 'inactivo'
                self.session.commit()
            else:
                self.session.delete(empleado)
                self.session.commit()
                
            return True
        except Exception:
            self.session.rollback()
            return False

class AreaRepository:
    """Repository for handling database operations for Area model."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, area_id: str) -> Optional[Area]:
        """Retrieve an area by its ID.
        
        Args:
            area_id: The ID of the area to retrieve
            
        Returns:
            The area if found, None otherwise
        """
        return self.session.query(Area).filter_by(AreaID=area_id).first()
    
    def get_all(self, include_inactive: bool = False) -> List[Area]:
        """Retrieve all areas.
        
        Args:
            include_inactive: Whether to include inactive areas
            
        Returns:
            List of areas ordered by name
        """
        query = self.session.query(Area)
        if not include_inactive:
            query = query.filter(Area.Estado == 'Activo')
        return query.order_by(Area.Nombre).all()
    
    def exists(self, area_id: str) -> bool:
        """Check if an area with the given ID exists.
        
        Args:
            area_id: The ID to check
            
        Returns:
            True if the area exists, False otherwise
        """
        return self.session.query(Area).filter_by(AreaID=area_id).first() is not None
    
    def create(self, area_data: Dict[str, Any]) -> Area:
        """Create a new area.
        
        Args:
            area_data: Dictionary containing area data
            
        Returns:
            The created area
            
        Raises:
            ValueError: If there's an error creating the area
        """
        try:
            area = Area(**area_data)
            self.session.add(area)
            self.session.commit()
            self.session.refresh(area)
            return area
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error creating area: {str(e)}")
    
    def update(self, area_id: str, update_data: Dict[str, Any]) -> Optional[Area]:
        """Update an existing area.
        
        Args:
            area_id: ID of the area to update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated area if found, None otherwise
            
        Raises:
            ValueError: If there's an error updating the area
        """
        try:
            area = self.get_by_id(area_id)
            if not area:
                return None
                
            for key, value in update_data.items():
                if hasattr(area, key):
                    setattr(area, key, value)
                    
            self.session.commit()
            self.session.refresh(area)
            return area
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error updating area: {str(e)}")
    
    def delete(self, area_id: str, force: bool = False) -> bool:
        """Delete an area.
        
        Args:
            area_id: ID of the area to delete
            force: If True, delete even if there are associated employees
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            ValueError: If force is False and there are associated employees
        """
        try:
            area = self.get_by_id(area_id)
            if not area:
                return False
                
            # Check for associated employees
            employee_count = self.session.query(Empleado).filter_by(AreaID=area_id).count()
            if employee_count > 0 and not force:
                raise ValueError(f"Cannot delete area with {employee_count} associated employees")
                
            self.session.delete(area)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            if isinstance(e, ValueError):
                raise
            return False

class AccesoRepository:
    """Repository for handling database operations for Acceso model."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, acceso_id: int) -> Optional[Acceso]:
        """Retrieve an access record by its ID.
        
        Args:
            acceso_id: The ID of the access record to retrieve
            
        Returns:
            The access record if found, None otherwise
        """
        return self.session.query(Acceso).filter_by(AccesoID=acceso_id).first()
    
    def get_all_with_employee_info(
        self,
        empleado_id: Optional[int] = None,
        area_id: Optional[str] = None,
        tipo_acceso: Optional[str] = None,
        acceso_permitido: Optional[str] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve access records with employee information.
        
        Args:
            empleado_id: Filter by employee ID
            area_id: Filter by area ID
            tipo_acceso: Filter by access type
            acceso_permitido: Filter by access result ("Permitido" or "Denegado")
            fecha_inicio: Filter by start date
            fecha_fin: Filter by end date
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Tuple of (list of access records, total count)
        """
        # Build the base query with joins
        query = self.session.query(
            Acceso,
            Empleado.Nombre.label('NombreEmpleado'),
            Empleado.Apellido,
            Empleado.DNI,
            Empleado.Rol,
            Area.Nombre.label('NombreArea')
        )\
        .join(Empleado, Acceso.EmpleadoID == Empleado.EmpleadoID, isouter=True)\
        .join(Area, Acceso.AreaID == Area.AreaID, isouter=True)
        
        # Apply filters
        if empleado_id is not None:
            query = query.filter(Acceso.EmpleadoID == empleado_id)
        if area_id:
            query = query.filter(Acceso.AreaID == area_id)
        if tipo_acceso:
            query = query.filter(Acceso.TipoAcceso == tipo_acceso)
        if acceso_permitido:
            query = query.filter(Acceso.AccesoPermitido == acceso_permitido)
        if fecha_inicio:
            query = query.filter(Acceso.FechaHora >= fecha_inicio)
        if fecha_fin:
            # Add one day to include the entire end date
            end_of_day = fecha_fin.replace(hour=23, minute=59, second=59)
            query = query.filter(Acceso.FechaHora <= end_of_day)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(Acceso.FechaHora.desc())
        query = query.offset(offset).limit(limit)
        
        # Execute query and format results
        results = query.all()
        accesos = []
        
        for acceso, nombre_empleado, apellido, dni, rol, nombre_area in results:
            acceso_dict = {
                "AccesoID": acceso.AccesoID,
                "EmpleadoID": acceso.EmpleadoID,
                "NombreEmpleado": f"{nombre_empleado or 'N/A'} {apellido or ''}".strip() or "Desconocido",
                "DNI": dni or "N/A",
                "Rol": rol.value if hasattr(rol, 'value') else str(rol) if rol else "N/A",
                "AreaID": acceso.AreaID,
                "NombreArea": nombre_area or "N/A",
                "TipoAcceso": acceso.TipoAcceso.value if hasattr(acceso.TipoAcceso, 'value') else str(acceso.TipoAcceso),
                "MetodoAcceso": acceso.MetodoAcceso.value if hasattr(acceso.MetodoAcceso, 'value') else str(acceso.MetodoAcceso),
                "DispositivoAcceso": acceso.DispositivoAcceso,
                "ConfianzaReconocimiento": acceso.ConfianzaReconocimiento,
                "AccesoPermitido": acceso.AccesoPermitido,
                "FechaHora": acceso.FechaHora.isoformat() if hasattr(acceso.FechaHora, 'isoformat') else str(acceso.FechaHora),
                "FechaHoraFormateada": acceso.FechaHora.strftime("%Y-%m-%d %H:%M:%S") if hasattr(acceso.FechaHora, 'strftime') else str(acceso.FechaHora)
            }
            accesos.append(acceso_dict)
            
        return accesos, total
    
    def create(self, acceso_data: Dict[str, Any]) -> Acceso:
        """Create a new access record.
        
        Args:
            acceso_data: Dictionary containing access record data
            
        Returns:
            The created access record
            
        Raises:
            ValueError: If there's an error creating the access record
        """
        try:
            acceso = Acceso(**acceso_data)
            self.session.add(acceso)
            self.session.commit()
            self.session.refresh(acceso)
            return acceso
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error creating access record: {str(e)}")
    
    def registrar_acceso(
        self,
        empleado_id: Optional[int],
        area_id: str,
        tipo_acceso: str,
        metodo_acceso: str,
        dispositivo: str,
        confianza: Optional[float] = None,
        acceso_permitido: str = "Permitido",
        motivo_denegacion: Optional[str] = None
    ) -> Acceso:
        """Register a new access attempt.
        
        Args:
            empleado_id: Employee ID (optional if access is denied)
            area_id: Area ID where access was attempted
            tipo_acceso: Type of access (Ingreso/Salida)
            metodo_acceso: Access method (Facial, PIN, etc.)
            dispositivo: Device identifier
            confianza: Confidence level of facial recognition (optional)
            acceso_permitido: "Permitido" or "Denegado"
            motivo_denegacion: Reason for denial (optional)
            
        Returns:
            The created access record
        """
        acceso_data = {
            "EmpleadoID": empleado_id,
            "AreaID": area_id,
            "TipoAcceso": tipo_acceso,
            "MetodoAcceso": metodo_acceso,
            "DispositivoAcceso": dispositivo,
            "ConfianzaReconocimiento": confianza,
            "AccesoPermitido": acceso_permitido,
            "MotivoDenegacion": motivo_denegacion,
            "FechaHora": datetime.now(timezone.utc)
        }
        
        return self.create(acceso_data)
    
    def delete_by_empleado_id(self, empleado_id: int) -> int:
        """Delete all access records for an employee.
        
        Args:
            empleado_id: ID of the employee
            
        Returns:
            Number of records deleted
        """
        try:
            count = self.session.query(Acceso).filter_by(EmpleadoID=empleado_id).delete()
            self.session.commit()
            return count
        except Exception:
            self.session.rollback()
            return 0
    
    def get_estadisticas_acceso(
        self,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        area_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get access statistics.
        
        Args:
            fecha_inicio: Start date for filtering
            fecha_fin: End date for filtering
            area_id: Area ID to filter by (optional)
            
        Returns:
            Dictionary with access statistics
        """
        query = self.session.query(Acceso)
        
        # Apply filters
        if fecha_inicio:
            query = query.filter(Acceso.FechaHora >= fecha_inicio)
        if fecha_fin:
            fecha_fin = datetime.combine(fecha_fin.date(), datetime.max.time())
            query = query.filter(Acceso.FechaHora <= fecha_fin)
        if area_id:
            query = query.filter(Acceso.AreaID == area_id)
        
        # Count totals
        total = query.count()
        permitidos = query.filter(Acceso.AccesoPermitido == "Permitido").count()
        denegados = total - permitidos
        
        # Calculate percentages
        porcentaje_permitidos = (permitidos / total * 100) if total > 0 else 0
        porcentaje_denegados = (denegados / total * 100) if total > 0 else 0
        
        # By access method
        metodos_query = self.session.query(
            Acceso.MetodoAcceso,
            func.count(Acceso.MetodoAcceso).label('total')
        )
        
        if fecha_inicio:
            metodos_query = metodos_query.filter(Acceso.FechaHora >= fecha_inicio)
        if fecha_fin:
            fecha_fin = datetime.combine(fecha_fin.date(), datetime.max.time())
            metodos_query = metodos_query.filter(Acceso.FechaHora <= fecha_fin)
        if area_id:
            metodos_query = metodos_query.filter(Acceso.AreaID == area_id)
            
        metodos = metodos_query.group_by(Acceso.MetodoAcceso).all()
        
        # Format results
        return {
            "total": total,
            "permitidos": permitidos,
            "denegados": denegados,
            "porcentaje_permitidos": round(porcentaje_permitidos, 2),
            "porcentaje_denegados": round(porcentaje_denegados, 2),
            "por_metodo": [
                {"metodo": metodo, "total": count, "porcentaje": round((count / total * 100) if total > 0 else 0, 2)}
                for metodo, count in metodos
            ]
        }
    
