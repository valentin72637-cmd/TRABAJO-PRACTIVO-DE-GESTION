// ===============================================================
// dashboard_admin.js
// Panel Admin con JWT + FastAPI
// ===============================================================

const API_URL = SegurAR.apiUrl;
// La validación de acceso se centraliza en guard.js y SegurAR.tabReady.

let usuariosCache = [];
let polizasCache = [];

// No leer credenciales antes de inicializar la sesión de esta pestaña.

// ---------------------------------------------------------------
// 🔹 Función auxiliar para llamadas con token
// ---------------------------------------------------------------
async function api(url, method = "GET", body = null) {
    if (!await window.segurarReady) throw new Error("No se pudo validar el acceso a esta pantalla.");
    const options = {method};
    if (body !== null) {
        options.headers = {"Content-Type": "application/json"};
        options.body = JSON.stringify(body);
    }
    try {
        const response = await SegurAR.request(url, options);
        return response.status === 204 ? null : await response.json();
    } catch (error) {
        SegurAR.showError(error.message);
        throw error;
    }
}

// ---------------------------------------------------------------
// USUARIOS
// ---------------------------------------------------------------
async function cargarUsuarios() {
    try {
        const data = await api(
            `${API_URL}/users/`
        );

        if (!data) {
            return;
        }

        // Guardamos una copia para editar/buscar
        usuariosCache = data;

        renderizarUsuarios(
            usuariosCache
        );

    } catch (error) {
        console.error(
            "Error cargando usuarios:",
            error
        );
    }
}

