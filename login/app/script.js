// ============================================
// login/app/script.js
// ============================================
// Versión FINAL — compatible con backend FastAPI actual
// ============================================

const API_URL = SegurAR.apiUrl;

(async function () {

  const form = document.getElementById('loginForm');
  const alertContainer = document.getElementById('alert-container');
  if (!await SegurAR.tabReady) return;
  const tabNotice = sessionStorage.getItem("segurar.tabNotice");
  if (tabNotice) {
    mostrarError(tabNotice);
    sessionStorage.removeItem("segurar.tabNotice");
  }

  // ============================================================
  // LOGIN REAL CON JWT + /auth/me
  // ============================================================
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!form.checkValidity()) {
      form.classList.add("was-validated");
      return;
    }

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
      // 1️⃣ LOGIN → recibir token
      const resp = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        mostrarError(SegurAR.errorMessage(body.detail, "No se pudo iniciar sesión. Intentá nuevamente."));
        return;
      }

      const data = await resp.json(); // { access_token }

      // Guardar token
      // Se guarda solo después de verificar los datos del usuario.

      // 2️⃣ PEDIR DATOS REALES DEL USUARIO
      const meResp = await fetch(`${API_URL}/auth/me`, {
        method: "GET",
        headers: {
          "Authorization": "Bearer " + data.access_token
        }
      });

      if (!meResp.ok) {
        mostrarError("No se pudo obtener el usuario.");
        return;
      }

      const user = await meResp.json();
      sessionStorage.setItem("token", data.access_token);

      // 3️⃣ Guardar información del usuario
      sessionStorage.setItem("userId", user.id);
      sessionStorage.setItem("nombre", user.nombre);
      sessionStorage.setItem("email", user.email);
      sessionStorage.setItem("role", user.role);

      // 4️⃣ Redirigir según el rol
      if (user.role === "admin") {
        window.location.href = "./app/dashboard_admin.html";
      } else if (user.role === "cliente") {
        window.location.href = "./app/dashboard_cliente.html";
      } else {
        mostrarError("Rol desconocido.");
      }

    } catch (err) {
      console.error(err);
      mostrarError("No se pudo conectar con el servidor.");
    }
  });


  // ============================================================
  // Mostrar error
  // ============================================================
  function mostrarError(msg) {
    if (!alertContainer) {
      alert(msg);
      return;
    }
    alertContainer.innerHTML = `
      <div class="alert alert-danger text-center alert-dismissible fade show" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        ${SegurAR.escapeHTML(msg)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>`;
  }

})();
