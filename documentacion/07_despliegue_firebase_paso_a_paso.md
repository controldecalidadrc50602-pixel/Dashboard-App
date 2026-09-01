# 🔥 07. Guía Completa de Despliegue en Firebase

Dado que tu infraestructura principal está en **Firebase** y ya agotaste el límite de Supabase, aquí tienes la solución exacta para desplegar este proyecto en **Firebase** utilizando **Firebase Cloud Functions (Python 2ª Generación)** o **Firebase App Hosting / Cloud Run**.

---

## 🛠️ Método 1: Firebase Cloud Functions Gen 2 (Python + FastAPI) — ¡Recomendado!

Firebase Gen 2 admite funciones nativas en **Python 3.11 / 3.12 / 3.13** y permite envolver tu aplicación **FastAPI** directamente en una sola función HTTP sin modificar la estructura del proyecto.

### Paso 1: Instalar Firebase CLI (si no lo tienes aún)
En tu terminal:
```powershell
npm install -g firebase-tools
```
O inicia sesión en Firebase:
```powershell
firebase login
```

---

### Paso 2: Inicializar Firebase Functions en la carpeta del proyecto

En la carpeta del proyecto (`dashboard-reportes`):
```powershell
firebase init functions
```
- Selecciona tu proyecto Firebase existente de la lista.
- Elige **Python** como lenguaje.
- Acepta instalar las dependencias con `pip`.

---

### Paso 3: Configurar el archivo `main.py` de la función Firebase

En la carpeta `functions/main.py` (o en la raíz), envuelve la app FastAPI:

```python
from firebase_functions import https_fn
from app.main import app as fastapi_app

# Envolver la app FastAPI como una función HTTP de Firebase
@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    return https_fn.wsgi_app(fastapi_app)(req)
```

---

### Paso 4: Base de Datos en Firebase (Firestore o Cloud SQL)

Para almacenar tus datos en Firebase tienes 2 opciones gratuitas:

#### Opción A: Base de datos SQLite persistente mediante Cloud Storage / Local
Si quieres conservar SQLite sin reescribir nada, se puede guardar el archivo `dashboard.db` en un bucket de **Firebase Storage**.

#### Opción B: Firebase Firestore (Recomendado)
Firebase Firestore te da **1 GB de almacenamiento gratis y 50,000 lecturas diarias**.
Se conecta mediante `firebase-admin` en Python:
```powershell
pip install firebase-admin
```

---

### Paso 5: Desplegar a Firebase
Ejecuta:
```powershell
firebase deploy --only functions
```

¡Firebase te entregará una URL pública de producción tipo:
`https://us-central1-tu-proyecto-firebase.cloudfunctions.net/api`!

---

## 🐋 Método 2: Firebase App Hosting / Cloud Run (Con Dockerfile)

Si prefieres usar un contenedor Docker completo que corra tu `run.py` con Uvicorn:

### 1. Archivo `Dockerfile` en la raíz del proyecto:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run.py"]
```

### 2. Desplegar a Google Cloud / Firebase Cloud Run:
```powershell
gcloud run deploy dashboard-reportes --source . --region us-central1 --allow-unauthenticated
```

---

## 📌 Comparativa de Costos en Firebase (Plan Spark Gratis)

| Recurso | Límite Gratuito Mensual Firebase | Tu Uso Estimado | Costo |
|---------|----------------------------------|------------------|-------|
| **Cloud Functions (Python)** | 2.000.000 peticiones / mes | ~5.000 / mes | **$0.00** |
| **Firestore Database** | 50.000 lecturas / 20.000 escrituras por día | ~500 / día | **$0.00** |
| **Firebase Hosting** | 10 GB almacenamiento / 360 MB/día transferencia | ~2 GB / mes | **$0.00** |