function renderizarUsuarios(usuarios) {

    const tbody =
        document.querySelector(
            "#tablaUsuarios tbody"
        );

    if (!tbody) {
        console.error(
            "No se encontró #tablaUsuarios tbody"
        );
        return;
    }

    tbody.innerHTML = "";


    // -------------------------------------------------------
    // SIN RESULTADOS
    // -------------------------------------------------------

    if (usuarios.length === 0) {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td
                colspan="5"
                class="text-center text-muted py-4"
            >
                No se encontraron usuarios.
            </td>
        `;

        tbody.appendChild(fila);

        return;
    }


    // -------------------------------------------------------
    // MOSTRAR USUARIOS
    // -------------------------------------------------------

    usuarios.forEach(usuario => {

        const row = `
            <tr>
                <td>${usuario.id}</td>

                <td>${SegurAR.escapeHTML(usuario.nombre)}</td>

                <td>${SegurAR.escapeHTML(usuario.email)}</td>

                <td>${SegurAR.escapeHTML(usuario.role)}</td>

                <td>
                    <button
                        class="btn btn-warning btn-sm"
                        onclick="editarUsuario(${usuario.id})"
                    >
                        Editar
                    </button>

                    <button
                        class="btn btn-danger btn-sm"
                        onclick="eliminarUsuario(${usuario.id})"
                    >
                        Eliminar
                    </button>
                </td>
            </tr>
        `;

        tbody.insertAdjacentHTML(
            "beforeend",
            row
        );
    });
}

//Abrir formulario para nuevo usuario

function abrirNuevoUsuario() {

    const form =
        document.getElementById(
            "formUsuario"
        );

    form.reset();

    document.getElementById(
        "userIndex"
    ).value = "";

    document.getElementById(
        "tituloUsuario"
    ).textContent = "Nuevo Usuario";

    document.getElementById(
        "urol"
    ).value = "cliente";


    // Contraseña obligatoria al crear
    const inputPassword =
        document.getElementById(
            "upass"
        );

    inputPassword.required = true;

    inputPassword.placeholder =
        "Elegí una contraseña nueva (mínimo 8 caracteres)";


    // Habilitar selector de póliza
    actualizarCampoTipoPoliza();


    document.getElementById(
        "guardarUsuario"
    ).textContent = "Guardar";
}

// ===============================================================
// Controlar tipo de póliza según el rol
// ===============================================================

function actualizarCampoTipoPoliza() {
    const rol = document.getElementById("urol").value;
    const tipoPoliza = document.getElementById("utipopoliza");
    const helpTipo = document.getElementById("helpTipo");

    if (rol === "cliente") {
        tipoPoliza.disabled = false;
        tipoPoliza.required = true;

        helpTipo.textContent =
            "Seleccione el tipo de póliza que tendrá el cliente.";
    } else {
        tipoPoliza.disabled = true;
        tipoPoliza.required = false;
        tipoPoliza.value = "Auto";

        helpTipo.textContent =
            "Los administradores no poseen póliza.";
    }
}

// Crear usuario
async function crearUsuario() {
    try {
        // =====================================================
        // 1. LEER DATOS DEL FORMULARIO
        // =====================================================

        const nombre =
            document.getElementById("uname").value.trim();

        const email =
            document.getElementById("uemail").value.trim();

        const password =
            document.getElementById("upass").value;

        const role =
            document.getElementById("urol").value;

        const tipoPoliza =
            document.getElementById("utipopoliza").value;


        // =====================================================
        // 2. VALIDACIONES
        // =====================================================

        if (!nombre || !email || !password || !role) {
            alert("Complete todos los campos obligatorios.");
            return;
        }

        if (password.length < 8) {
            alert(
                "La contraseña debe tener al menos 8 caracteres."
            );
            return;
        }


        // =====================================================
        // 3. CREAR USUARIO
        // =====================================================

        await api(
            `${API_URL}/users/`, "POST",
            {nombre, email, password, role, tipo_poliza: role === "cliente" ? tipoPoliza : null}
        );


        // =====================================================
        // 5. CERRAR MODAL
        // =====================================================

        const modalElemento =
            document.getElementById("modalUsuario");

        const modal =
            bootstrap.Modal.getInstance(
                modalElemento
            );

        if (modal) {
            modal.hide();
        }


        // =====================================================
        // 6. LIMPIAR FORMULARIO
        // =====================================================

        document
            .getElementById("formUsuario")
            .reset();


        // =====================================================
        // 7. ACTUALIZAR TABLAS
        // =====================================================

        await cargarUsuarios();
        await cargarPolizas();


        // =====================================================
        // 8. MENSAJE FINAL
        // =====================================================

        if (role === "cliente") {

            alert(
                "Cliente y póliza creados correctamente."
            );

        } else {

            alert(
                "Administrador creado correctamente."
            );
        }

    } catch (error) {

        console.error(
            "Error creando usuario:",
            error
        );

        alert(
            error.message ||
            "No se pudo crear el usuario."
        );
    }
}

// Editar usuario
function editarUsuario(id) {

    const usuario =
        usuariosCache.find(
            u => u.id === id
        );

    if (!usuario) {
        alert(
            "No se encontró el usuario."
        );
        return;
    }


    // Guardar ID que estamos editando
    document.getElementById(
        "userIndex"
    ).value = usuario.id;


    // Cambiar título
    document.getElementById(
        "tituloUsuario"
    ).textContent = "Editar Usuario";


    // Cargar datos actuales
    document.getElementById(
        "uname"
    ).value = usuario.nombre;

    document.getElementById(
        "uemail"
    ).value = usuario.email;

    document.getElementById(
        "urol"
    ).value = usuario.role;


    // La contraseña queda vacía.
    // Solo se modifica si el admin escribe una nueva.
    const inputPassword =
        document.getElementById(
            "upass"
        );

    inputPassword.value = "";

    inputPassword.required = false;

    inputPassword.placeholder =
        "Dejar vacío para conservar la actual";


    // La póliza se editará desde la pestaña Pólizas.
    const tipoPoliza =
        document.getElementById(
            "utipopoliza"
        );

    tipoPoliza.disabled = true;
    tipoPoliza.required = false;

    document.getElementById(
        "helpTipo"
    ).textContent =
        "La póliza del cliente se modifica desde la pestaña Pólizas.";


    // Cambiar texto del botón
    document.getElementById(
        "guardarUsuario"
    ).textContent = "Guardar cambios";


    // Abrir modal Bootstrap
    const modalElemento =
        document.getElementById(
            "modalUsuario"
        );

    const modal =
        bootstrap.Modal.getOrCreateInstance(
            modalElemento
        );

    modal.show();
}

async function actualizarUsuario() {

    try {

        const id =
            document.getElementById(
                "userIndex"
            ).value;


        if (!id) {
            return;
        }


        const nombre =
            document.getElementById(
                "uname"
            ).value.trim();

        const email =
            document.getElementById(
                "uemail"
            ).value.trim();

        const role =
            document.getElementById(
                "urol"
            ).value;

        const password =
            document.getElementById(
                "upass"
            ).value;


        // -----------------------------------------------------
        // VALIDACIONES
        // -----------------------------------------------------

        if (!nombre || !email || !role) {
            alert(
                "Nombre, email y rol son obligatorios."
            );
            return;
        }


        // Solo validar contraseña si se escribió una nueva
        if (
            password &&
            password.length < 8
        ) {
            alert(
                "La nueva contraseña debe tener al menos 8 caracteres."
            );
            return;
        }


        // -----------------------------------------------------
        // PREPARAR DATOS
        // -----------------------------------------------------

        const datosActualizados = {
            nombre,
            email,
            role
        };


        // No enviar contraseña vacía
        if (password) {
            datosActualizados.password =
                password;
        }


        // -----------------------------------------------------
        // PUT
        // -----------------------------------------------------

        const usuarioActualizado =
            await api(
                `${API_URL}/users/${id}`,
                "PUT",
                datosActualizados
            );


        console.log(
            "Usuario actualizado:",
            usuarioActualizado
        );


        // -----------------------------------------------------
        // CERRAR MODAL
        // -----------------------------------------------------

        const modalElemento =
            document.getElementById(
                "modalUsuario"
            );

        const modal =
            bootstrap.Modal.getInstance(
                modalElemento
            );

        if (modal) {
            modal.hide();
        }


        // -----------------------------------------------------
        // ACTUALIZAR TABLAS
        // -----------------------------------------------------

        await cargarUsuarios();

        // Importante:
        // si cambió el nombre de un cliente,
        // la tabla de pólizas también debe actualizarlo.
        await cargarPolizas();


        alert(
            "Usuario actualizado correctamente."
        );

    } catch (error) {

        console.error(
            "Error actualizando usuario:",
            error
        );

        alert(
            error.message ||
            "No se pudo actualizar el usuario."
        );
    }
}

async function procesarGuardadoUsuario() {

    const id =
        document.getElementById(
            "userIndex"
        ).value;

    if (id) {
        await actualizarUsuario();
    } else {
        await crearUsuario();
    }
}

// Eliminar usuario
async function eliminarUsuario(id) {

    // -------------------------------------------------------
    // BUSCAR EL USUARIO
    // -------------------------------------------------------

    const usuario =
        usuariosCache.find(
            u => u.id === id
        );

    if (!usuario) {
        alert(
            "No se encontró el usuario."
        );
        return;
    }


    // -------------------------------------------------------
    // PROTEGER AL ADMINISTRADOR QUE ESTÁ LOGUEADO
    // -------------------------------------------------------

    const usuarioActualId =
        Number(
            sessionStorage.getItem(
                "userId"
            )
        );

    if (usuario.id === usuarioActualId) {

        alert(
            "No puedes eliminar tu propio usuario mientras tienes la sesión iniciada."
        );

        return;
    }


    // -------------------------------------------------------
    // ADVERTENCIA PARA CLIENTES
    // -------------------------------------------------------

    let mensaje =
        `¿Está seguro de eliminar al usuario "${usuario.nombre}"?`;

    if (usuario.role === "cliente") {

        mensaje +=
            "\n\nTambién se eliminarán las pólizas asociadas a este cliente.";
    }


    const confirmar =
        confirm(mensaje);

    if (!confirmar) {
        return;
    }


    // -------------------------------------------------------
    // DELETE
    // -------------------------------------------------------

    try {

        await api(
            `${API_URL}/users/${usuario.id}`,
            "DELETE"
        );


        // Actualizar ambas tablas
        await cargarUsuarios();
        await cargarPolizas();


        alert(
            "Usuario eliminado correctamente."
        );

    } catch (error) {

        console.error(
            "Error eliminando usuario:",
            error
        );

        alert(
            error.message ||
            "No se pudo eliminar el usuario."
        );
    }
}

function filtrarUsuarios() {

    const buscador =
        document.getElementById(
            "buscarUsuario"
        );

    if (!buscador) {
        return;
    }


    const texto =
        buscador.value
            .trim()
            .toLowerCase();


    // Si está vacío mostramos todos
    if (!texto) {

        renderizarUsuarios(
            usuariosCache
        );

        return;
    }


    const usuariosFiltrados =
        usuariosCache.filter(
            usuario => {

                return (
                    String(usuario.nombre)
                        .toLowerCase()
                        .includes(texto)

                    ||

                    String(usuario.email)
                        .toLowerCase()
                        .includes(texto)

                    ||

                    String(usuario.role)
                        .toLowerCase()
                        .includes(texto)

                    ||

                    String(usuario.id)
                        .includes(texto)
                );
            }
        );


    renderizarUsuarios(
        usuariosFiltrados
    );
}

// ---------------------------------------------------------------
// PÓLIZAS
// ---------------------------------------------------------------
async function cargarPolizas() {
    try {
        console.log("Solicitando pólizas...");

        const [polizas, usuarios] = await Promise.all([
            api(`${API_URL}/polizas/`),
            api(`${API_URL}/users/`)
        ]);

        polizasCache = polizas;
        usuariosCache = usuarios;

        console.log(
            "Pólizas recibidas:",
            polizasCache
        );

        renderizarPolizas(
            polizasCache
        );

    } catch (error) {
        console.error(
            "Error cargando pólizas:",
            error
        );
    }
}

function renderizarPolizas(polizas) {

    const tbody =
        document.querySelector(
            "#tablaPolizas tbody"
        );

    if (!tbody) {
        console.error(
            "No se encontró #tablaPolizas tbody"
        );
        return;
    }

    tbody.innerHTML = "";


    // Crear relación ID → nombre
    const usuariosPorId = {};

    usuariosCache.forEach(usuario => {
        usuariosPorId[usuario.id] =
            usuario.nombre;
    });


    // Si no hay resultados
    if (polizas.length === 0) {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td
                colspan="6"
                class="text-center text-muted py-4"
            >
                No se encontraron pólizas.
            </td>
        `;

        tbody.appendChild(fila);

        return;
    }


    polizas.forEach(poliza => {

        const nombreCliente =
            usuariosPorId[poliza.cliente_id]
            || `Cliente ID ${poliza.cliente_id}`;

        const row = `
            <tr>
                <td>${poliza.id}</td>

                <td>${SegurAR.escapeHTML(poliza.numero)}</td>

                <td>${SegurAR.escapeHTML(nombreCliente)}</td>

                <td>${SegurAR.escapeHTML(poliza.tipo)}</td>

                <td>${SegurAR.escapeHTML(poliza.vencimiento)}</td>

                <td>
                    <button
                        class="btn btn-warning btn-sm"
                        onclick="editarPoliza(${poliza.id})"
                    >
                        Editar
                    </button>

                    <button
                        class="btn btn-danger btn-sm"
                        onclick="eliminarPoliza(${poliza.id})"
                    >
                        Eliminar
                    </button>
                </td>
            </tr>
        `;

        tbody.insertAdjacentHTML(
            "beforeend",
            row
        );
    });
}

