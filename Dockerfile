# Imagen de la app web: Python 3.12 slim con las dependencias; arranca con gunicorn.
FROM python:3.12-slim

# Sin archivos .pyc, la salida sin búfer (los logs se ven al instante) y la hora de La Paz en los logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/La_Paz

WORKDIR /app

# Primero solo las dependencias: si el código cambia, Docker reutiliza esta capa.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
