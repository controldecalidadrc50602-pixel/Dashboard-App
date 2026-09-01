# 🚀 06. Guía de Despliegue en Vercel, Firebase y Supabase

Esta guía explica paso a paso cómo desplegar la aplicación a producción de manera gratuita y profesional.

---

## ⚠️ Aspecto Clave antes de Desplegar

En tu equipo local usamos **SQLite (`dashboard.db`)**. Sin embargo, las plataformas Serverless como **Vercel** o **Firebase Hosting** reinician su disco en cada petición, por lo que **SQLite local no guarda cambios**.

Para desplegar en la nube existen dos caminos sencillos:

---

## 🌐 Opción A: Vercel + Supabase PostgreSQL (Recomendada para Vercel)

Esta opción te da **hosting gratis en Vercel** y **Base de Datos gratis en Supabase**.

### Paso 1: Crear la Base de Datos Gratis en Supabase
1. Ingresa a [supabase.com](https://supabase.com) y crea una cuenta gratuita.
2. Crea un nuevo proyecto (ej: `dashboard-reportes`).
3. Ve a **Project Settings → Database → Connection String → URI**.
4. Copia la URL de conexión (se ve así):
   `postgresql://postgres:[TU_PASSWORD]@db.xxxx.supabase.co:5432/postgres`

### Paso 2: Crear el archivo `vercel.json` en el proyecto
Crea un archivo llamado `vercel.json` en la raíz de la carpeta `dashboard-reportes/`:

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### Paso 3: Subir a Vercel
1. Ingresa a [vercel.com](https://vercel.com) e inicia sesión con tu cuenta de GitHub.
2. Haz clic en **Import Project** y selecciona la carpeta o repositorio de `dashboard-reportes`.
3. En la sección **Environment Variables** (Variables de entorno), agrega:
   - `DATABASE_URL`: La URL de Supabase (reemplazando `postgresql://` si aplica).
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: `TuClaveSegura123`
   - `SECRET_KEY`: `UnaClaveSecretaMuyLargaYSegura`
4. Haz clic en **Deploy**. ¡Vercel te entregará una URL pública `.vercel.app` en 2 minutos!

---

## 🚅 Opción B: Railway.app (La opción más fácil - 1 Clic)

Railway te permite desplegar el servidor Python completo sin configurar Postgres manualmente ni hacer cambios.

1. Ingresa a [railway.app](https://railway.app) y crea una cuenta.
2. Haz clic en **New Project → Deploy from GitHub repo** (o usa el CLI de Railway).
3. Agrega las variables de entorno en la pestaña **Variables**:
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: `TuClaveSegura123`
   - `SECRET_KEY`: `ClaveSecreta123`
4. Railway detectará `requirements.txt` y `run.py` automáticamente y te generará tu URL pública de producción `https://dashboard-reportes.up.railway.app`.

---

## 🔥 Opción C: Firebase (Hosting / Cloud Run)

Si prefieres la suite de Google / Firebase:

1. **Firebase Hosting (Frontend Estático):** Si compilas el frontend como estático.
2. **Google Cloud Run / Firebase App Hosting:** Puedes empaquetar el proyecto con Docker / Cloud Run conectándolo a una base de datos Cloud SQL o Supabase.

---

## 📌 Resumen de Recomendación

| Plataforma | Dificultad | Base de Datos | Costo |
|------------|------------|---------------|-------|
| **Railway** | 🟢 Muy Fácil | SQLite o Postgres | Gratis |
| **Vercel + Supabase** | 🟡 Fácil | Supabase Postgres | Gratis |
| **Firebase Cloud Run** | 🔴 Intermedio | Cloud SQL | Gratis (Tier) |
