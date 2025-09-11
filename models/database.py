from sqlalchemy import (
    Column, Integer, String, Text, Float, Enum, ForeignKey, false
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel
from typing import Optional
from models.enums import RolEnum, EstadoEmpleadoEnum, TipoAccesoEnum, MetodoAccesoEnum

# Declaramos base para modelos SQLAlchemy
Base = declarative_base()

# Modelo Area
class Area(Base):
    __tablename__ = "areas"

    AreaID = Column(String, primary_key=True, index=True)  # AREA001, AREA002, etc.
    Nombre = Column(String, nullable=False)
    Descripcion = Column(Text, nullable=False)
    Estado = Column(String, nullable=False, default="Activo")

    # Relación con empleados
    empleados = relationship("Empleado", back_populates="area")

# Modelo Empleado
class Empleado(Base):
    __tablename__ = "empleados"

    EmpleadoID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Nombre = Column(String, nullable=False)
    Apellido = Column(String, nullable=False)
    DNI = Column(String, unique=True, nullable=False)
    FechaNacimiento = Column(String, nullable=False)
    Email = Column(String, unique=True, nullable=False)
    Rol = Column(Enum(RolEnum), nullable=False)
    EstadoEmpleado = Column(Enum(EstadoEmpleadoEnum), nullable=False)
    AreaID = Column(String, ForeignKey("areas.AreaID"), nullable=False)
    PIN = Column(String, nullable=True)  # PIN de acceso (opcional)
    DatosBiometricos = Column(Text, nullable=True)  # JSON string con encoding facial (legacy)
    vector_cifrado = Column(Text, nullable=True)  # Encrypted facial vector
    iv = Column(Text, nullable=True)  # Initialization vector for decryption
    estado = Column(String, default='activo', nullable=False)  # 'activo' or 'inactivo'
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

    AccesoID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    EmpleadoID = Column(Integer, ForeignKey("empleados.EmpleadoID"), nullable=True)  # Puede ser NULL si acceso denegado
    AreaID = Column(String, ForeignKey("areas.AreaID"), nullable=False)
    FechaHora = Column(String, nullable=False)
    TipoAcceso = Column(Enum(TipoAccesoEnum), nullable=False)
    MetodoAcceso = Column(Enum(MetodoAccesoEnum), nullable=False)
    DispositivoAcceso = Column(String, nullable=False)
    ConfianzaReconocimiento = Column(Float, nullable=True)
    AccesoPermitido = Column(String, nullable=False)  # "Permitido" o "Denegado"

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
    AreaNombre: Optional[str] = None
    TieneBiometricos: bool = False
    FechaRegistro: str

class PaginationMetadata(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_previous: bool
    has_next: bool

class PaginatedResponse(BaseModel):
    items: list
    pagination: PaginationMetadata
    
    class Config:
        from_attributes = True

class AreaResponse(BaseModel):
    AreaID: str
    Nombre: str
    Descripcion: str
    Estado: str
    
    class Config:
        from_attributes = True
