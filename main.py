from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
import face_recognition
import io
import json
import numpy as np
from typing import Literal, Optional
from datetime import datetime
from database import Empleado, Acceso, TipoAccesoEnum, MetodoAccesoEnum, EmpleadoCreate, EmpleadoResponse  # solo para referencia, no usados directamente aquí
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pyme-frontend-smoky.vercel.app", "http://localhost:5173,http://localhost:3000,http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],             # Permite todos los métodos HTTP
    allow_headers=["*"],             # Permite todos los headers
)

# Middleware de debug para registrar el origen de las peticiones
@app.middleware("http")
async def log_request(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"[DEBUG] Request Origin: {origin} - {request.method} {request.url}")
    response = await call_next(request)
    return response

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("La variable de entorno DATABASE_URL no está definida")

# Instancia de conexión async a la base de datos
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    # Conectar a la base de datos al iniciar la app
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    # Desconectar al apagar la app
    await database.disconnect()

@app.get("/")
async def root():
    return {"message": "Backend reconocimiento facial con PostgreSQL listo"}

@app.get("/empleados", response_model=list[EmpleadoResponse])
async def obtener_empleados():
    # Consulta empleados usando el modelo de respuesta
    query = 'SELECT * FROM empleados ORDER BY "EmpleadoID"'
    empleados = await database.fetch_all(query=query)
    return [EmpleadoResponse(**dict(empleado)) for empleado in empleados]

@app.get("/areas")
async def obtener_areas():
    """
    Obtiene lista de todas las áreas disponibles
    """
    query = 'SELECT * FROM areas ORDER BY "AreaID"'
    areas = await database.fetch_all(query=query)
    return [dict(area) for area in areas]

@app.get("/areas/{area_id}")
async def obtener_area(area_id: str):
    """
    Obtiene información de un área específica
    """
    query = 'SELECT * FROM areas WHERE "AreaID" = :area_id'
    area = await database.fetch_one(query=query, values={"area_id": area_id})
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return dict(area)

@app.get("/empleados/{empleado_id}", response_model=EmpleadoResponse)
async def obtener_empleado(empleado_id: int):
    # Consulta empleado por ID usando el modelo de respuesta
    query = 'SELECT * FROM empleados WHERE "EmpleadoID" = :empleado_id'
    empleado = await database.fetch_one(query=query, values={"empleado_id": empleado_id})
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return EmpleadoResponse(**dict(empleado))

@app.get("/empleados/{empleado_id}/completo")
async def obtener_empleado_completo(empleado_id: int):
    # Endpoint para desarrollo que devuelve todos los datos del empleado
    query = 'SELECT * FROM empleados WHERE "EmpleadoID" = :empleado_id'
    empleado = await database.fetch_one(query=query, values={"empleado_id": empleado_id})
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return dict(empleado)

