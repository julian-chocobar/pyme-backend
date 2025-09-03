import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base

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
