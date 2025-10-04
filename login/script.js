// Validación simple + toggle de contraseña + alertas por querystring
(function () {
  const form = document.getElementById('loginForm');
  const toggle = document.getElementById('togglePwd');
  const pwd = document.getElementById('password');
  const alertContainer = document.getElementById('alert-container');

  toggle.addEventListener('click', () => {
    pwd.type = pwd.type === 'password' ? 'text' : 'password';
  });

  form.addEventListener('submit', (e) => {
    if (!form.checkValidity()) {
      e.preventDefault();
      e.stopPropagation();
    }
    form.classList.add('was-validated');
  }, false);

  // Mostrar alertas desde ?error=code
  const params = new URLSearchParams(window.location.search);
  const err = params.get('error');
  if (err) {
    let msg = 'Ocurrió un error.';
    if (err === 'invalid') msg = 'Correo o contraseña incorrectos.';
    if (err === 'required') msg = 'Completá tus credenciales.';
    if (err === 'session') msg = 'Necesitás iniciar sesión.';
    if (err === 'role') msg = 'No tenés permisos para acceder a esa sección.';
    alertContainer.innerHTML = `<div class="alert alert-danger" role="alert">${msg}</div>`;
  }
})();
