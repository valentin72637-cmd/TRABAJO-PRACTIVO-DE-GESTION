// ============================================
// login/script.js
// ============================================
// Simula un backend local (sin servidor real)
// Guarda usuarios, sesión y login en localStorage
// ============================================

// === Usuarios de demostración (pre-cargados) ===
const USERS_DEMO = [
  { nombre: 'Administrador Demo', email: 'admin@demo.com', password: 'Admin123!', rol: 'admin' },
  { nombre: 'Cliente Demo', email: 'cliente@demo.com', password: 'Cliente123!', rol: 'cliente' }
];

// Autoejecutable: se ejecuta apenas carga el script
(function () {

  // === Elementos del DOM ===
  const form = document.getElementById('loginForm'); // Formulario principal
  const toggle = document.getElementById('togglePwd'); // Botón de mostrar/ocultar contraseña
  const pwd = document.getElementById('password'); // Campo de contraseña
  const alertContainer = document.getElementById('alert-container'); // Contenedor de alertas

  // ============================================
  // 1️⃣ Mostrar / Ocultar contraseña
  // ============================================
  if (toggle) {
    toggle.addEventListener('click', () => {
      // Alterna entre tipo "password" y "text"
      pwd.type = pwd.type === 'password' ? 'text' : 'password';
    });
  }

  // ============================================
  // 2️⃣ Inicialización de datos demo
  // ============================================
  // Si no hay usuarios almacenados, se crean los de ejemplo
  if (!localStorage.getItem('usuarios')) {
    localStorage.setItem('usuarios', JSON.stringify([
      { nombre: 'Administrador Demo', email: 'admin@demo.com', password: 'Admin123!', rol: 'admin' },
      { nombre: 'Cliente Demo', email: 'cliente@demo.com', password: 'Cliente123!', rol: 'cliente' }
    ]));
  }

  // Si no hay pólizas almacenadas, se crean las demo
  if (!localStorage.getItem('polizas')) {
    const hoy = new Date();
    hoy.setFullYear(hoy.getFullYear() + 1); // vence en 1 año
    const fechaVenc = hoy.toISOString().split('T')[0];

    const polizasDemo = [
      {
        numero: "1001",
        cliente: "Cliente Demo",
        tipo: "Auto",
        vencimiento: fechaVenc
      }
    ];

    localStorage.setItem('polizas', JSON.stringify(polizasDemo));
  }

  // ============================================
  // 3️⃣ Evento de Login (envío del formulario)
  // ============================================
  form?.addEventListener('submit', (e) => {
    e.preventDefault(); // Evita recargar la página

    // Valida campos del formulario
    if (!form.checkValidity()) {
      form.classList.add('was-validated'); // Activa los estilos de validación de Bootstrap
      return;
    }

    // Obtiene los valores ingresados por el usuario
    const email = (document.getElementById('email').value || '').trim().toLowerCase();
    const pass = document.getElementById('password').value;

    // ============================================
    // 4️⃣ Cargar usuarios (demo + locales)
    // ============================================
    const usuariosLocales = JSON.parse(localStorage.getItem('usuarios') || '[]');
    const usuarios = [...USERS_DEMO, ...usuariosLocales]; // Mezcla los arrays (demo + guardados)

    // ============================================
    // 5️⃣ Verifica credenciales ingresadas
    // ============================================
    const user = usuarios.find(u =>
      u.email.toLowerCase() === email && u.password === pass
    );

    // Si no se encuentra el usuario, muestra error
    if (!user) {
      alertContainer.innerHTML = `
        <div class="alert alert-danger text-center">
          Correo o contraseña incorrectos.
        </div>`;
      return;
    }

    // ============================================
    // 6️⃣ Guardar sesión activa
    // ============================================
    const payload = { nombre: user.nombre, email: user.email, rol: user.rol };
    localStorage.setItem('usuario_actual', JSON.stringify(payload)); // Sesión principal
    localStorage.setItem('auth', JSON.stringify(payload));           // Copia auxiliar (por compatibilidad)

    // ============================================
    // 7️⃣ Redirección según el rol
    // ============================================
    if (user.rol === 'admin') {
      window.location.href = "./app/dashboard_admin.html";
    } else {
      window.location.href = "./app/dashboard_cliente.html";
    }
  });

})(); // Fin de la función autoejecutable
