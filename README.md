# Sistema de Gestión de Seguros (Versión Estática - HTML + JS + LocalStorage)

Este proyecto simula un **sistema de gestión de seguros** con **roles de usuario (admin / cliente)**,
implementado completamente en el **navegador**, sin necesidad de servidor PHP ni base de datos activa.

---

## 🚀 Características principales
- Interfaz basada en **Bootstrap 5.3**.
- Control de sesión mediante **LocalStorage**.
- Roles diferenciados:
  - **Admin** → Puede crear, editar o eliminar usuarios y pólizas.
  - **Cliente** → Solo visualiza su póliza.
- Mensajes visuales tipo **notificación flotante** (fade-in / fade-out).
- Sincronización automática entre usuarios y pólizas.
- Diseño adaptable y responsivo.

---

## 🧩 Estructura del proyecto

```
/backend/Header
  header.css           → Estilos del encabezado general

/login
  index.html           → Pantalla de login
  script.js            → Validación de usuario y redirección por rol
  style.css            → Estilos visuales del login
  /app
    dashboard_admin.html   → Panel principal del administrador
    dashboard_cliente.html → Panel del cliente
    clientes_admin.html    → Gestión de clientes
    guard.js               → Controla el acceso por rol
    logout.html / logout.js → Cierre de sesión
/legacy
  header.php / login.php    → Archivos de la versión antigua en PHP (solo referencia)
```

---

## 🧠 Funcionamiento general

1. **Inicio de sesión:**
   - Se valida el usuario ingresado en `index.html`.
   - Si el rol es “admin” → se redirige a `dashboard_admin.html`.
   - Si el rol es “cliente” → se redirige a `dashboard_cliente.html`.

2. **Gestión de usuarios y pólizas (admin):**
   - Los datos se guardan y actualizan en `LocalStorage`.
   - Cada cliente tiene asignada automáticamente una póliza.
   - Mensaje visual confirma las acciones (“✅ Cambios guardados correctamente”).

3. **Clientes:**
   - Ven solo su póliza y vencimiento actual.
   - No pueden modificar datos.

---

## 💡 Modo de uso

1. Abrí `login/index.html` en el navegador (no requiere servidor).
2. Iniciá sesión con alguno de los usuarios demo:
   - Admin: `admin@demo.com` / `Admin123!`
   - Cliente: `cliente@demo.com` / `Cliente123!`
3. ¡Listo! Podés administrar o visualizar las pólizas desde las vistas correspondientes.

---

## 🗂️ Carpeta `legacy/`

Incluye los archivos originales en **PHP + MySQL** (`header.php` y `login.php`)  
para referencia o futura migración a una versión dinámica.

---

## 🧱 Tecnologías utilizadas
- **HTML5**, **CSS3**, **JavaScript ES6**
- **Bootstrap 5.3**
- **LocalStorage API**
- **(Legacy)** PHP 8.x + MySQL (no requerido en esta versión)

---

## 📄 Licencia
Proyecto académico con fines didácticos – libre uso y modificación.
