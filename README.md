# Sistema de Reconocimiento Facial para Control de Accesos

Este es un backend desarrollado en FastAPI que implementa un sistema de control de accesos mediante reconocimiento facial para PYMEs.

## Características

- **Reconocimiento Facial Avanzado**: Utiliza la librería `face_recognition` con optimizaciones para identificar empleados de manera eficiente
- **Cifrado Seguro**: Los vectores biométricos se almacenan cifrados con AES-256-GCM para máxima seguridad
- **Control de Accesos**: Registra entradas y salidas con validación de permisos por área
- **Base de Datos PostgreSQL**: Almacena empleados, accesos y datos biométricos de forma segura
- **API REST**: Endpoints para gestión completa del sistema
- **Validaciones de Seguridad**: Verifica permisos por área y reconoce empleados con umbral de confianza ajustable


```

## Requisitos del Sistema

- **Python**: Se recomienda usar la versión 3.9.18 por compatibilidad de dependencias
- **PostgreSQL**: 12 o superior, idealmente 17.4
- **Sistema Operativo**: Windows, Linux o macOS

## Instalación

1. **Clonar el repositorio**:

```bash
git clone <url-del-repositorio>
cd pyme-backend
```

2. **Crear entorno virtual**: (el comando "python" varia dependiendo de la version de python que se use)

```bash
python -m venv venv
```

3. **Activar entorno virtual**:

```bash
# En Windows (PowerShell):
venv\Scripts\Activate.ps1
# En Windows (Command Prompt):
venv\Scripts\activate.bat
# En Linux/Mac:
source venv/bin/activate
```

4. **Instalar dependencias** (el comando "pip" varia dependiendo de la version de python que se use):

```bash
pip install -r requirements.txt
```

**Nota**: La instalación puede tomar varios minutos debido a las dependencias de machine learning (dlib, face_recognition, numpy) que se instalan automáticamente.

5. **Configurar variables de entorno**:
   Crear archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db

```

6. **Crear base de datos y tablas**:

```bash
python scripts/seed_data.py
```
ó
```bash
python -m scripts.seed_data
```

7. **Ejecutar la aplicación**:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en: `http://localhost:8000`
Documentación automática de la API: `http://localhost:8000/docs`

## Solución de Problemas Comunes

### Error al instalar dlib o face_recognition

```bash
# En Windows, instalar Visual Studio Build Tools primero
# En Linux/Mac, instalar dependencias del sistema:
sudo apt-get install cmake build-essential  # Ubuntu/Debian
brew install cmake  # macOS
```

### Error de conexión a PostgreSQL

- Verificar que PostgreSQL esté ejecutándose
- Confirmar que la URL de conexión en `.env` sea correcta
- Verificar que la base de datos exista

## Uso con Docker

El proyecto incluye un Dockerfile que permite ejecutar la aplicación en un contenedor. Sigue estos pasos para usarlo localmente:

1. **Construir la imagen de Docker**:

```bash
docker build -t pyme-backend .
```

2. **Ejecutar el contenedor**:

```bash
docker run -d \
  --name pyme-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://usuario:password@host.docker.internal:5432/nombre_db \
  pyme-backend
```

**Notas importantes**:
- Asegúrate de tener Docker instalado y en ejecución en tu sistema.
- El comando asume que tu base de datos PostgreSQL está corriendo en tu máquina local. Si estás usando Docker para PostgreSQL, asegúrate de que ambos contenedores estén en la misma red de Docker.
- El parámetro `host.docker.internal` apunta a la IP de tu máquina host desde dentro del contenedor.
- Ajusta las variables de entorno según tu configuración de base de datos.

3. **Verificar que el contenedor esté en ejecución**:

```bash
docker ps
```

4. **Ver los logs del contenedor**:

```bash
docker logs pyme-backend
```

5. **Detener el contenedor**:

```bash
docker stop pyme-backend
```

6. **Eliminar el contenedor (si es necesario)**:

```bash
docker rm pyme-backend
```

## Estructura del Proyecto

