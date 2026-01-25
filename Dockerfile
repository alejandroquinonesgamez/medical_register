FROM python:3.10-slim

WORKDIR /app

# Crear directorio instance
RUN mkdir -p /app/instance

# Copiar e instalar dependencias primero (optimización de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

EXPOSE 5001

CMD ["sh", "-c", "python /app/scripts/init_storage.py && gunicorn --bind 0.0.0.0:5001 --workers 1 --timeout 120 run:app"]