function cargarClientesEnSelect(clienteSeleccionado = null) {

    const select =
        document.getElementById("cliente");

    if (!select) {
        console.error(
            "No se encontró el selector #cliente"
        );
        return;
    }

    select.innerHTML = `
        <option value="">
            Seleccione un cliente
        </option>
    `;

    const clientes =
        usuariosCache.filter(
            usuario => usuario.role === "cliente"
        );

    clientes.forEach(cliente => {

        const option =
            document.createElement("option");

        option.value = cliente.id;
        option.textContent =
            `${cliente.nombre} - ${cliente.email}`;

        if (
            clienteSeleccionado !== null &&
            Number(cliente.id) ===
            Number(clienteSeleccionado)
        ) {
            option.selected = true;
        }

        select.appendChild(option);
    });
}

function abrirNuevaPoliza() {

    // Limpiar formulario
    document
        .getElementById("formPoliza")
        .reset();


    // Sin ID = nueva póliza
    document.getElementById(
        "polizaIndex"
    ).value = "";


    // Título
    document.getElementById(
        "tituloPoliza"
    ).textContent = "Nueva Póliza";


    // Cargar clientes
    cargarClientesEnSelect();


    // -------------------------------------------------------
    // Fecha inicial = hoy
    // -------------------------------------------------------

    const hoy =
        new Date();

    const convertirFecha = fecha =>
        SegurAR.localDate(fecha);

    document.getElementById(
        "inicio"
    ).value = convertirFecha(hoy);


    // -------------------------------------------------------
    // Vencimiento = un año
    // -------------------------------------------------------

    const vencimiento =
        new Date(hoy);

    vencimiento.setFullYear(
        vencimiento.getFullYear() + 1
    );

    document.getElementById(
        "vencimiento"
    ).value =
        convertirFecha(vencimiento);


    // Valores predeterminados
    document.getElementById(
        "tipo"
    ).value = "Auto";

    document.getElementById(
        "estado"
    ).value = "Vigente";

    document.getElementById(
        "mensaje"
    ).value = "Póliza Auto activa";


    // -------------------------------------------------------
    // Número automático
    // -------------------------------------------------------

    const numeroAutomatico =
        `POL-${Date.now()
            .toString()
            .slice(-8)}`;

    document.getElementById(
        "numero"
    ).value =
        numeroAutomatico;


    document.getElementById(
        "guardarPoliza"
    ).textContent = "Guardar";


    // Abrir modal
    const modal =
        bootstrap.Modal.getOrCreateInstance(
            document.getElementById(
                "modalPoliza"
            )
        );

    modal.show();
}

