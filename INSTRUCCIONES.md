# Instrucciones para Iniciar CampoEnOrden

Este documento explica paso a paso cómo iniciar el servidor backend (Django) y el servidor frontend (Ionic/Angular).

## 1. Configuración del Backend (Django)

### Prerrequisitos
- Python 3.x instalado
- MySQL Server instalado y ejecutándose
- pip (gestor de paquetes de Python)

### Pasos

1. **Navegar al directorio del backend:**
   ```bash
   cd backend/campoenorden_backend
   ```

2. **Crear y activar un entorno virtual (recomendado):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
   
   O instalar manualmente:
   ```bash
   pip install Django djangorestframework djangorestframework-simplejwt mysqlclient Pillow django-cors-headers
   ```

4. **Configurar la base de datos en `settings.py`:**
   
   Editar `campoenorden_backend/settings.py` y configurar:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'campoenorden_db',
           'USER': 'tu_usuario_mysql',
           'PASSWORD': 'tu_password_mysql',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

5. **Crear la base de datos en MySQL:**
   ```bash
   mysql -u root -p
   CREATE DATABASE campoenorden_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

6. **Realizar migraciones:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Crear superusuario (opcional):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Iniciar el servidor backend:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   
   El backend estará disponible en: http://localhost:8000

## 2. Configuración del Frontend (Ionic/Angular)

### Prerrequisitos
- Node.js instalado (versión LTS recomendada)
- npm (viene con Node.js)
- Ionic CLI

### Pasos

1. **Instalar Ionic CLI globalmente (si no lo tienes):**
   ```bash
   npm install -g @ionic/cli
   ```

2. **Navegar al directorio del frontend:**
   ```bash
   cd frontend/campoenorden_frontend
   ```

3. **Instalar dependencias:**
   ```bash
   npm install
   ```

4. **Configurar la URL del backend:**
   
   Si el backend está en una dirección diferente a `http://localhost:8000`, editar los servicios en `src/app/services/` para apuntar a la URL correcta.

5. **Iniciar el servidor de desarrollo:**
   ```bash
   ionic serve
   ```
   
   El frontend estará disponible en: http://localhost:8100

6. **Para construir la aplicación para producción:**
   ```bash
   ionic build
   ```

7. **Para ejecutar en dispositivo móvil o emulador (requiere Capacitor):**
   ```bash
   ionic cap add android
   ionic cap add ios  # Solo en macOS
   ionic cap sync
   ionic cap open android  # Abre Android Studio
   ```

## 3. Verificación

1. Backend: Visitar http://localhost:8000/admin para acceder al panel de administración
2. Frontend: Visitar http://localhost:8100 para ver la aplicación

## Notas Importantes

- Asegúrate de que el backend esté corriendo antes de iniciar el frontend
- El backend debe tener CORS configurado para aceptar peticiones desde el frontend
- Si cambias los puertos por defecto, actualiza la configuración CORS en el backend
- Para producción, configura correctamente las variables de entorno y secretos

## Solución de Problemas

**Error de conexión a MySQL:**
- Verifica que MySQL esté corriendo: `sudo systemctl status mysql`
- Verifica las credenciales en `settings.py`

**Error de CORS:**
- Asegúrate de que `django-cors-headers` esté instalado y configurado en `settings.py`

**Error de dependencias en frontend:**
- Elimina `node_modules` y `package-lock.json`, luego ejecuta `npm install` nuevamente
