from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
import os
from dotenv import load_dotenv

# Importar routers
from api.empleados import router as empleados_router
from api.areas import router as areas_router
from api.accesos import router as accesos_router

load_dotenv()

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pyme-frontend-smoky.vercel.app", "http://localhost:5173"],
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

# Incluir routers
app.include_router(empleados_router)
app.include_router(areas_router)
app.include_router(accesos_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)