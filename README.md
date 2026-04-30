# CampoEnOrden

Sistema de gestión para operaciones agrícolas con backend en Django y frontend móvil en Ionic/Angular.

## Descripción

CampoEnOrden es una aplicación diseñada para la gestión de campos agrícolas, permitiendo administrar labores, logística y operaciones del campo de manera organizada.

## Estructura del Proyecto

```
CampoEnOrden/
├── backend/                    # Servidor Django
│   └── campoenorden_backend/
│       ├── campoenorden_backend/   # Configuración principal
│       │   ├── settings.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       ├── core/               # App principal
│       ├── labores/            # Gestión de labores agrícolas
│       ├── logistica/          # Gestión de logística
│       ├── manage.py
│       └── requirements.txt
├── frontend/                   # Cliente Ionic/Angular
│   └── campoenorden_frontend/
│       ├── src/
│       │   ├── app/
│       │   │   ├── pages/      # Páginas de la aplicación
│       │   │   ├── services/   # Servicios API
│       │   │   └── components/ # Componentes reutilizables
│       │   └── theme/          # Estilos globales
│       ├── package.json
│       └── ionic.config.json
└── docs/                       # Documentación adicional
```

## Backend (Django)

- **Framework**: Django 6.0.4 con Django REST Framework
- **Autenticación**: JWT (djangorestframework-simplejwt)
- **Base de datos**: MySQL
- **Apps**:
  - `core`: Funcionalidad central y autenticación
  - `labores`: Gestión de labores agrícolas
  - `logistica`: Gestión de logística del campo
- **CORS**: Configurado con django-cors-headers para permitir peticiones del frontend

## Frontend (Ionic + Angular)

- **Framework**: Ionic 8 con Angular 20
- **UI Components**: Angular Material
- **Almacenamiento local**: @ionic/storage-angular
- **Capacitor**: Para funcionalidades nativas (Android/iOS)
- **PWA**: Soporte para Progressive Web App

## Requisitos

### Backend
- Python 3.x
- MySQL Server
- Pip (gestor de paquetes de Python)

### Frontend
- Node.js (versión LTS recomendada)
- npm
- Ionic CLI: `npm install -g @ionic/cli`

## Configuración e Instalación

Ver el archivo `INSTRUCCIONES.md` para pasos detallados sobre cómo iniciar el servidor backend y frontend.

## Tecnologías Utilizadas

### Backend
- Django
- Django REST Framework
- Simple JWT
- MySQLclient
- Pillow (manejo de imágenes)
- django-cors-headers

### Frontend
- Ionic Framework
- Angular
- Angular Material
- RxJS
- TypeScript

## Licencia

Proyecto privado - Todos los derechos reservados.
