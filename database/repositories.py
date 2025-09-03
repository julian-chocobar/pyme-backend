from sqlalchemy.orm import Session
from models.database import Empleado, Area, Acceso
from datetime import datetime

class EmpleadoRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, empleado_id: int):
        return self.session.query(Empleado).filter_by(EmpleadoID=empleado_id).first()
    
    def get_all(self):
        return self.session.query(Empleado).order_by(Empleado.EmpleadoID).all()
    
    def get_by_dni_or_email(self, dni: str, email: str):
        return self.session.query(Empleado).filter(
            (Empleado.DNI == dni) | (Empleado.Email == email)
        ).first()
    
    def get_by_pin_and_area(self, pin: str, area_id: str):
        return self.session.query(Empleado).filter(
            Empleado.PIN == pin,
            Empleado.AreaID == area_id
        ).first()
    
    def get_with_biometric_data(self):
        return self.session.query(Empleado).filter(
            Empleado.DatosBiometricos.isnot(None)
        ).all()
    
    def create(self, empleado_data: dict):
        empleado = Empleado(**empleado_data)
        self.session.add(empleado)
        self.session.commit()
        self.session.refresh(empleado)
        return empleado
    
    def update_biometric_data(self, empleado_id: int, biometric_data: str):
        empleado = self.get_by_id(empleado_id)
        if empleado:
            empleado.DatosBiometricos = biometric_data
            self.session.commit()
            return True
        return False
    
    def delete(self, empleado_id: int):
        empleado = self.get_by_id(empleado_id)
        if empleado:
            self.session.delete(empleado)
            self.session.commit()
            return True
        return False

class AreaRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, area_id: str):
        return self.session.query(Area).filter_by(AreaID=area_id).first()
    
    def get_all(self):
        return self.session.query(Area).order_by(Area.AreaID).all()
    
    def exists(self, area_id: str):
        return self.session.query(Area).filter_by(AreaID=area_id).first() is not None

class AccesoRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, acceso_id: int):
        return self.session.query(Acceso).filter_by(AccesoID=acceso_id).first()
    
    def get_all_with_employee_info(self, empleado_id=None, area_id=None, tipo_acceso=None, 
                                 fecha_inicio=None, fecha_fin=None, limit=100, offset=0):
        query = self.session.query(
            Acceso, Empleado.Nombre, Empleado.Apellido, Empleado.DNI, Empleado.Rol
        ).join(Empleado, Acceso.EmpleadoID == Empleado.EmpleadoID)
        
        if empleado_id:
            query = query.filter(Acceso.EmpleadoID == empleado_id)
        if area_id:
            query = query.filter(Acceso.AreaID == area_id)
        if tipo_acceso:
            query = query.filter(Acceso.TipoAcceso == tipo_acceso)
        if fecha_inicio:
            query = query.filter(Acceso.FechaHora >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Acceso.FechaHora <= fecha_fin)
        
        query = query.order_by(Acceso.AccesoID.desc()).offset(offset).limit(limit)
        results = query.all()
        
        # Convertir tuplas a diccionarios
        accesos = []
        for acceso, nombre, apellido, dni, rol in results:
            acceso_dict = {
                "AccesoID": acceso.AccesoID,
                "EmpleadoID": acceso.EmpleadoID,
                "AreaID": acceso.AreaID,
                "FechaHora": acceso.FechaHora,
                "TipoAcceso": acceso.TipoAcceso.value if hasattr(acceso.TipoAcceso, 'value') else str(acceso.TipoAcceso),
                "MetodoAcceso": acceso.MetodoAcceso.value if hasattr(acceso.MetodoAcceso, 'value') else str(acceso.MetodoAcceso),
                "DispositivoAcceso": acceso.DispositivoAcceso,
                "ConfianzaReconocimiento": acceso.ConfianzaReconocimiento,
                "AccesoPermitido": acceso.AccesoPermitido,
                "Nombre": nombre,
                "Apellido": apellido,
                "DNI": dni,
                "Rol": rol.value if hasattr(rol, 'value') else str(rol)
            }
            accesos.append(acceso_dict)
        
        return accesos
    
    def create(self, acceso_data: dict):
        acceso = Acceso(**acceso_data)
        self.session.add(acceso)
        self.session.commit()
        self.session.refresh(acceso)
        return acceso
    
    def delete_by_empleado_id(self, empleado_id: int):
        self.session.query(Acceso).filter(Acceso.EmpleadoID == empleado_id).delete()
        self.session.commit()