function editarPoliza(id) {

    const poliza =
        polizasCache.find(
            p => p.id === id
        );

    if (!poliza) {
        alert(
            "No se encontró la póliza."
        );
        return;
    }


    // ID de la póliza que editamos
    document.getElementById(
        "polizaIndex"
    ).value = poliza.id;


    // Título
    document.getElementById(
        "tituloPoliza"
    ).textContent = "Editar Póliza";


    // Cargar clientes
    cargarClientesEnSelect(
        poliza.cliente_id
    );


    // Cargar datos actuales
    document.getElementById(
        "numero"
    ).value =
        poliza.numero;

    document.getElementById(
        "tipo"
    ).value =
        poliza.tipo;

    document.getElementById(
        "inicio"
    ).value =
        poliza.inicio;

    document.getElementById(
        "vencimiento"
    ).value =
        poliza.vencimiento;

    document.getElementById(
        "estado"
    ).value =
        poliza.estado;

    document.getElementById(
        "mensaje"
    ).value =
        poliza.mensaje || "";


    document.getElementById(
        "guardarPoliza"
    ).textContent =
        "Guardar cambios";


    // Abrir modal
    const modal =
        bootstrap.Modal.getOrCreateInstance(
            document.getElementById(
                "modalPoliza"
            )
        );

    modal.show();
}

