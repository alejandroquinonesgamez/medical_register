FROM python:3.10-slim

WORKDIR /app

# Usuario no root (UID 1000) para evitar crear archivos como root en volúmenes montados
RUN useradd --no-create-home --uid 1000 appuser

# Crear directorio instance (el entrypoint ajustará permisos al arrancar)
RUN mkdir -p /app/instance

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

# Copiar entrypoint fuera de /app para evitar que el bind mount lo sobreescriba
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# Copiar el resto de la aplicación
COPY . .

EXPOSE 5001
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

