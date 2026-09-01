FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Puerto de exposición
EXPOSE 8000

# Iniciar servidor Uvicorn
CMD ["python", "run.py"]
