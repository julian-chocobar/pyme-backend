# Etapa 1: Build - Instalar dependencias del sistema y de Python
FROM python:3.9-slim as builder

# Actualizar e instalar dependencias del sistema necesarias para compilar dlib (para face_recognition)
# Esto puede tardar varios minutos la primera vez que se construye.
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libdlib-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos e instalar las dependencias de Python
COPY requirements.txt .

# Usamos --no-cache-dir para no guardar el caché de pip y mantener la imagen ligera
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: Final - Crear la imagen de producción, más ligera
FROM python:3.9-slim

# Instalar solo las librerías de sistema necesarias para EJECUTAR la aplicación, no para compilarla
RUN apt-get update && apt-get install -y \
    libdlib1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar las dependencias de Python ya instaladas desde la etapa de 'builder'
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que correrá la aplicación
# Uvicorn por defecto usa el puerto 8000. Render puede asignar uno diferente con la variable PORT.
EXPOSE 8000

# Comando para iniciar la aplicación cuando el contenedor se ejecute
# El host 0.0.0.0 es crucial para que la app sea accesible desde fuera del contenedor.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
