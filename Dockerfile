FROM python:3.10-slim

WORKDIR /app

# Usuario no root (UID 1000) para evitar crear archivos como root en volúmenes montados
RUN useradd --no-create-home --uid 1000 appuser

# Crear directorio instance (el entrypoint ajustará permisos al arrancar)
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

# Entrypoint: crea directorios escribibles, chown a appuser y ejecuta la app como no root
RUN chmod +x /app/scripts/docker-entrypoint.sh
EXPOSE 5001
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

