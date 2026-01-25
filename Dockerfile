FROM python:3.10-slim

WORKDIR /app

# Crear directorio instance
RUN mkdir -p /app/instance

# Instalar Docker CLI para poder ejecutar comandos docker desde el contenedor
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Dependencias para SQLCipher (pysqlcipher3)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libsqlcipher-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias primero (optimización de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

EXPOSE 5001

CMD ["sh", "-c", "python /app/scripts/init_storage.py && gunicorn --bind 0.0.0.0:5001 --workers 1 --timeout 120 run:app"]

