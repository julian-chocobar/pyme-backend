from sqlalchemy import (
    Column, Integer, String, Text, Float, Enum, ForeignKey, false
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel
import enum
from typing import Optional

# Declaramos base para modelos SQLAlchemy
Base = declarative_base()

# Enumerados para roles y estados
class RolEnum(str, enum.Enum):
    Supervisor = "Supervisor"
    Operario = "Operario"
    Jefe_Turno = "Jefe_Turno"
    Control_Calidad = "Control_Calidad"
    Mantenimiento = "Mantenimiento"
    Administracion = "Administracion"

class EstadoEmpleadoEnum(str, enum.Enum):
    Activo = "Activo"
    Inactivo = "Inactivo"
    Suspendido = "Suspendido"

class TipoAccesoEnum(str, enum.Enum):
    Ingreso = "Ingreso"
    Egreso = "Egreso"

class MetodoAccesoEnum(str, enum.Enum):
    Facial = "Facial"
    PIN = "PIN"
    Manual = "Manual"

# Modelo Area
class Area(Base):
    __tablename__ = "areas"

    AreaID = Column(String, primary_key=True, index=True)  # AREA001, AREA002, etc.
    Nombre = Column(String, nullable=False)
    NivelAcceso = Column(Integer, nullable=False)
    Descripcion = Column(Text, nullable=False)
    Estado = Column(String, nullable=False, default="Activo")

    # Relación con empleados
    empleados = relationship("Empleado", back_populates="area")

# Modelo Empleado
class Empleado(Base):
    __tablename__ = "empleados"

    EmpleadoID = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String, nullable=False)
    Apellido = Column(String, nullable=False)
    DNI = Column(String, unique=True, nullable=False)
    FechaNacimiento = Column(String, nullable=False)
    Email = Column(String, unique=True, nullable=False)
    Rol = Column(Enum(RolEnum), nullable=False)
    EstadoEmpleado = Column(Enum(EstadoEmpleadoEnum), nullable=False)
    AreaID = Column(String, ForeignKey("areas.AreaID"), nullable=False)
    PIN = Column(String, nullable=True)  # PIN de acceso (opcional)
    DatosBiometricos = Column(Text, nullable=True)  # JSON string con encoding facial
    FechaRegistro = Column(String, nullable=False)

    # Relación con área
    area = relationship("Area", back_populates="empleados")

# Modelos Pydantic para solicitudes (creación de empleados)
class EmpleadoCreate(BaseModel):
    Nombre: str
    Apellido: str
    DNI: str
    FechaNacimiento: str
    Email: str
    Rol: RolEnum  # Usar el Enum para validación
    EstadoEmpleado: EstadoEmpleadoEnum # Usar el Enum para validación
    AreaID: str
    PIN: Optional[str] = None  # PIN es opcional 
    class Config:
        use_enum_values = False # Permite que los valores del enum se usen directamente

# Modelo Acceso
class Acceso(Base):
    __tablename__ = "accesos"

    AccesoID = Column(Integer, primary_key=True, index=True)
    EmpleadoID = Column(Integer, ForeignKey("empleados.EmpleadoID"), nullable=True)  # Puede ser NULL si acceso denegado
    AreaID = Column(String, ForeignKey("areas.AreaID"), nullable=False)
    FechaHoraIngreso = Column(String, nullable=True)
    FechaHoraEgreso = Column(String, nullable=True)
    TipoAcceso = Column(Enum(TipoAccesoEnum), nullable=False)
    MetodoAcceso = Column(Enum(MetodoAccesoEnum), nullable=False)
    DispositivoAcceso = Column(String, nullable=False)
    ConfianzaReconocimiento = Column(Float, nullable=True)
    ObservacionesSeguridad = Column(Text, nullable=True)
    AccesoPermitido = Column(String, nullable=False)  # "Permitido" o "Denegado"
    MotivoDenegacion = Column(Text, nullable=True)  # Razón si el acceso fue denegado

# Modelos Pydantic para respuestas (sin información sensible)
class EmpleadoResponse(BaseModel):
    EmpleadoID: int
    Nombre: str
    Apellido: str
    DNI: str
    FechaNacimiento: str
    Email: str
    Rol: str
    EstadoEmpleado: str
    AreaID: str
    FechaRegistro: str
    
    class Config:
        from_attributes = True

class AreaResponse(BaseModel):
    AreaID: str
    Nombre: str
    NivelAcceso: int
    Descripcion: str
    Estado: str
    
    class Config:
        from_attributes = True