async function eliminarPoliza(id) {

    const poliza =
        polizasCache.find(
            p => p.id === id
        );

    if (!poliza) {
        alert(
            "No se encontró la póliza."
        );
        return;
    }


    const confirmar =
        confirm(
            `¿Está seguro de eliminar la póliza ${poliza.numero}?`
        );

    if (!confirmar) {
        return;
    }


    try {

        await api(
            `${API_URL}/polizas/${id}`,
            "DELETE"
        );

        await cargarPolizas();

        alert(
            "Póliza eliminada correctamente."
        );

    } catch (error) {

        console.error(
            "Error eliminando póliza:",
            error
        );

        alert(
            error.message ||
            "No se pudo eliminar la póliza."
        );
    }
}

function filtrarPolizas() {

    const buscador =
        document.getElementById(
            "buscarPoliza"
        );

    const texto =
        buscador.value
            .trim()
            .toLowerCase();


    if (!texto) {
        renderizarPolizas(
            polizasCache
        );
        return;
    }


    const filtradas =
        polizasCache.filter(poliza => {

            const cliente =
                usuariosCache.find(
                    usuario =>
                        usuario.id ===
                        poliza.cliente_id
                );

            const nombreCliente =
                cliente
                    ? cliente.nombre
                    : "";


            return (
                String(poliza.numero)
                    .toLowerCase()
                    .includes(texto)

                ||

                String(poliza.tipo)
                    .toLowerCase()
                    .includes(texto)

                ||

                String(nombreCliente)
                    .toLowerCase()
                    .includes(texto)

                ||

                String(poliza.vencimiento)
                    .toLowerCase()
                    .includes(texto)

                ||

                String(poliza.estado)
                    .toLowerCase()
                    .includes(texto)
            );
        });


    renderizarPolizas(
        filtradas
    );
}

