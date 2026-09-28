/* Revocar primero en el servidor; no anunciar éxito si no se pudo contactar. */
(async function closeSession() {
    if (!await SegurAR.tabReady) return;
    const token = sessionStorage.getItem("token");
    if (!token) { SegurAR.clearSession(); location.replace("../index.html"); return; }
    try {
        const response = await fetch(SegurAR.apiUrl + "/auth/logout", {
            method: "POST", headers: {Authorization: "Bearer " + token},
            signal: AbortSignal.timeout(15000)
        });
        if (!response.ok && response.status !== 401) throw new Error("Servidor no disponible");
        if (sessionStorage.getItem("token") === token) {
            SegurAR.clearSession();
            location.replace("../index.html");
        }
    } catch (_) {
        SegurAR.showError("No se pudo cerrar la sesión en el servidor. Volvé a intentar para revocar el acceso.");
    }
})();
