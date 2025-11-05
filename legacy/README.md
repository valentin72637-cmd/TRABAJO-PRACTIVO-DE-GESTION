# Módulo de Login - Gestión de Seguros (PHP + MySQL + Bootstrap)

## Requisitos
- PHP 8.x
- MySQL/MariaDB
- Servidor web (Apache recomendado)

## Instalación
1. Importá la base:
   ```sql
   SOURCE database/seguros.sql;
   ```
2. Configurá credenciales en `backend/db.php`.
3. Iniciá el servidor (por ejemplo, XAMPP/MAMP/WAMP).
4. Ejecutá una vez `backend/seed_users.php` en el navegador para crear los usuarios demo.
5. Abrí `login/index.html` en el navegador y probá:

- Admin: `admin@demo.com` / `Admin123!` → redirige a `dashboard_admin.php`
- Cliente: `cliente@demo.com` / `Cliente123!` → redirige a `dashboard_cliente.php`

## Estructura
```
/login
  index.html
  style.css
  script.js
/backend
  db.php
  login.php
  logout.php
  dashboard_admin.php
  dashboard_cliente.php
  seed_users.php
/database
  seguros.sql
README.md
```

## Seguridad
- Contraseñas: `password_hash` / `password_verify`.
- Sesiones con `session_regenerate_id`.
- Consultas preparadas en login y seed.
- Roles y verificación de acceso por archivo.

> Este módulo se basa en los requerimientos del documento del curso y es 100% extensible.
