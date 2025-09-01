# Usamos una imagen base con Python 3.9 y herramientas de compilación
FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para compilar dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dlib desde el código fuente
RUN pip install --no-cache-dir dlib

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto en el que correrá la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación cuando el contenedor se ejecute
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