@app.get("/accesos")
async def obtener_accesos(
    empleado_id: Optional[int] = None,
    area_id: Optional[str] = None,
    tipo_acceso: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Obtiene lista de accesos con filtros opcionales
    """
    base_query = """
        SELECT a.*, e."Nombre", e."Apellido", e."DNI", e."Rol"
        FROM accesos a
        JOIN empleados e ON a."EmpleadoID" = e."EmpleadoID"
        WHERE 1=1
    """
    values = {}
    
    if empleado_id:
        base_query += ' AND a."EmpleadoID" = :empleado_id'
        values["empleado_id"] = empleado_id
    
    if area_id:
        base_query += ' AND a."AreaID" = :area_id'
        values["area_id"] = area_id
    
    if tipo_acceso:
        base_query += ' AND a."TipoAcceso" = :tipo_acceso'
        values["tipo_acceso"] = tipo_acceso
    
    if fecha_inicio:
        base_query += ' AND (a."FechaHoraIngreso" >= :fecha_inicio OR a."FechaHoraEgreso" >= :fecha_inicio)'
        values["fecha_inicio"] = fecha_inicio
    
    if fecha_fin:
        base_query += ' AND (a."FechaHoraIngreso" <= :fecha_fin OR a."FechaHoraEgreso" <= :fecha_fin)'
        values["fecha_fin"] = fecha_fin
    
    base_query += ' ORDER BY a."AccesoID" DESC LIMIT :limit OFFSET :offset'
    values["limit"] = limit
    values["offset"] = offset
    
    accesos = await database.fetch_all(query=base_query, values=values)
    return [dict(acceso) for acceso in accesos]

@app.get("/accesos/{acceso_id}")
async def obtener_acceso(acceso_id: int):
    """
    Obtiene un acceso específico por ID
    """
    query = """
        SELECT a.*, e."Nombre", e."Apellido", e."DNI", e."Rol"
        FROM accesos a
        JOIN empleados e ON a."EmpleadoID" = e."EmpleadoID"
        WHERE a."AccesoID" = :acceso_id
    """
    acceso = await database.fetch_one(query=query, values={"acceso_id": acceso_id})
    if not acceso:
        raise HTTPException(status_code=404, detail="Acceso no encontrado")
    return dict(acceso)

@app.post("/empleados/{empleado_id}/registrar_rostro")
async def registrar_rostro(empleado_id: int, file: UploadFile = File(...)):
    # Buscar empleado
    query = 'SELECT * FROM empleados WHERE "EmpleadoID" = :empleado_id'
    empleado = await database.fetch_one(query=query, values={"empleado_id": empleado_id})
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    # Leer imagen subida
    contents = await file.read()
    imagen = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(imagen)
    if len(encodings) == 0:
        raise HTTPException(status_code=400, detail="No se detectó rostro en la imagen")

    # Guardar encoding facial como JSON string
    encoding = encodings[0].tolist()
    encoding_json = json.dumps(encoding)

    # Actualizar empleado con encoding
    update_query = 'UPDATE empleados SET "DatosBiometricos" = :encoding WHERE "EmpleadoID" = :empleado_id'
    await database.execute(query=update_query, values={"encoding": encoding_json, "empleado_id": empleado_id})

    return {"message": "Rostro registrado correctamente"}

@app.post("/empleados/crear", response_model=dict)
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
    # Verificar si el DNI o Email ya existen
    async with database.transaction():
        existing_employee_query = 'SELECT "EmpleadoID" FROM empleados WHERE "DNI" = :dni OR "Email" = :email'
        existing_employee = await database.fetch_one(
            query=existing_employee_query, 
            values={"dni": empleado_data.DNI, "email": empleado_data.Email}
        )
        if existing_employee:
            raise HTTPException(status_code=400, detail="DNI o Email ya registrados")
        
        # Verificar si el AreaID existe
        area_exists_query = 'SELECT "AreaID" FROM areas WHERE "AreaID" = :area_id'
        area_exists = await database.fetch_one(query=area_exists_query, values={"area_id": empleado_data.AreaID})
        if not area_exists:
            raise HTTPException(status_code=404, detail=f"Área con ID '{empleado_data.AreaID}' no encontrada")
        
        # Obtener el siguiente ID disponible
        next_id_query = 'SELECT COALESCE(MAX("EmpleadoID"), 0) + 1 as next_id FROM empleados'
        next_id_result = await database.fetch_one(query=next_id_query)
        next_id = next_id_result["next_id"]
        
        # Insertar el nuevo empleado
        now = datetime.now().isoformat()
        insert_query = """
            INSERT INTO empleados (
                "EmpleadoID", "Nombre", "Apellido", "DNI", "FechaNacimiento", "Email", "Rol", 
                "EstadoEmpleado", "AreaID", "PIN", "FechaRegistro"
            ) VALUES (
                :EmpleadoID, :Nombre, :Apellido, :DNI, :FechaNacimiento, :Email, :Rol, 
                :EstadoEmpleado, :AreaID, :PIN, :FechaRegistro
            ) RETURNING "EmpleadoID"
        """

        values = {
            "EmpleadoID": next_id,
            "Nombre": empleado_data.Nombre,
            "Apellido": empleado_data.Apellido,
            "DNI": empleado_data.DNI,
            "FechaNacimiento": empleado_data.FechaNacimiento,
            "Email": empleado_data.Email,
            "Rol": empleado_data.Rol.value,  # Usar .value para el enum
            "EstadoEmpleado": empleado_data.EstadoEmpleado.value,
            "AreaID": empleado_data.AreaID,
            "PIN": empleado_data.PIN,
            "FechaRegistro": now
        }
        
        try:
            empleado_id = await database.execute(query=insert_query, values=values)
            # Obtener el empleado recién creado para devolverlo en la respuesta
            empleado = await database.fetch_one(
                query='SELECT * FROM empleados WHERE "EmpleadoID" = :empleado_id',
                values={"empleado_id": empleado_id}
            )
            return {
                "message": "Empleado creado correctamente",
                "empleado": EmpleadoResponse(**dict(empleado)).dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear empleado: {str(e)}")

@app.delete("/empleados/{empleado_id}", response_model=dict)
async def eliminar_empleado(empleado_id: int):
    """
    Elimina un empleado de la base de datos por su EmpleadoID.
    
    - **empleado_id**: ID numérico del empleado a eliminar
    
    Devuelve un mensaje de confirmación si la operación fue exitosa.
    """
    # Verificar si el empleado existe
    query = 'SELECT * FROM empleados WHERE "EmpleadoID" = :empleado_id'
    empleado = await database.fetch_one(query=query, values={"empleado_id": empleado_id})
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Iniciar transacción para asegurar la integridad de los datos
    async with database.transaction():
        # Primero, eliminar registros relacionados en otras tablas (si existen)
        # Por ejemplo, si hay una tabla de accesos que referencia al empleado
        try:
            # Eliminar accesos del empleado
            await database.execute(
                query='DELETE FROM accesos WHERE "EmpleadoID" = :empleado_id',
                values={"empleado_id": empleado_id}
            )
            
            # Luego eliminar el empleado
            delete_query = 'DELETE FROM empleados WHERE "EmpleadoID" = :empleado_id'
            await database.execute(query=delete_query, values={"empleado_id": empleado_id})
            
            return {
                "message": "Empleado eliminado correctamente",
                "empleado_eliminado": EmpleadoResponse(**dict(empleado)).dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar empleado: {str(e)}")

@app.post("/accesos/crear")
async def crear_acceso(
    file: UploadFile = File(...),
    tipo_acceso: TipoAccesoEnum = Form(...),
    area_id: str = Form(...),
    dispositivo: str = Form("Dispositivo1"),
    observaciones: Optional[str] = Form(None)
):
    """
    Crea un nuevo acceso después de reconocer facialmente al empleado.
    Solo registra accesos cuando son permitidos.
    Si el empleado no es reconocido o no tiene permisos para el área, devuelve error sin crear registro.
    """
    try:
        # Leer imagen subida
        contents = await file.read()
        imagen = face_recognition.load_image_file(io.BytesIO(contents))
        encodings = face_recognition.face_encodings(imagen)
        
        if len(encodings) == 0:
            raise HTTPException(status_code=400, detail="No se detectó rostro en la imagen")

        encoding = encodings[0]
        ahora = datetime.now().isoformat()

        # Obtener empleados con datos biométricos
        query = 'SELECT * FROM empleados WHERE "DatosBiometricos" IS NOT NULL'
        empleados = await database.fetch_all(query=query)

        mejor_empleado = None
        mejor_confianza = 0.6  # umbral de distancia para reconocimiento
        
        for empleado in empleados:
            encoding_guardado = np.array(json.loads(empleado["DatosBiometricos"]))
            distancia = np.linalg.norm(encoding - encoding_guardado)
            if distancia < mejor_confianza:
                mejor_confianza = distancia
                mejor_empleado = empleado

        if mejor_empleado is None:
            # No crear registro de acceso, solo devolver error
            raise HTTPException(status_code=403, detail="Empleado no reconocido")

        # Verificar si el empleado pertenece al área
        if mejor_empleado["AreaID"] != area_id:
            # No crear registro de acceso, solo devolver error
            raise HTTPException(
                status_code=403, 
                detail=f"Empleado {mejor_empleado['Nombre']} {mejor_empleado['Apellido']} no tiene acceso al área {area_id}"
            )

        # Acceso permitido - crear registro
        fecha_ingreso = ahora if tipo_acceso == TipoAccesoEnum.Ingreso else None
        fecha_egreso = ahora if tipo_acceso == TipoAccesoEnum.Egreso else None

        acceso_permitido = {
            "EmpleadoID": mejor_empleado["EmpleadoID"],
            "AreaID": area_id,
            "FechaHoraIngreso": fecha_ingreso,
            "FechaHoraEgreso": fecha_egreso,
            "TipoAcceso": tipo_acceso.value,
            "MetodoAcceso": "Facial",
            "DispositivoAcceso": dispositivo,
            "ConfianzaReconocimiento": 1 - mejor_confianza,
            "ObservacionesSeguridad": observaciones,
            "AccesoPermitido": "Permitido",
            "MotivoDenegacion": None
        }

        insert_query = """
            INSERT INTO accesos (
                "EmpleadoID", "AreaID", "FechaHoraIngreso", "FechaHoraEgreso",
                "TipoAcceso", "MetodoAcceso", "DispositivoAcceso", "ConfianzaReconocimiento",
                "ObservacionesSeguridad", "AccesoPermitido", "MotivoDenegacion"
            ) VALUES (
                :EmpleadoID, :AreaID, :FechaHoraIngreso, :FechaHoraEgreso,
                :TipoAcceso, :MetodoAcceso, :DispositivoAcceso, :ConfianzaReconocimiento,
                :ObservacionesSeguridad, :AccesoPermitido, :MotivoDenegacion
            )
        """

        await database.execute(query=insert_query, values=acceso_permitido)

        return {
            "message": f"Acceso {tipo_acceso.value} registrado correctamente",
            "empleado": {
                "id": mejor_empleado["EmpleadoID"],
                "nombre": mejor_empleado["Nombre"],
                "apellido": mejor_empleado["Apellido"],
                "rol": mejor_empleado["Rol"]
            },
            "area_id": area_id,
            "tipo_acceso": tipo_acceso.value,
            "confianza": 1 - mejor_confianza,
            "acceso_permitido": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/accesos/crear_pin")
async def crear_acceso_pin(
    pin: str = Form(...),
    tipo_acceso: TipoAccesoEnum = Form(...),
    area_id: str = Form(...),
    dispositivo: str = Form("Dispositivo1"),
    observaciones: Optional[str] = Form(None)
):
    """
    Crea un nuevo acceso mediante PIN.
    Solo registra accesos cuando son permitidos.
    """
    try:
        # Buscar empleado por PIN y área
        query = 'SELECT * FROM empleados WHERE "PIN" = :pin AND "AreaID" = :area_id'
        empleado = await database.fetch_one(query=query, values={"pin": pin, "area_id": area_id})
        
        if not empleado:
            # No crear registro de acceso, solo devolver error
            raise HTTPException(
                status_code=403, 
                detail="PIN incorrecto o empleado no tiene acceso a esta área"
            )

        # Verificar que el empleado esté activo
        if empleado["EstadoEmpleado"] != "Activo":
            raise HTTPException(
                status_code=403,
                detail="Empleado no está activo en el sistema"
            )

        # Acceso permitido - crear registro
        ahora = datetime.now().isoformat()
        fecha_ingreso = ahora if tipo_acceso == TipoAccesoEnum.Ingreso else None
        fecha_egreso = ahora if tipo_acceso == TipoAccesoEnum.Egreso else None

        acceso_permitido = {
            "EmpleadoID": empleado["EmpleadoID"],
            "AreaID": area_id,
            "FechaHoraIngreso": fecha_ingreso,
            "FechaHoraEgreso": fecha_egreso,
            "TipoAcceso": tipo_acceso.value,
            "MetodoAcceso": "PIN",
            "DispositivoAcceso": dispositivo,
            "ConfianzaReconocimiento": 1.0,  # PIN es 100% confiable
            "ObservacionesSeguridad": observaciones,
            "AccesoPermitido": "Permitido",
            "MotivoDenegacion": None
        }

        insert_query = """
            INSERT INTO accesos (
                "EmpleadoID", "AreaID", "FechaHoraIngreso", "FechaHoraEgreso",
                "TipoAcceso", "MetodoAcceso", "DispositivoAcceso", "ConfianzaReconocimiento",
                "ObservacionesSeguridad", "AccesoPermitido", "MotivoDenegacion"
            ) VALUES (
                :EmpleadoID, :AreaID, :FechaHoraIngreso, :FechaHoraEgreso,
                :TipoAcceso, :MetodoAcceso, :DispositivoAcceso, :ConfianzaReconocimiento,
                :ObservacionesSeguridad, :AccesoPermitido, :MotivoDenegacion
            )
        """

        await database.execute(query=insert_query, values=acceso_permitido)

        return {
            "message": f"Acceso {tipo_acceso.value} por PIN registrado correctamente",
            "empleado": {
                "id": empleado["EmpleadoID"],
                "nombre": empleado["Nombre"],
                "apellido": empleado["Apellido"],
                "rol": empleado["Rol"]
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
