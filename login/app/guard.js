/* El rol se obtiene del servidor, nunca del sessionStorage. */
window.segurarReady = (async () => {
    const protectedContent = document.querySelector("main") || document.querySelector(".container");
    if (protectedContent) protectedContent.hidden = true;
    if (!await SegurAR.tabReady) return false;
    if (!sessionStorage.getItem("token")) {
        location.replace("../index.html?error=session");
        return false;
    }
    try {
        const response = await SegurAR.request(SegurAR.apiUrl + "/auth/me");
        const user = await response.json();
        const path = location.pathname;
        const expectedRole = document.body.dataset.role ||
            (path.includes("_admin.html") ? "admin" : path.includes("_cliente.html") ? "cliente" : null);
        if (!["admin", "cliente"].includes(user.role) || (expectedRole && user.role !== expectedRole)) {
            SegurAR.showError("No tenés permiso para esta pantalla.");
            return false;
        }
        for (const [key, value] of Object.entries({
            userId: user.id, nombre: user.nombre, email: user.email, role: user.role
        })) sessionStorage.setItem(key, String(value));
        for (const [id, value] of [["username", user.nombre], ["userrole", user.role]]) {
            const node = document.getElementById(id); if (node) node.textContent = value;
        }
        if (protectedContent) protectedContent.hidden = false;
        return true;
    } catch (error) {
        SegurAR.showError(error.message);
        return false;
    }
})();
