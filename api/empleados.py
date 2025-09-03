from fastapi import APIRouter, HTTPException, UploadFile, File
from services.empleado_service import EmpleadoService
from services.face_recognition_service import FaceRecognitionService
from models.database import EmpleadoCreate, EmpleadoResponse
import json

router = APIRouter(prefix="/empleados", tags=["empleados"])

@router.get("", response_model=list[EmpleadoResponse])
async def obtener_empleados():
    """Obtiene lista de todos los empleados"""
    service = EmpleadoService()
    return service.get_all_empleados()

@router.get("/{empleado_id}", response_model=EmpleadoResponse)
async def obtener_empleado(empleado_id: int):
    """Obtiene un empleado específico por ID"""
    service = EmpleadoService()
    return service.get_empleado(empleado_id)

@router.get("/{empleado_id}/completo")
async def obtener_empleado_completo(empleado_id: int):
    """Obtiene información completa de un empleado (incluye datos sensibles)"""
    service = EmpleadoService()
    return service.get_empleado_completo(empleado_id)

@router.post("/crear", response_model=dict)
async def crear_empleado(empleado_data: EmpleadoCreate):
    """
    Crea un nuevo empleado en la base de datos.
    
    - **Nombre**: Nombre del empleado
    - **Apellido**: Apellido del empleado
    - **DNI**: Número de documento (debe ser único)
    - **FechaNacimiento**: Fecha de nacimiento (formato YYYY-MM-DD)
    - **Email**: Correo electrónico (debe ser único)
    - **Rol**: Rol del empleado (Supervisor, Operario, etc.)
    - **EstadoEmpleado**: Estado del empleado (Activo, Inactivo, Suspendido)
    - **AreaID**: ID del área a la que pertenece
    - **PIN**: PIN de acceso (opcional)
    
    Devuelve el ID del empleado creado.
    """
    service = EmpleadoService()
    return service.create_empleado(empleado_data)

@router.post("/{empleado_id}/registrar_rostro")
async def registrar_rostro(empleado_id: int, file: UploadFile = File(...)):
    """Registra el rostro de un empleado para reconocimiento facial"""
    # Leer imagen subida
    contents = await file.read()
    
    # Extraer encoding facial
    face_service = FaceRecognitionService()
    face_encoding = face_service.extract_face_encoding(contents)
    encoding_json = json.dumps(face_encoding)
    
    # Registrar en base de datos
    service = EmpleadoService()
    return service.register_face(empleado_id, encoding_json)

@router.delete("/{empleado_id}", response_model=dict)
async def eliminar_empleado(empleado_id: int):
    """
    Elimina un empleado de la base de datos por su EmpleadoID.
    
    - **empleado_id**: ID numérico del empleado a eliminar
    
    Devuelve un mensaje de confirmación si la operación fue exitosa.
    """
    service = EmpleadoService()
    return service.delete_empleado(empleado_id)