async function guardarDatosPoliza() {

    try {

        const id =
            document.getElementById(
                "polizaIndex"
            ).value;

        const numero =
            document.getElementById(
                "numero"
            ).value.trim();

        const clienteId =
            document.getElementById(
                "cliente"
            ).value;

        const tipo =
            document.getElementById(
                "tipo"
            ).value;

        const inicio =
            document.getElementById(
                "inicio"
            ).value;

        const vencimiento =
            document.getElementById(
                "vencimiento"
            ).value;

        const estado =
            document.getElementById(
                "estado"
            ).value;

        const mensaje =
            document.getElementById(
                "mensaje"
            ).value.trim();


        // ===================================================
        // VALIDACIONES
        // ===================================================

        if (
            !numero ||
            !clienteId ||
            !tipo ||
            !inicio ||
            !vencimiento ||
            !estado
        ) {
            alert(
                "Complete todos los campos obligatorios."
            );

            return;
        }


        if (
            new Date(vencimiento) <
            new Date(inicio)
        ) {
            alert(
                "La fecha de vencimiento no puede ser anterior a la fecha de inicio."
            );

            return;
        }


        const datosPoliza = {
            numero,
            tipo,
            inicio,
            vencimiento,
            estado,
            mensaje: mensaje || null,
            cliente_id: Number(clienteId)
        };


        // ===================================================
        // EDITAR
        // ===================================================

        if (id) {

            await api(
                `${API_URL}/polizas/${id}`,
                "PUT",
                datosPoliza
            );

        } else {

            // =================================================
            // CREAR
            // =================================================

            await api(
                `${API_URL}/polizas/`,
                "POST",
                datosPoliza
            );
        }


        // ===================================================
        // CERRAR MODAL
        // ===================================================

        const modal =
            bootstrap.Modal.getInstance(
                document.getElementById(
                    "modalPoliza"
                )
            );

        if (modal) {
            modal.hide();
        }


        // Actualizar tabla
        await cargarPolizas();


        if (id) {
            alert(
                "Póliza actualizada correctamente."
            );
        } else {
            alert(
                "Póliza creada correctamente."
            );
        }

    } catch (error) {

        console.error(
            "Error guardando póliza:",
            error
        );

        alert(
            error.message ||
            "No se pudo guardar la póliza."
        );
    }
}

// ---------------------------------------------------------------
// ACTUALIZAR MENSAJE SEGÚN EL TIPO DE PÓLIZA
// ---------------------------------------------------------------
function actualizarMensajePoliza() {

    const tipo =
        document.getElementById(
            "tipo"
        ).value;

    const mensaje =
        document.getElementById(
            "mensaje"
        );

    if (!mensaje) {
        return;
    }

    const mensajes = {
        Auto: "Póliza Auto activa",
        Hogar: "Protección completa del hogar",
        Vida: "Póliza Vida activa",
        Salud: "Póliza Salud activa"
    };

    mensaje.value =
        mensajes[tipo] ||
        `Póliza ${tipo} activa`;
}
// ===============================================================
// FONDOS ROTATIVOS DEL PANEL ADMIN
// ===============================================================