```
pyme-backend/
├── api/                    # Endpoints de la API
│   ├── empleados.py       # Endpoints de empleados
│   ├── areas.py           # Endpoints de áreas
│   └── accesos.py         # Endpoints de accesos
├── models/                # Modelos de datos
│   ├── database.py        # Modelos SQLAlchemy y Pydantic
│   └── enums.py           # Enumeraciones del sistema
├── services/              # Lógica de negocio
│   ├── empleado_service.py
│   ├── area_service.py
│   ├── acceso_service.py
│   └── face_recognition_service.py
├── database/              # Configuración de base de datos
│   ├── connection.py      # Conexión SQLAlchemy
│   └── repositories.py    # Repositorios de datos
├── scripts/               # Scripts de utilidad
│   └── seed_data.py       # Datos de ejemplo
├── main.py               # Aplicación principal FastAPI
├── requirements.txt      # Dependencias
└── README.md            # Documentación
```



## Estructura de la Base de Datos

### Tabla: areas

- `AreaID` : ID único del área
- `Nombre` : Nombre del área
- `NivelAcceso` : Nivel de acceso en enteros (1-4)
- `Descripcion` : Breve descripción del área
- `Estado` : Activo o Inactivo

### Tabla: empleados

- `EmpleadoID`: ID único del empleado
- `Nombre`: Nombre del empleado
- `Apellido`: Apellido del empleado
- `DNI`: Documento Nacional de Identidad (único)
- `FechaNacimiento`: Fecha de nacimiento
- `Email`: Correo electrónico (único)
- `Rol`: Rol del empleado (Supervisor, Operario, Jefe_Turno, etc.)
- `EstadoEmpleado`: Estado actual (Activo, Inactivo, Suspendido)
- `AreaID`: ID del área donde trabaja el empleado
- `DatosBiometricos`: Encoding facial en formato JSON
- `FechaRegistro`: Fecha de registro en el sistema

### Tabla: accesos

- `AccesoID`: ID único del acceso
- `EmpleadoID`: ID del empleado (puede ser NULL si acceso denegado)
- `AreaID`: ID del área donde se intentó el acceso
- `FechaHora`: Fecha y hora del acceso
- `TipoAcceso`: Tipo de acceso (Ingreso o Egreso)
- `MetodoAcceso`: Método utilizado (Facial, PIN, Manual)
- `DispositivoAcceso`: Dispositivo utilizado para el acceso
- `ConfianzaReconocimiento`: Nivel de confianza del reconocimiento facial
- `AccesoPermitido`: Si el acceso fue permitido o denegado

## Endpoints de la API

### Empleados

#### GET `/empleados`

Obtiene información de todos los empleados.

**Nota**: Este endpoint devuelve solo la información básica de los empleados, sin datos sensibles.

**Respuesta**:

```json
[
  {
    "EmpleadoID": 1,
    "Nombre": "Juan",
    "Apellido": "Perez",
    "DNI": "12345678",
    "FechaNacimiento": "1980-01-01",
    "Email": "juan.perez@example.com",
    "Rol": "Operario",
    "EstadoEmpleado": "Activo",
    "AreaID": "AREA001",
    "FechaRegistro": "2025-08-31T18:50:38.382434"
  },
  {
    "EmpleadoID": 2,
    "Nombre": "Maria",
    "Apellido": "Gomez",
    "DNI": "87654321",
    "FechaNacimiento": "1990-05-15",
    "Email": "maria.gomez@example.com",
    "Rol": "Supervisor",
    "EstadoEmpleado": "Activo",
    "AreaID": "AREA002",
    "FechaRegistro": "2025-08-31T18:50:38.384872"
  }
]
```

#### GET `/empleados/{empleado_id}`

Obtiene información básica de un empleado específico sin datos sensibles.

**Parámetros**:

- `empleado_id` (path): ID numérico del empleado

**Respuesta**:

```json
{
  "EmpleadoID": 1,
  "Nombre": "Juan",
  "Apellido": "Perez",
  "DNI": "12345678",
  "FechaNacimiento": "1980-01-01",
  "Email": "juan.perez@example.com",
  "Rol": "Operario",
  "EstadoEmpleado": "Activo",
  "AreaID": "AREA001",
  "FechaRegistro": "2025-08-31T18:50:38.382434"
}
```

#### POST `/empleados/crear`

Crea un nuevo empleado en la base de datos. Los IDs se generan automáticamente de forma incremental.

**Parámetros (Body JSON)**:

```json
{
  "Nombre": "Juan",
  "Apellido": "Perez",
  "DNI": "12345678A",
  "FechaNacimiento": "1990-05-15",
  "Email": "juan.perez@example.com",
  "Rol": "Operario",
  "EstadoEmpleado": "Activo",
  "AreaID": "AREA001",
  "PIN": "1234"
}
```

**Validaciones:**

- PIN puede ser opcional
- DNI y Email deben ser únicos.
- AreaID debe existir en la tabla areas.

**Respuesta**:

```json
{
  "message": "Empleado creado correctamente",
  "EmpleadoID": 3
}
```

#### POST `/empleados/{empleado_id}/registrar_rostro`

Registra el rostro de un empleado para reconocimiento facial.

**Parámetros**:

- `empleado_id` (path): ID del empleado
- `file` (form): Imagen del rostro (formato: jpg, png)

**Respuesta exitosa (200 OK)**:

```json
{
  "message": "Rostro registrado correctamente",
  "vector_length": 128,
  "encryption_status": "success"
}
```

**Errores comunes**:

- `400 Bad Request`: Imagen no proporcionada o inválida
- `404 Not Found`: Empleado no encontrado
- `500 Internal Server Error`: Error al procesar la imagen

#### POST `/accesos/crear`

Crea un nuevo registro de acceso mediante reconocimiento facial.

**Parámetros (form-data)**:

- `file`: Imagen del rostro para reconocimiento
- `tipo_acceso`: "Ingreso" o "Salida"
- `area_id`: ID del área a la que se intenta acceder
- `dispositivo`: (opcional) Identificador del dispositivo

**Respuesta exitosa (200 OK)**:

```json
{
  "acceso_id": 123,
  "empleado_id": 1,
  "empleado_nombre": "Juan Pérez",
  "area_id": "AREA001",
  "tipo_acceso": "Ingreso",
  "fecha_hora": "2025-09-10T15:30:00-03:00",
  "acceso_permitido": true,
  "confianza": 0.92
}
```

**Errores comunes**:

- `403 Forbidden`: Acceso denegado (empleado no reconocido o sin permisos)
- `400 Bad Request`: Parámetros inválidos

#### DELETE `/empleados/{empleado_id}`

Elimina un empleado del sistema. Este proceso también elimina todos los registros de accesos asociados al empleado y sus datos biométricos.

**Parámetros**:

- `empleado_id` (path): ID numérico del empleado a eliminar

**Respuesta**:

```json
{
  "message": "Empleado eliminado correctamente",
  "empleado_eliminado": {
    "EmpleadoID": 1,
    "Nombre": "Juan",
    "Apellido": "Perez",
    "DNI": "12345678",
    "FechaNacimiento": "1980-01-01",
    "Email": "juan.perez@example.com",
    "Rol": "Operario",
    "EstadoEmpleado": "Activo",
    "AreaID": "AREA001",
    "FechaRegistro": "2025-08-31T18:50:38.382434"
  }
}
```

**Nota**: Esta operación es irreversible y eliminará todos los registros asociados al empleado.

### Accesos

#### GET `/accesos`

Obtiene lista de accesos con filtros opcionales.

**Parámetros de consulta**:

- `empleado_id` (opcional): Filtrar por empleado específico
- `area_id` (opcional): Filtrar por área específica
- `tipo_acceso` (opcional): Filtrar por tipo de acceso
- `fecha_inicio` (opcional): Filtrar desde fecha
- `fecha_fin` (opcional): Filtrar hasta fecha
- `limit` (opcional): Límite de resultados (default: 100)
- `offset` (opcional): Desplazamiento para paginación (default: 0)

**Ejemplo**:

```bash
GET /accesos?empleado_id=1&area_id=AREA001&limit=10
```

**Respuesta**:

```json
[
  {
    "AccesoID": 1,
    "EmpleadoID": 1,
    "AreaID": "AREA001",
    "Nombre": "Juan",
    "Apellido": "Perez",
    "DNI": "12345678",
    "Rol": "Operario",
    "FechaHora": "2024-08-31T08:00:00",
    "TipoAcceso": "Ingreso",
    "MetodoAcceso": "Facial",
  }
]
```

#### GET `/accesos/{acceso_id}`

Obtiene información de un acceso específico.

**Parámetros**:

- `acceso_id` (path): ID del acceso

**Respuesta**:

```json
{
  "AccesoID": 1,
  "EmpleadoID": 1,
  "AreaID": "AREA001",
  "Nombre": "Juan",
  "Apellido": "Perez",
  "DNI": "12345678",
  "Rol": "Operario",
  "FechaHora": "2024-08-31T08:00:00",
  "TipoAcceso": "Ingreso",
  "MetodoAcceso": "Facial",
  "DispositivoAcceso": "Dispositivo1",
  "ConfianzaReconocimiento": 0.95,
}
```

#### POST `/accesos/crear`

Crea un nuevo acceso después de reconocer facialmente al empleado.

**Parámetros**:

- `file` (form): Imagen del rostro para reconocimiento
- `tipo_acceso` (form): Tipo de acceso (Ingreso o Egreso)
- `area_id` (form): ID del área donde se intenta el acceso
- `dispositivo` (form, opcional): Dispositivo utilizado (default: "Dispositivo1")
- `observaciones` (form, opcional): Observaciones adicionales

**Validaciones**:

1. **Reconocimiento Facial**: Verifica que se detecte un rostro en la imagen
2. **Empleado Reconocido**: Compara con los rostros registrados en la base de datos
3. **Permisos por Área**: Verifica que el empleado tenga acceso al área solicitada

**Importante**: Solo se registran accesos cuando son **permitidos**. Los intentos fallidos (empleado no reconocido o sin permisos) devuelven error HTTP pero no crean registros en la base de datos.

**Respuesta de Acceso Permitido**:

```json
{
  "message": "Acceso Ingreso registrado correctamente",
  "empleado": {
    "id": 1,
    "nombre": "Juan",
    "apellido": "Perez",
    "rol": "Operario"
  },
  "area_id": "AREA001",
  "tipo_acceso": "Ingreso",
  "confianza": 0.95,
  "acceso_permitido": true
}
```

**Respuesta de Acceso Denegado**:

```json
{
  "detail": "Empleado Juan Perez no tiene acceso al área AREA002"
}
```

#### POST `/accesos/crear_pin` (Acceso con PIN)

Crea un nuevo acceso mediante PIN del empleado.

**Parámetros**:

- `pin` (form): PIN de acceso del empleado
- `tipo_acceso` (form): Tipo de acceso (Ingreso o Egreso)
- `area_id` (form): ID del área donde se intenta el acceso
- `dispositivo` (form, opcional): Dispositivo utilizado (default: "Dispositivo1")
- `observaciones` (form, opcional): Observaciones adicionales

**Validaciones**:

1. **PIN Correcto**: Verifica que el PIN coincida con un empleado
2. **Permisos por Área**: Verifica que el empleado tenga acceso al área solicitada
3. **Estado Activo**: Verifica que el empleado esté activo en el sistema

**Respuesta de Acceso Permitido**:

```json
{
  "message": "Acceso Ingreso por PIN registrado correctamente",
  "empleado": {
    "id": 1,
    "nombre": "Juan",
    "apellido": "Perez",
    "rol": "Operario"
  },
  "area_id": "AREA001",
  "tipo_acceso": "Ingreso",
  "metodo_acceso": "PIN",
  "acceso_permitido": true
}
```

**Respuesta de Acceso Denegado**:

```json
{
  "detail": "PIN incorrecto o empleado no tiene acceso a esta área"
}
```

## Flujo de Trabajo del Sistema

### 1. Registro de Empleados

1. Se crea un empleado en la base de datos
2. Se registra su rostro mediante `/empleados/{id}/registrar_rostro`
3. El sistema almacena el encoding facial del empleado

### 2. Control de Accesos

#### **Acceso por Reconocimiento Facial**:

1. **Empleado se acerca al dispositivo**:

   - Se toma una foto del rostro
   - Se envía al endpoint `/accesos/crear` con método "Facial"

2. **Sistema procesa la solicitud**:

   - Detecta rostro en la imagen
   - Compara con rostros registrados
   - Verifica permisos por área

3. **Resultado del Acceso**:
   - **Permitido**: Se registra entrada/salida en la base de datos y se abre la puerta
   - **Denegado**: Se devuelve error HTTP (sin crear registro) y se mantiene cerrada

#### **Acceso por PIN**:

1. **Empleado ingresa PIN**:

   - Se envía al endpoint `/accesos/crear_pin` con método "PIN"

