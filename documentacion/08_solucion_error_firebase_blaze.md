# 🛑 Solución al Error "Must be on the Blaze plan" en Firebase

## 🔍 ¿Por qué ocurrió este error?

Firebase introdujo una regla en sus **Cloud Functions de 2ª Generación (Python)**: aunque el uso mensual es **100% gratuito (hasta 2 millones de peticiones/mes)**, Google exige que el proyecto de Firebase esté en el **Plan Blaze (Pay-as-you-go)** para poder compilar el código de Python usando *Google Cloud Build*.

---

## 🛠️ Las 2 Soluciones Posibles

---

### 🟢 Solución 1: Pasarse al Plan Blaze en Firebase ($0.00 de costo real)

Si agregas tu tarjeta a Firebase en el Plan Blaze:
- **Google te regala $300 USD de crédito inicial**.
- La cuota gratuita de 2 millones de ejecuciones al mes **sigue aplicando**.
- Tu factura mensual seguirá siendo de **$0.00 USD** mientras no superes millones de visitas al mes.

**Pasos:**
1. Abre este enlace: [Console Firebase - Detalles de uso](https://console.firebase.google.com/project/dashboard-app-763eb/usage/details)
2. Haz clic en **Modificar plan → Seleccionar Blaze**.
3. Una vez cambiado a Blaze, vuelve a ejecutar en tu terminal:
   ```powershell
   firebase deploy
   ```

---

### 🟢 Solución 2: Render.com (100% Gratis - Sin Tarjeta de Crédito)

Si prefieres **NO ingresar ninguna tarjeta de crédito**, la alternativa gratuita más popular para Python FastAPI es **Render.com**:

1. Registrate en [Render.com](https://render.com) (con GitHub o email).
2. Haz clic en **New → Web Service**.
3. Conecta este repositorio/carpeta.
4. Render detectará Python automáticamente y desplegará tu app en `https://dashboard-reportes.onrender.com`.
5. ¡Listo! Tendrás tu servidor FastAPI corriendo en la nube **sin pagar nada y sin ingresar tarjeta de crédito**.

---

### 🟢 Solución 3: Firebase Hosting Estático + Backend en Render

También puedes dejar los archivos estáticos en Firebase Hosting (que sí es 100% gratis en el plan Spark sin tarjeta):
```powershell
firebase deploy --only hosting
```
Y conectar la API al servidor de Render.