function iniciarFondosRotativos() {

    const fondos = document.querySelectorAll(
        "#fondoRotativo .fondo-imagen"
    );

    // Comprobar que existan imágenes
    if (fondos.length === 0) {
        console.warn(
            "No se encontraron imágenes para los fondos rotativos."
        );
        return;
    }

    // Si solamente hay una imagen, dejarla visible
    if (fondos.length === 1) {
        fondos[0].classList.add("active");
        return;
    }

    let indiceActual = 0;

    // Asegurar que inicialmente solo esté visible la primera
    fondos.forEach((fondo, indice) => {
        fondo.classList.toggle(
            "active",
            indice === 0
        );
    });

    console.log(
        `Fondos rotativos iniciados: ${fondos.length} imágenes`
    );

    // Cambiar de fondo cada 8 segundos
    setInterval(() => {

        // Quitar active de la imagen actual
        fondos[indiceActual]
            .classList.remove("active");

        // Pasar a la siguiente imagen
        indiceActual =
            (indiceActual + 1) %
            fondos.length;

        // Mostrar la nueva imagen
        fondos[indiceActual]
            .classList.add("active");

        console.log(
            `Fondo activo: ${indiceActual + 1}`
        );

    }, 8000);
}
// ---------------------------------------------------------------
// INICIALIZACIÓN
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {

    cargarUsuarios();
    cargarPolizas();

    // Iniciar rotación de fondos
    iniciarFondosRotativos();

    // Detectar cambio entre cliente y admin
    document
        .getElementById("urol")
        .addEventListener("change", actualizarCampoTipoPoliza);

    // Guardar nuevo usuario
    document
        .getElementById("guardarUsuario")
        .addEventListener(
            "click",
            procesarGuardadoUsuario
        );
    // -------------------------------------------------------
    // NUEVA PÓLIZA
    // -------------------------------------------------------

    const btnNuevaPoliza =
        document.getElementById(
            "btnNuevaPoliza"
        );

    if (btnNuevaPoliza) {
        btnNuevaPoliza.addEventListener(
            "click",
            abrirNuevaPoliza
        );
    }


    // -------------------------------------------------------
    // GUARDAR PÓLIZA
    // -------------------------------------------------------

    const btnGuardarPoliza =
        document.getElementById(
            "guardarPoliza"
        );

    if (btnGuardarPoliza) {
        btnGuardarPoliza.addEventListener(
            "click",
            guardarDatosPoliza
        );
    }

    // -------------------------------------------------------
    // CAMBIO DE TIPO
    // -------------------------------------------------------

    const selectTipo =
        document.getElementById(
            "tipo"
        );

    if (selectTipo) {
        selectTipo.addEventListener(
            "change",
            actualizarMensajePoliza
        );
    }
    // -------------------------------------------------------
    // BUSCAR PÓLIZAS
    // -------------------------------------------------------

    const buscarPoliza =
        document.getElementById(
            "buscarPoliza"
        );

    if (buscarPoliza) {

        buscarPoliza.addEventListener(
            "input",
            filtrarPolizas
        );
    }

    // -------------------------------------------------------
    // BUSCAR USUARIOS
    // -------------------------------------------------------

    const buscarUsuario =
        document.getElementById(
            "buscarUsuario"
        );

    if (buscarUsuario) {

        buscarUsuario.addEventListener(
            "input",
            filtrarUsuarios
        );
    }
    // =======================================================
    // CONTROL DE OPACIDAD DEL FONDO - PANEL ADMIN
    // =======================================================

    const fondoRotativo =
        document.getElementById("fondoRotativo");

    const sliderOpacidad =
        document.getElementById("sliderOpacidad");

    const btnResetOpacidad =
        document.getElementById("btnResetOpacidad");

    if (
        fondoRotativo &&
        sliderOpacidad &&
        btnResetOpacidad
    ) {

        const OPACIDAD_PREDETERMINADA = 0.9;

        // ---------------------------------------------------
        // Recuperar valor guardado
        // ---------------------------------------------------

        const opacidadGuardada =
            localStorage.getItem(
                "segurar_admin_opacidad"
            );

        const opacidadInicial =
            opacidadGuardada !== null
                ? Number(opacidadGuardada)
                : OPACIDAD_PREDETERMINADA;

        // Aplicar al comenzar
        sliderOpacidad.value =
            opacidadInicial;

        fondoRotativo.style.setProperty(
            "--overlay-opacity",
            opacidadInicial
        );


        // ---------------------------------------------------
        // Mover slider
        // ---------------------------------------------------

        sliderOpacidad.addEventListener(
            "input",
            () => {

                const valor =
                    Number(
                        sliderOpacidad.value
                    );

                fondoRotativo.style.setProperty(
                    "--overlay-opacity",
                    valor
                );

                localStorage.setItem(
                    "segurar_admin_opacidad",
                    valor
                );
            }
        );


        // ---------------------------------------------------
        // RESTABLECER
        // ---------------------------------------------------

        btnResetOpacidad.addEventListener(
            "click",
            () => {

                sliderOpacidad.value =
                    OPACIDAD_PREDETERMINADA;

                fondoRotativo.style.setProperty(
                    "--overlay-opacity",
                    OPACIDAD_PREDETERMINADA
                );

                localStorage.setItem(
                    "segurar_admin_opacidad",
                    OPACIDAD_PREDETERMINADA
                );
            }
        );

    } else {

        console.warn(
            "No se encontraron los controles de opacidad del panel administrador."
        );
    }

});
