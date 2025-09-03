import enum

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
