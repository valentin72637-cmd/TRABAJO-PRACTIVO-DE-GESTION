# Sistema de Gestión de Seguros (Versión Actual -- FastAPI + SQLite + Frontend Moderno)

## Actualización de seguridad y QA (27/09/2026)

Ver [CORRECCIONES_QA.md](CORRECCIONES_QA.md) para los cambios, pruebas y pasos actualizados de inicio con Python 3.13.
Las sesiones anteriores deben renovarse. Las claves demo publicadas están bloqueadas; usar el comando local de restablecimiento indicado en esa guía. Ya no se crean cuentas demo al arrancar.
Las contraseñas nuevas usan PBKDF2-SHA256; bcrypt se mantiene únicamente para migrar credenciales antiguas.

Proyecto académico desarrollado para la gestión de usuarios y pólizas de seguros.
SegurAR integra un frontend desarrollado con HTML, CSS, Bootstrap y JavaScript con un backend REST desarrollado en FastAPI, utilizando SQLite como base de datos y autenticación mediante JWT.
El sistema posee dos tipos de usuarios:
- Administrador
- Cliente
Cada rol dispone de funcionalidades y permisos diferentes.
------------------------------------------------------------------------

## 🚀 Características principales

### 🔒 Autenticación y Seguridad

El sistema utiliza autenticación mediante JSON Web Token (JWT).
Características implementadas:
- Inicio de sesión mediante email y contraseña.
- Contraseñas nuevas almacenadas con PBKDF2-SHA256; migración de bcrypt heredado.
- Token JWT con tiempo de expiración.
- Protección de endpoints mediante FastAPI.
- Protección de rutas del frontend.
- Control de acceso basado en roles.
- Endpoint OAuth2 para autenticación desde Swagger.
- Validación del usuario autenticado mediante `/auth/me`.
Endpoints principales de autenticación:
```text
POST /auth/login	es utilizado por el frontend de SegurAR.
POST /auth/token	permite utilizar el botón Authorize de Swagger mediante OAuth2.
GET  /auth/me
------------------------------------------------------------------------

### Roles del sistema
Administrador
El administrador puede:

•	Consultar usuarios.
•	Crear usuarios.
•	Editar usuarios.
•	Eliminar usuarios.
•	Buscar usuarios.
•	Consultar pólizas.
•	Crear pólizas.
•	Editar pólizas.
•	Eliminar pólizas.
•	Buscar pólizas.
•	Asignar pólizas a clientes.
•	Crear automáticamente una póliza al registrar un nuevo cliente.

También existen controles de seguridad para impedir:
•	Que el administrador elimine su propia cuenta durante una sesión.
•	Que el último administrador del sistema sea eliminado.
•	Que el último administrador pierda su rol.
•	Que un cliente con pólizas asignadas sea convertido en administrador.
•	Emails duplicados.
•	Contraseñas demasiado cortas.
Cliente
El cliente puede:

•	Iniciar sesión.
•	Consultar sus datos personales.
•	Ver exclusivamente las pólizas asociadas a su cuenta.
•	Consultar:
    o	Número de póliza.
    o	Tipo.
    o	Fecha de inicio.
    o	Fecha de vencimiento.
    o	Estado.
•	Visualizar fondos dinámicos según el tipo de póliza.
•	Regular la opacidad del fondo.
•	Restablecer la opacidad.
•	Contactar a un asesor.

Un cliente nunca puede visualizar las pólizas pertenecientes a otros usuarios.
------------------------------------------------------------------------


### Tecnologías utilizadas
Backend
•	Python
•	FastAPI
•	Uvicorn
•	SQLAlchemy
•	SQLite
•	Pydantic 2
•	python-jose
•	Passlib
•	bcrypt
•	python-dotenv
•	python-multipart
Frontend
•	HTML5
•	CSS3
•	JavaScript
•	Bootstrap 5.3
•	Bootstrap Icons
•	Google Fonts
Seguridad
•	JWT
•	OAuth2PasswordBearer
•	bcrypt
•	Validación mediante Pydantic
•	Autorización basada en roles

------------------------------------------------------------------------

## 🧩 Estructura del proyecto

   TFi/
│
├── backend/
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── polizas.py
│   │
│   ├── __init__.py
│   ├── auth_utils.py
│   ├── database.py
│   ├── init_demo.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── login/
│   │
│   ├── app/
│   │   │
│   │   ├── assets/
│   │   │   └── fondos/
│   │   │
│   │   ├── dashboard_admin.html
│   │   ├── dashboard_admin.js
│   │   ├── dashboard_cliente.html
│   │   ├── dashboard_cliente.js
│   │   ├── guard.js
│   │   ├── logout.html
│   │   └── logout.js
│   │
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── segurar.db
------------------------------------------------------------------------

## Base de datos

El proyecto utiliza SQLite.

Archivo:
    segurar.db

La conexión y manejo de sesiones de SQLAlchemy se realiza desde:
    backend/database.py
-------------------------------------------------------------------------

##Tablas principales

usuarios

    Campos principales:
        id
        nombre
        email
        password
        role

    Roles permitidos:
        admin
        cliente

El campo email es único.

Las contraseñas nuevas se almacenan utilizando PBKDF2-SHA256. Las claves bcrypt existentes se migran al iniciar sesión.
-------------------------------------------------------------------------------------

## Polizas

Campos principales:
    id
    numero
    tipo
    inicio
    vencimiento
    estado
    mensaje
    cliente_id

Tipos de póliza permitidos:
    Auto
    Hogar
    Vida
    Salud

Estados permitidos:
    Vigente
    Por vencer
    Vencida

La relación principal es:
    Usuario 1 ───────── N Pólizas

cliente_id funciona como clave foránea hacia usuarios.id.

Al eliminar un cliente también se eliminan las pólizas relacionadas de acuerdo con la configuración de la relación.

### Validaciones implementadas

El backend valida los datos antes de almacenarlos.

Usuarios
Se valida:
    Nombre obligatorio.
    Email válido.
    Email único.
    Contraseña mínima de 8 caracteres.
    Roles permitidos.
    Protección del administrador autenticado.
    Protección del último administrador.
------------------------------------------------------------------------

## Pólizas
Se valida:
    Número de póliza obligatorio.
    Número de póliza único.
    Cliente existente.
    El usuario asignado debe tener rol cliente.
    Tipo de póliza válido.
    Estado válido.
    cliente_id mayor que cero.
    Fecha de vencimiento no anterior a la fecha de inicio.

Estas validaciones se realizan utilizando Pydantic y reglas adicionales implementadas en los routers.
------------------------------------------------------------------------

##API REST

La API utiliza el prefijo correspondiente a cada recurso.

Autenticación
POST /auth/login
POST /auth/token
GET  /auth/me
------------------------------------------------------------------------

##Usuarios
    GET    /users/
    POST   /users/
    PUT    /users/{user_id}
    DELETE /users/{user_id}

También existe un endpoint utilizado por los clientes para consultar asesores disponibles:
    GET /users/asesores
Las operaciones administrativas requieren un token perteneciente a un usuario con rol admin.
------------------------------------------------------------------------

##Pólizas
    GET    /polizas/
    POST   /polizas/
    PUT    /polizas/{poliza_id}
    DELETE /polizas/{poliza_id}

Para clientes:
    GET /polizas/mias

Este endpoint devuelve exclusivamente las pólizas cuyo cliente_id coincide con el usuario autenticado.
------------------------------------------------------------------------

##Instalación
1. Abrir el proyecto

Abrir en Visual Studio Code la carpeta raíz:
    TRABAJO-PRACTIVO-DE-GESTION

Es importante ejecutar los comandos desde esta carpeta y no desde backend.
------------------------------------------------------------------------

2. Crear un entorno virtual

En PowerShell:
    python -m venv .venv
------------------------------------------------------------------------

3. Activar el entorno virtual

En Windows PowerShell:
    .\.venv\Scripts\Activate.ps1

La terminal debería mostrar:
    (.venv)
------------------------------------------------------------------------

4. Instalar dependencias

Ejecutar:
    pip install -r requirements.txt

El archivo requirements.txt incluye las dependencias necesarias para ejecutar SegurAR.
------------------------------------------------------------------------
  
