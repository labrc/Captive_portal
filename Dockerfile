# Imagen base liviana de Python 3.12
FROM python:3.12-slim

# Evitar prompts y logs ruidosos
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Directorio de trabajo
WORKDIR /app

# Copiamos el proyecto (sin config.ini; se montará por volumen)
COPY main.py /app/main.py
COPY database.py /app/database.py
COPY templates/ /app/templates/
COPY services/ /app/services/
COPY static/ /app/static/

# Dependencias
# - fastapi      → API
# - uvicorn      → server ASGI
# - psycopg2-binary → Postgres
# - requests     → UniFi API
# - python-multipart → manejo de forms (Form)
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    gunicorn \
    Jinja2 \
    psycopg2-binary \
    requests \
    python-multipart\
    itsdangerous\
    asyncpg

# Exponemos el puerto
EXPOSE 80

# Comando de inicio
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "1", "--threads", "4", "--timeout", "15", "--keep-alive", "5", "-b", "0.0.0.0:80"]

