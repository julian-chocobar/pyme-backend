# Sistema de Reconocimiento Facial para Control de Accesos

Este es un backend desarrollado en FastAPI que implementa un sistema de control de accesos mediante reconocimiento facial para PYMEs.

## Características

- **Reconocimiento Facial**: Utiliza la librería `face_recognition` para identificar empleados
- **Control de Accesos**: Registra entradas y salidas con validación de permisos por área
- **Base de Datos PostgreSQL**: Almacena empleados, accesos y datos biométricos
- **API REST**: Endpoints para gestión completa del sistema
- **Validaciones de Seguridad**: Verifica permisos por área y reconoce empleados

## Requisitos del Sistema

- **Python**: 3.8 o superior
- **PostgreSQL**: 12 o superior
- **Sistema Operativo**: Windows, Linux o macOS

## Instalación

1. **Clonar el repositorio**:
```bash
git clone <url-del-repositorio>
cd pyme-backend
```

2. **Crear entorno virtual**:
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

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

**Nota**: La instalación puede tomar varios minutos debido a las dependencias de machine learning (dlib, face_recognition, numpy) que se instalan automáticamente.

5. **Configurar variables de entorno**:
Crear archivo `.env` en la raíz del proyecto:
```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db

# Configuración CORS (orígenes permitidos separados por comas)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

6. **Crear base de datos y tablas**:
```bash
python create_tables.py
```

7. **Ejecutar la aplicación**:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
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


### Error de CORS (Cross-Origin Resource Sharing)
- Verificar que el dominio del frontend esté incluido en `ALLOWED_ORIGINS`
- Asegurar que las URLs en `ALLOWED_ORIGINS` no tengan espacios
- Para desarrollo, incluir `http://localhost:PUERTO` en la configuración

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
- `FechaHoraIngreso`: Fecha y hora de ingreso
- `FechaHoraEgreso`: Fecha y hora de egreso
- `TipoAcceso`: Tipo de acceso (Ingreso o Egreso)
- `MetodoAcceso`: Método utilizado (Facial, PIN, Manual)
- `DispositivoAcceso`: Dispositivo utilizado para el acceso
- `ConfianzaReconocimiento`: Nivel de confianza del reconocimiento facial
- `ObservacionesSeguridad`: Observaciones adicionales
- `AccesoPermitido`: Si el acceso fue permitido o denegado
- `MotivoDenegacion`: Razón de la denegación (si aplica)

## Endpoints de la API

### Empleados

#### GET `/empleados/
Obtiene información de todos los empleados.
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
        "AreaID": 101,
        "DatosBiometricos": null,
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
        "AreaID": 102,
        "DatosBiometricos": null,
        "FechaRegistro": "2025-08-31T18:50:38.384872"
    }
```


#### GET `/empleados/{empleado_id}`
Obtiene información de un empleado específico.

**Parámetros**:
- `empleado_id` (path): ID del empleado

**Respuesta**:
```json
{
  "EmpleadoID": 1,
  "Nombre": "Juan",
  "Apellido": "Perez",
  "DNI": "12345678",
  "Email": "juan.perez@example.com",
  "Rol": "Operario",
  "EstadoEmpleado": "Activo",
  "AreaID": 101
}
```

#### POST `/empleados/{empleado_id}/registrar_rostro`
Registra el rostro de un empleado para reconocimiento facial.

**Parámetros**:
- `empleado_id` (path): ID del empleado
- `file` (form): Imagen del rostro

**Respuesta**:
```json
{
  "message": "Rostro registrado correctamente"
}
```

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
GET /accesos?empleado_id=1&area_id=101&limit=10
```

**Respuesta**:
```json
[
  {
    "AccesoID": 1,
    "EmpleadoID": 1,
    "AreaID": 101,
    "Nombre": "Juan",
    "Apellido": "Perez",
    "DNI": "12345678",
    "Rol": "Operario",
    "FechaHoraIngreso": "2024-08-31T08:00:00",
    "TipoAcceso": "Ingreso",
    "MetodoAcceso": "Facial",
    "AccesoPermitido": "Permitido"
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
  "AreaID": 101,
  "Nombre": "Juan",
  "Apellido": "Perez",
  "DNI": "12345678",
  "Rol": "Operario",
  "FechaHoraIngreso": "2024-08-31T08:00:00",
  "FechaHoraEgreso": "2024-08-31T17:00:00",
  "TipoAcceso": "Ingreso",
  "MetodoAcceso": "Facial",
  "DispositivoAcceso": "Dispositivo1",
  "ConfianzaReconocimiento": 0.95,
  "AccesoPermitido": "Permitido"
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

#### POST `/accesos/crear_pin`
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

### 3. Auditoría y Reportes
- Solo los accesos **permitidos** se registran en la base de datos
- Los intentos fallidos se registran en logs del servidor pero no en la base de datos
- Se puede consultar historial completo de accesos exitosos mediante `/accesos`
- Filtros por empleado, área, fecha, tipo de acceso

## Seguridad

- **Reconocimiento Facial**: Umbral de confianza configurable (default: 0.6)
- **Validación de Permisos**: Verificación estricta de acceso por área
- **Registro Completo**: Todos los intentos de acceso se registran
- **Auditoría**: Trazabilidad completa de movimientos

## Configuración

### Umbral de Reconocimiento
El umbral de confianza para el reconocimiento facial se puede ajustar en `main.py`:
```python
mejor_confianza = 0.6  # Ajustar según necesidades
```

### Áreas de Acceso
Las áreas se definen mediante `AreaID` en la base de datos. Cada empleado tiene asignada un área específica.

### Configuración CORS
El sistema permite configurar los orígenes permitidos mediante la variable de entorno `ALLOWED_ORIGINS`:

**Desarrollo local**:
```env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

**Producción**:
```env
ALLOWED_ORIGINS=https://tu-dominio.com,https://app.tu-dominio.com
```

**Múltiples orígenes**: Separa las URLs con comas sin espacios:
```env
ALLOWED_ORIGINS=https://app1.com,https://app2.com,http://localhost:3000
```

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
- **FastAPI** (0.116.1): Framework web moderno y rápido con documentación automática
- **Uvicorn** (0.35.0): Servidor ASGI para FastAPI

### Reconocimiento Facial y Machine Learning
- **face-recognition** (1.3.0): Librería de reconocimiento facial
- **NumPy** (2.3.2): Computación numérica y arrays

### Base de Datos
- **PostgreSQL**: Base de datos principal
- **SQLAlchemy** (2.0.43): ORM para base de datos
- **Databases** (0.9.0): Biblioteca para trabajar con bases de datos asíncronas

### Validación de Datos
- **Pydantic** (2.11.7): Validación de datos y serialización

### Utilidades
- **Python-multipart** (0.0.20): Manejo de formularios multipart
- **Python-dotenv** (1.1.1): Carga de variables de entorno

### Dependencias Automáticas
Las siguientes dependencias se instalan automáticamente como dependencias transitivas:
- **Starlette**: Framework ASGI base para FastAPI
- **dlib**: Librería de machine learning para visión por computadora
- **Pillow**: Procesamiento de imágenes
- **psycopg2-binary**: Driver PostgreSQL
- **asyncpg**: Driver PostgreSQL asíncrono
- **Pydantic Core**: Core de Pydantic
- **Annotated Types**: Tipos anotados para validación
- **AnyIO**: Biblioteca para programación asíncrona
- **H11**: Implementación del protocolo HTTP/1.1
- **Sniffio**: Detección de bibliotecas asíncronas