2. **Sistema procesa la solicitud**:

   - Verifica que el PIN coincida con un empleado
   - Verifica que el empleado tenga acceso al área solicitada
   - Verifica que el empleado esté activo

3. **Resultado del Acceso**:
   - **Permitido**: Se registra entrada/salida en la base de datos y se abre la puerta
   - **Denegado**: Se devuelve error HTTP (sin crear registro) y se mantiene cerrada


## Configuración

### Umbral de Reconocimiento

El umbral de confianza para el reconocimiento facial se puede ajustar en `services/face_recognition_service.py`:

```python
def __init__(self, threshold=0.6):
    self.threshold = threshold  # Ajustar según necesidades
```

### Áreas de Acceso

Las áreas se definen mediante `AreaID` en la base de datos. Cada empleado tiene asignada un área específica.

## Seguridad y Cifrado

### Implementación de Seguridad

#### 1. Almacenamiento Seguro de Datos Biométricos

Los vectores faciales se almacenan de forma segura utilizando cifrado AES-256-GCM, que proporciona:

- **Confidencialidad**: Los datos biométricos están cifrados en reposo
- **Autenticación**: Garantiza que los datos no han sido alterados
- **IV único**: Cada vector se cifra con un vector de inicialización (IV) único

#### 2. Flujo de Autenticación Facial

1. **Registro**:
   - Se extrae el vector facial de la imagen
   - Se genera un IV único
   - El vector se cifra usando AES-256-GCM
   - Se almacenan tanto el vector cifrado como el IV

2. **Autenticación**:
   - Se extrae el vector facial de la imagen de entrada
   - Se recuperan y descifran los vectores almacenados
   - Se compara la similitud con todos los vectores
   - Se valida el acceso según el umbral de confianza

#### 3. Configuración Requerida

```env
# Clave de cifrado (generar con: python -c "import os; print(os.urandom(32).hex())")
VECTOR_ENCRYPTION_KEY=tu_clave_secreta_aqui

# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db

## Ejemplos de Uso

### Registrar Rostro de Empleado

```bash
curl -X POST "http://localhost:8000/empleados/1/registrar_rostro" \
  -F "file=@rostro_juan.jpg"
```

### Crear Acceso por Reconocimiento Facial

```bash
curl -X POST "http://localhost:8000/accesos/crear" \
  -F "file=@rostro_empleado.jpg" \
  -F "tipo_acceso=Ingreso" \
  -F "area_id=AREA001" \
  -F "dispositivo=Dispositivo1"
```

### Crear Acceso por PIN

```bash
curl -X POST "http://localhost:8000/accesos/crear_pin" \
  -F "pin=1234" \
  -F "tipo_acceso=Ingreso" \
  -F "area_id=AREA001" \
  -F "dispositivo=Dispositivo1"
```




### Consultar Accesos

```bash
# Todos los accesos
curl "http://localhost:8000/accesos"

# Accesos de un empleado específico
curl "http://localhost:8000/accesos?empleado_id=1"

# Accesos de un área específica
curl "http://localhost:8000/accesos?area_id=AREA001"
```


## Tecnologías Utilizadas

### Core Framework
- **FastAPI 0.95.2**: Framework web moderno y rápido para construir APIs con Python
- **Uvicorn 0.22.0**: Servidor ASGI para ejecutar aplicaciones FastAPI

### ORM y Bases de Datos
- **SQLAlchemy 1.4.41**: ORM para la interacción con la base de datos
- **Databases 0.6.2**: Soporte asíncrono para bases de datos SQL
- **Pydantic 1.10.7**: Validación de datos y configuración mediante type hints
- **PostgreSQL**: Sistema de base de datos relacional
- **psycopg2**: Adaptador PostgreSQL para Python
- **greenlet 2.0.2**: Soporte para programación asíncrona

### Procesamiento de Imágenes
- **face-recognition 1.3.0**: Biblioteca para reconocimiento facial
- **NumPy 1.24.3**: Soporte para operaciones numéricas y arrays multidimensionales
- **Pillow 9.5.0**: Procesamiento de imágenes


### Utilidades
- **python-multipart 0.0.6**: Manejo de carga de archivos
- **python-dotenv 1.0.0**: Manejo de variables de entorno
- **anyio 3.6.2**: Utilidades de E/S asíncrona
- **starlette 0.27.0**: Framework web ligero en el que se basa FastAPI