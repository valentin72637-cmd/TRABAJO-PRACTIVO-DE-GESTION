/* Utilidades compartidas: no interpretar datos de la API como HTML. */
window.SegurAR = (() => {
    const apiUrl = window.SEGURAR_API_URL || "http://127.0.0.1:8000";
    const keys = ["token", "userId", "nombre", "email", "role", "auth", "usuario_actual"];
    function clearSession() {
        for (const key of keys) sessionStorage.removeItem(key);
    }
    // sessionStorage puede ser copiado al duplicar una pestaña. Un lease por ID
    // evita usar en dos pestañas el mismo JWT heredado, sin revocarlo en la original.
    let releaseTabLock = () => {};
    let leaving = false;
    window.addEventListener("pagehide", () => { leaving = true; releaseTabLock(); });
    window.addEventListener("pageshow", event => {
        if (event.persisted) location.reload(); // Revalidar identidad al volver desde BFCache.
    });
    function claimTab(id) {
        return new Promise((resolve, reject) => {
            navigator.locks.request("segurar-tab:" + id, {ifAvailable: true}, async lock => {
                if (!lock) { resolve(false); return; }
                const held = new Promise(release => { releaseTabLock = release; });
                if (leaving) releaseTabLock();
                resolve(!leaving);
                await held;
            }).catch(reject);
        });
    }
    const tabReady = (async () => {
        try {
            if (!navigator.locks || !crypto.randomUUID) {
                throw new Error("Las sesiones por pestaña requieren un navegador actualizado en localhost, 127.0.0.1 o HTTPS.");
            }
            let id = sessionStorage.getItem("segurar.tabId");
            if (!id) {
                // No adoptar credenciales antiguas o copiadas sin identificador de pestaña.
                clearSession();
                id = crypto.randomUUID();
                sessionStorage.setItem("segurar.tabId", id);
            }
            if (!await claimTab(id)) {
                if (leaving) return false;
                clearSession(); // Solo la copia local; no llamar /auth/logout.
                sessionStorage.setItem("segurar.tabNotice",
                    "Esta pestaña necesita su propio inicio de sesión. La sesión de la otra pestaña sigue activa.");
                id = crypto.randomUUID();
                sessionStorage.setItem("segurar.tabId", id);
                if (!await claimTab(id)) throw new Error("No se pudo inicializar esta pestaña. Volvé a cargar.");
            }
            return true;
        } catch (error) {
            showError(error.message || "No se pudo acceder al almacenamiento de esta pestaña.");
            return false;
        }
    })();
    function errorMessage(detail, fallback = "No se pudo completar la operación.") {
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) return detail.map(x =>
            (Array.isArray(x.loc) ? x.loc.filter(k => k !== "body" && k !== "query").join(".") + ": " : "") +
            (x.msg || "Valor inválido")).join("; ");
        return fallback;
    }
    function showError(message) {
        let box = document.getElementById("error-global");
        if (!box) {
            box = document.createElement("div");
            box.id = "error-global"; box.className = "alert alert-danger m-3";
            box.setAttribute("role", "alert"); document.body.prepend(box);
        }
        box.replaceChildren(document.createTextNode(message + " "));
        const retry = document.createElement("button");
        retry.type = "button"; retry.className = "btn btn-sm btn-outline-danger";
        retry.textContent = "Volver a cargar"; retry.onclick = () => location.reload();
        box.append(retry);
    }
    async function request(url, options = {}) {
        if (!await tabReady) throw new Error("La sesión de esta pestaña no está disponible.");
        const headers = new Headers(options.headers || {});
        const token = sessionStorage.getItem("token");
        if (token) headers.set("Authorization", "Bearer " + token);
        let response;
        try { response = await fetch(url, {...options, headers}); }
        catch (error) {
            if (error.name === "AbortError") throw error;
            throw new Error("No se pudo conectar. Tu sesión se conserva; intentá nuevamente.");
        }
        if (response.status === 401) {
            // Un 401 tardío de la identidad anterior no debe borrar un login más reciente.
            if (sessionStorage.getItem("token") === token) {
                clearSession(); location.replace("../index.html?error=session");
            }
            throw new Error("La sesión venció. Iniciá sesión nuevamente.");
        }
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(errorMessage(body.detail, "Error del servidor (" + response.status + ")."));
        }
        return response;
    }
    const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g,
        c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
    const localDate = value => [value.getFullYear(),
        String(value.getMonth() + 1).padStart(2, "0"),
        String(value.getDate()).padStart(2, "0")].join("-");
    return {apiUrl, tabReady, clearSession, errorMessage, showError, request, escapeHTML, localDate};
})();
