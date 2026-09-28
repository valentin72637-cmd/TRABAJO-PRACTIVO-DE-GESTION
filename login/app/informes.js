/* Informes: datos como texto, filtros aplicados inmutables y peticiones cancelables. */
const esAdmin = document.body.dataset.role === "admin";
let applied = new URLSearchParams();
let page = 1;
let totalPages = 0;
let ready = false;
let loading = false;
let requestId = 0;
let controller;

function readFilters() {
    const values = new URLSearchParams();
    for (const [key, value] of new FormData(document.getElementById("filtros")))
        if (value) values.set(key, value);
    return values;
}
function element(tag, text, className = "") {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    node.className = className;
    return node;
}
function filterNotice() {
    const dirty = readFilters().toString() !== applied.toString();
    document.getElementById("pendientes").textContent = dirty
        ? "Hay cambios sin aplicar. El listado y el PDF siguen usando los filtros aplicados." : "";
}
function filterDescription(values) {
    if (!values.toString()) return "Filtros aplicados: todas las pólizas disponibles para tu cuenta.";
    const labels = {cliente_id: "Cliente ID", estado: "Estado", tipo: "Tipo",
        vencimiento_desde: "Vence desde", vencimiento_hasta: "Vence hasta"};
    return "Filtros aplicados: " + [...values].map(([key, value]) => labels[key] + ": " + value).join(" | ");
}
function tarjetas(values) {
    const target = document.getElementById("cards"); target.replaceChildren();
    for (const [title, count] of [["Total", values.total_polizas], ["Vigentes", values.vigentes],
        ["Próximas a vencer", values.proximas_a_vencer], ["Vencidas", values.vencidas]]) {
        const col = element("div", undefined, "col-6 col-lg-3");
        const card = element("div", undefined, "card card-body shadow-sm");
        card.append(element("span", title, "text-muted"), element("strong", count, "display-6"));
        col.append(card); target.append(col);
    }
}
function summary(rows) {
    const max = Math.max(0, ...rows.map(row => row.cantidad));
    if (!max) return "No hay pólizas para comparar con estos filtros.";
    const leaders = rows.filter(row => row.cantidad === max).map(row => row.categoria || row.tramo);
    return leaders.length === 1 ? leaders[0] + " tiene la mayor cantidad: " + max + "."
        : "Empatan " + leaders.join(", ") + ", con " + max + " póliza(s) cada categoría.";
}
function chart(id, rows, color) {
    // Barras HTML sin CDN: cantidades visibles y tabla semántica para lectores de pantalla.
    const target = document.getElementById(id); target.replaceChildren();
    const table = element("table", undefined, "table table-sm align-middle");
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const name of ["Categoría", "Comparación", "Cantidad"]) {
        const th = element("th", name); th.scope = "col"; headRow.append(th);
    }
    head.append(headRow); table.append(head);
    const body = document.createElement("tbody");
    const max = Math.max(1, ...rows.map(row => row.cantidad));
    for (const row of rows) {
        const tr = document.createElement("tr");
        const label = element("th", row.categoria || row.tramo); label.scope = "row";
        const graphic = document.createElement("td"); graphic.style.width = "45%";
        const bar = element("div", undefined, "report-bar");
        bar.style.width = (100 * row.cantidad / max) + "%"; bar.style.backgroundColor = color;
        bar.setAttribute("aria-hidden", "true"); graphic.append(bar);
        tr.append(label, graphic, element("td", row.cantidad, "text-end fw-bold")); body.append(tr);
    }
    table.append(body); target.append(table, element("p", summary(rows), "text-muted mb-0"));
}
function tabla(data) {
    const target = document.querySelector("#tabla tbody"); target.replaceChildren();
    if (!data.items.length) {
        const tr = document.createElement("tr");
        const message = applied.toString() ? "No hay pólizas que coincidan con los filtros. Probá limpiar los filtros."
            : "Todavía no hay pólizas disponibles para tu cuenta.";
        const td = element("td", message, "text-center text-muted py-4");
        td.colSpan = esAdmin ? 7 : 6; tr.append(td); target.append(tr);
    }
    for (const policy of data.items) {
        const tr = document.createElement("tr");
        const values = [policy.numero];
        if (esAdmin) values.push(policy.cliente_nombre);
        values.push(policy.tipo, policy.inicio, policy.vencimiento, policy.estado, policy.mensaje || "-");
        for (const value of values) tr.append(element("td", value));
        target.append(tr);
    }
    const pg = data.pagination;
    totalPages = pg.total_pages;
    const navigation = document.getElementById("paginacion"); navigation.replaceChildren();
    if (totalPages) {
        navigation.append(element("span", "Página " + pg.page + " de " + totalPages + " · " + pg.total_items + " póliza(s)"));
        for (const [title, delta, disabled] of [["Anterior", -1, pg.page === 1], ["Siguiente", 1, pg.page >= totalPages]]) {
            const button = element("button", title, "btn btn-sm btn-outline-primary ms-2");
            button.type = "button"; button.disabled = disabled; button.onclick = () => cambiar(delta);
            navigation.append(button);
        }
    }
}
function clearResults() {
    for (const id of ["cards", "porEstado", "porTipo", "porVencer", "resumen", "paginacion"])
        document.getElementById(id).replaceChildren();
    document.querySelector("#tabla tbody").replaceChildren();
}
async function cargar(candidate = applied, targetPage = 1) {
    const id = ++requestId;
    controller?.abort(); controller = new AbortController();
    const snapshot = new URLSearchParams(candidate);
    const listParams = new URLSearchParams(snapshot);
    listParams.set("page", targetPage); listParams.set("page_size", 20);
    loading = true; ready = false; clearResults();
    document.getElementById("exportar").disabled = true;
    document.getElementById("error").textContent = "";
    document.getElementById("cargando").textContent = "Cargando informe…";
    document.getElementById("aplicados").textContent = "Actualizando los filtros del informe…";
    try {
        const responses = await Promise.all([
            SegurAR.request(SegurAR.apiUrl + "/informes/polizas/resumen?" + snapshot, {signal: controller.signal}),
            SegurAR.request(SegurAR.apiUrl + "/informes/polizas/listado?" + listParams, {signal: controller.signal})
        ]);
        const [report, list] = await Promise.all(responses.map(response => response.json()));
        if (id !== requestId) return;
        applied = snapshot; page = targetPage;
        // La tabla se muestra antes de preparar las visualizaciones.
        tabla(list); tarjetas(report.indicadores);
        chart("porEstado", report.por_estado, "#0d6efd");
        chart("porTipo", report.por_tipo, "#198754");
        chart("porVencer", report.vencimientos_por_tramo, "#b45309");
        document.getElementById("resumen").textContent = report.resumen_textual +
            " Fecha de referencia (Argentina): " + report.fecha_referencia + ".";
        document.getElementById("aplicados").textContent = filterDescription(applied);
        ready = true; document.getElementById("exportar").disabled = false; filterNotice();
    } catch (error) {
        if (id !== requestId || error.name === "AbortError") return;
        clearResults();
        document.getElementById("error").textContent = error.message + " Revisá los filtros y pulsá Aplicar para reintentar.";
        document.getElementById("aplicados").textContent = "El informe no está disponible; no se muestran datos anteriores.";
    } finally {
        if (id === requestId) { loading = false; document.getElementById("cargando").textContent = ""; }
    }
}
function cambiar(delta) {
    if (loading || !ready || page + delta < 1 || page + delta > totalPages) return;
    cargar(applied, page + delta);
}
function limpiar() {
    document.getElementById("filtros").reset();
    cargar(readFilters(), 1);
}
async function pdf() {
    if (!ready || loading) return;
    const snapshot = new URLSearchParams(applied);
    const button = document.getElementById("exportar"); button.disabled = true;
    try {
        const response = await SegurAR.request(SegurAR.apiUrl + "/informes/polizas/exportar.pdf?" + snapshot);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url; link.download = "informe_polizas_segurar.pdf";
        document.body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { document.getElementById("error").textContent = error.message; }
    finally { button.disabled = !ready || loading; }
}
async function cargarClientes() {
    if (!esAdmin) return;
    const response = await SegurAR.request(SegurAR.apiUrl + "/users/");
    const users = await response.json();
    const select = document.getElementById("cliente");
    for (const user of users.filter(user => user.role === "cliente")) {
        const option = element("option", user.nombre + " (" + user.email + ")");
        option.value = user.id; select.append(option);
    }
}
document.addEventListener("DOMContentLoaded", async () => {
    if (!await window.segurarReady) return;
    const form = document.getElementById("filtros");
    form.addEventListener("input", filterNotice);
    form.addEventListener("submit", event => { event.preventDefault(); cargar(readFilters(), 1); });
    try { await cargarClientes(); }
    catch (error) { SegurAR.showError("No se pudo cargar el selector de clientes. " + error.message); }
    await cargar(readFilters(), 1);
});
