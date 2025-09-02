import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from database import Empleado, RolEnum, EstadoEmpleadoEnum, Acceso, TipoAccesoEnum, MetodoAccesoEnum, Area
from datetime import datetime
import os
from dotenv import load_dotenv

# Carga variables de entorno desde archivo .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("La variable de entorno DATABASE_URL no está definida")
    
# Crear motor de conexión
engine = create_engine(DATABASE_URL)
# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Crear sesión para insertar datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cargar_areas_ejemplo():
    session = SessionLocal()
    try:
        # Crear áreas de ejemplo basadas en la imagen
        areas = [
            Area(
                AreaID="AREA001",
                Nombre="Preparacion",
                Descripcion="Control de materia prima entrante",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA002",
                Nombre="Procesamiento",
                Descripcion="Procesamiento inicial de alimentos",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA003",
                Nombre="Elaboración",
                Descripcion="Elaboración de productos terminados",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA004",
                Nombre="Envasado",
                Descripcion="Envasado y empaquetado final",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA005",
                Nombre="Etiquetado",
                Descripcion="Etiquetado",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA006",
                Nombre="Control Calidad",
                Descripcion="Control de calidad y laboratorio",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA007",
                Nombre="Administración",
                Descripcion="Área administrativa y gerencia",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA008",
                Nombre="Comun",
                Descripcion="Espacios comunes",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA009",
                Nombre="Logistica",
                Descripcion="Gestion de almacenamiento y distribucion de insumos y productos terminados",
                Estado="Activo"
            )
        ]
        
        # Insertar áreas si no existen
        for area in areas:
            existe = session.query(Area).filter_by(AreaID=area.AreaID).first()
            if not existe:
                session.add(area)
        session.commit()
        print("Áreas de ejemplo cargadas correctamente.")
    except Exception as e:
        print("Error cargando áreas:", e)
        session.rollback()
    finally:
        session.close()

def cargar_empleados_iniciales():
    session = SessionLocal()
    try:
        # Crear empleados de ejemplo
        empleados = [
            Empleado(
                Nombre="Julian",
                Apellido="Chocobar",
                DNI="12345678",
                FechaNacimiento="2000-01-01",
                Email="julian.chocobar@example.com",
                Rol=RolEnum.Operario,
                EstadoEmpleado=EstadoEmpleadoEnum.Activo,
                AreaID="AREA001",  # Preparacion
                PIN="1234",  # PIN de ejemplo
                DatosBiometricos=None,
                FechaRegistro=datetime.now().isoformat()
            ),
            Empleado(
                Nombre="Tamara",
                Apellido="Fernández",
                DNI="87654321",
                FechaNacimiento="1990-05-15",
                Email="tamara.fernandez@example.com",
                Rol=RolEnum.Supervisor,
                EstadoEmpleado=EstadoEmpleadoEnum.Activo,
                AreaID="AREA002",  # Procesamiento
                PIN="5678",  # PIN de ejemplo
                DatosBiometricos=None,
                FechaRegistro=datetime.now().isoformat()
            ),
            Empleado(
                Nombre="Manuel",
                Apellido="Torres",
                DNI="11223344",
                FechaNacimiento="1985-03-20",
                Email="manuel.torres@example.com",
                Rol=RolEnum.Jefe_Turno,
                EstadoEmpleado=EstadoEmpleadoEnum.Activo,
                AreaID="AREA001",  # Preparacion
                PIN="9012",  # PIN de ejemplo
                DatosBiometricos=None,
                FechaRegistro=datetime.now().isoformat()
            ),
            Empleado(
                Nombre="Federico",
                Apellido="Zapata",
                DNI="55667788",
                FechaNacimiento="1992-07-10",
                Email="federico.zapata@example.com",
                Rol=RolEnum.Control_Calidad,
                EstadoEmpleado=EstadoEmpleadoEnum.Activo,
                AreaID="AREA006",  # Control Calidad
                PIN="3456",  # PIN de ejemplo
                DatosBiometricos=None,
                FechaRegistro=datetime.now().isoformat()
            ),
            Empleado(
                Nombre="Martín",
                Apellido="García",
                DNI="99887766",
                FechaNacimiento="1988-12-25",
                Email="martin.garcia@example.com",
                Rol=RolEnum.Operario,
                EstadoEmpleado=EstadoEmpleadoEnum.Activo,
                AreaID="AREA001",  # Preparacion
                PIN="7890",  # PIN de ejemplo
                DatosBiometricos=None,
                FechaRegistro=datetime.now().isoformat()
            )
                
        ]
        # Insertar empleados si no existen
        for emp in empleados:
            existe = session.query(Empleado).filter_by(EmpleadoID=emp.EmpleadoID).first()
            if not existe:
                session.add(emp)
        session.commit()
        print("Empleados iniciales cargados correctamente.")
    except Exception as e:
        print("Error cargando empleados:", e)
        session.rollback()
    finally:
        session.close()

def cargar_accesos_ejemplo():
    session = SessionLocal()
    try:
        # Crear accesos de ejemplo
        accesos = [
            Acceso(
                EmpleadoID=1,
                AreaID="AREA001",
                FechaHora="2024-08-31T08:00:00",
                TipoAcceso=TipoAccesoEnum.Ingreso,
                MetodoAcceso=MetodoAccesoEnum.Facial,
                DispositivoAcceso="Dispositivo1",
                ConfianzaReconocimiento=0.95,
                AccesoPermitido="Permitido",
            ),
            Acceso(
                EmpleadoID=2,
                AreaID="AREA002",
                FechaHora="2024-08-31T08:15:00",
                TipoAcceso=TipoAccesoEnum.Ingreso,
                MetodoAcceso=MetodoAccesoEnum.Facial,
                DispositivoAcceso="Dispositivo2",
                ConfianzaReconocimiento=0.92,
                AccesoPermitido="Permitido",
            ),
            Acceso(
                EmpleadoID=3,
                AreaID="AREA001",
                FechaHora="2024-08-31T07:45:00",
                TipoAcceso=TipoAccesoEnum.Ingreso,
                MetodoAcceso=MetodoAccesoEnum.Facial,
                DispositivoAcceso="Dispositivo1",
                ConfianzaReconocimiento=0.88,
                AccesoPermitido="Permitido",
            ),
            Acceso(
                EmpleadoID=1,
                AreaID="AREA002",
                FechaHora="2024-08-31T10:00:00",
                TipoAcceso=TipoAccesoEnum.Ingreso,
                MetodoAcceso=MetodoAccesoEnum.Facial,
                DispositivoAcceso="Dispositivo2",
                ConfianzaReconocimiento=0.90,
                AccesoPermitido="Denegado",
            ),
            Acceso(
                EmpleadoID=None,
                AreaID="AREA001",
                FechaHora="2024-08-31T10:15:00",
                TipoAcceso=TipoAccesoEnum.Ingreso,
                MetodoAcceso=MetodoAccesoEnum.Facial,
                DispositivoAcceso="Dispositivo1",
                ConfianzaReconocimiento=0.0,
                AccesoPermitido="Denegado",
            )
        ]
        
        # Insertar accesos si no existen
        for acc in accesos:
            existe = session.query(Acceso).filter_by(AccesoID=acc.AccesoID).first()
            if not existe:
                session.add(acc)
        session.commit()
        print("Accesos de ejemplo cargados correctamente.")
    except Exception as e:
        print("Error cargando accesos:", e)
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cargar_areas_ejemplo()
    cargar_empleados_iniciales()
    cargar_accesos_ejemplo()
