// ===============================================================
// dashboard_cliente.js
// Panel Cliente con JWT + FastAPI
// ===============================================================

const API_URL = SegurAR.apiUrl;
// La validación de acceso se centraliza en guard.js y SegurAR.tabReady.

// No leer credenciales antes de inicializar la sesión de esta pestaña.


// ===============================================================
// FUNCIÓN AUXILIAR PARA API
// ===============================================================

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


// ===============================================================
// CARGAR DATOS DEL CLIENTE
// ===============================================================

async function cargarDatosUsuario() {
    try {
        const datos = await api(
            `${API_URL}/auth/me`
        );

        if (!datos) {
            return;
        }

        console.log(
            "Cliente autenticado:",
            datos
        );

        // Nombre
        const clienteNombre =
            document.getElementById("clienteNombre");

        if (clienteNombre) {
            clienteNombre.textContent =
                datos.nombre;
        }

        // Email
        // Solo se modifica si existe en el HTML
        const clienteEmail =
            document.getElementById("clienteEmail");

        if (clienteEmail) {
            clienteEmail.textContent =
                datos.email;
        }

        // Rol
        // Solo se modifica si existe en el HTML
        const clienteRol =
            document.getElementById("clienteRol");

        if (clienteRol) {
            clienteRol.textContent =
                datos.role;
        }

    } catch (error) {
        console.error(
            "Error cargando datos del cliente:",
            error
        );
    }
}


// ===============================================================
// CARGAR PÓLIZAS DEL CLIENTE
// ===============================================================

async function cargarMisPolizas() {
    try {
        console.log(
            "Solicitando pólizas del cliente..."
        );

        const data = await api(
            `${API_URL}/polizas/mias`
        );

        if (!data) {
            return;
        }

        console.log(
            "Pólizas recibidas:",
            data
        );

        const tbody =
            document.querySelector(
                "#tablaMisPolizas tbody"
            );

        if (!tbody) {
            console.error(
                "No se encontró #tablaMisPolizas tbody"
            );
            return;
        }

        tbody.innerHTML = "";


        // -------------------------------------------------------
        // CLIENTE SIN PÓLIZAS
        // -------------------------------------------------------

        if (data.length === 0) {
            const fila =
                document.createElement("tr");

            const celda =
                document.createElement("td");

            celda.colSpan = 6;

            celda.className =
                "text-center text-muted py-4";

            celda.textContent =
                "No tienes pólizas asignadas actualmente.";

            fila.appendChild(celda);
            tbody.appendChild(fila);

            actualizarResumenSinPoliza();

            return;
        }


        // -------------------------------------------------------
        // MOSTRAR PÓLIZAS
        // -------------------------------------------------------

        data.forEach(p => {
            const tr =
                document.createElement("tr");

            agregarCelda(tr, p.id);
            agregarCelda(tr, p.numero);
            agregarCelda(tr, p.tipo);
            agregarCelda(tr, p.inicio);
            agregarCelda(tr, p.vencimiento);
            agregarCelda(tr, p.estado);

            tbody.appendChild(tr);
        });


        // -------------------------------------------------------
        // USAMOS LA PRIMERA PÓLIZA COMO PÓLIZA PRINCIPAL
        // -------------------------------------------------------

        const polizaPrincipal = data[0];

        aplicarFondoPorTipo(
            polizaPrincipal.tipo
        );

        actualizarResumenPoliza(
            polizaPrincipal
        );

    } catch (error) {
        console.error(
            "Error cargando pólizas:",
            error
        );
    }
}


// ===============================================================
// CREAR CELDA DE TABLA
// ===============================================================

function agregarCelda(fila, valor) {
    const td =
        document.createElement("td");

    td.textContent =
        valor ?? "-";

    fila.appendChild(td);
}


// ===============================================================
// FONDOS SEGÚN TIPO DE PÓLIZA
// ===============================================================

let intervaloFondos = null;

function aplicarFondoPorTipo(tipo) {

    const tipos = {
        Auto: "auto",
        Hogar: "hogar",
        Vida: "vida",
        Salud: "salud"
    };

    const prefijo = tipos[tipo];

    if (!prefijo) {
        console.warn(
            "Tipo de póliza sin fondo definido:",
            tipo
        );
        return;
    }


    const imagenes = [
        `assets/fondos/${prefijo}1.jpg`,
        `assets/fondos/${prefijo}2.jpg`,
        `assets/fondos/${prefijo}3.jpg`
    ];


    // Si había una rotación anterior,
    // detenerla.
    if (intervaloFondos) {
        clearInterval(intervaloFondos);
        intervaloFondos = null;
    }


    let indiceActual = 0;


    // -----------------------------------------------------------
    // Mostrar primera imagen
    // -----------------------------------------------------------

    document.body.style.backgroundImage =
        `url("${imagenes[indiceActual]}")`;

    document.body.style.backgroundSize =
        "cover";

    document.body.style.backgroundPosition =
        "center";

    document.body.style.backgroundAttachment =
        "fixed";

    document.body.style.backgroundRepeat =
        "no-repeat";


    console.log(
        "Fondo aplicado:",
        imagenes[indiceActual]
    );


    // -----------------------------------------------------------
    // Rotar cada 5 segundos
    // -----------------------------------------------------------

    intervaloFondos = setInterval(
        () => {

            indiceActual =
                (indiceActual + 1)
                % imagenes.length;

            document.body.style.backgroundImage =
                `url("${imagenes[indiceActual]}")`;

            console.log(
                "Nuevo fondo:",
                imagenes[indiceActual]
            );

        },
        5000
    );
}

// ===============================================================
// TEXTO DINÁMICO SEGÚN TIPO
// ===============================================================

function actualizarResumenPoliza(poliza) {
    const mensajeTipo =
        document.getElementById(
            "mensajeTipoPoliza"
        );

    const resumen =
        document.getElementById(
            "resumenPoliza"
        );


    const textos = {
        Auto:
            "Tu póliza Auto protege tu vehículo y te acompaña en cada viaje.",

        Hogar:
            "Tu póliza Hogar protege tu vivienda y los bienes más importantes.",

        Vida:
            "Tu póliza Vida brinda respaldo y tranquilidad para vos y tu familia.",

        Salud:
            "Tu póliza Salud te brinda protección y respaldo para cuidar tu bienestar."
    };


    if (mensajeTipo) {
        mensajeTipo.textContent =
            textos[poliza.tipo]
            || "Tu póliza te brinda protección y tranquilidad.";
    }


    if (resumen) {

        resumen.classList.remove(
            "d-none"
        );

        resumen.classList.add(
            "alert-info"
        );

        resumen.textContent =
            poliza.mensaje
            || `Póliza ${poliza.tipo} - Estado: ${poliza.estado}`;
    }
}


// ===============================================================
// CLIENTE SIN PÓLIZA
// ===============================================================

function actualizarResumenSinPoliza() {
    const mensajeTipo =
        document.getElementById(
            "mensajeTipoPoliza"
        );

    const resumen =
        document.getElementById(
            "resumenPoliza"
        );


    if (mensajeTipo) {
        mensajeTipo.textContent =
            "Actualmente no tienes una póliza asignada.";
    }


    if (resumen) {

        resumen.classList.remove(
            "d-none"
        );

        resumen.classList.add(
            "alert-warning"
        );

        resumen.textContent =
            "Comunícate con un asesor para obtener información.";
    }
}


// ===============================================================
// CONTROL DE OPACIDAD
// ===============================================================

function inicializarControlOpacidad() {

    const slider =
        document.getElementById(
            "sliderOpacidad"
        );

    const botonReset =
        document.getElementById(
            "btnResetOpacidad"
        );

    const overlay =
        document.getElementById(
            "overlay"
        );


    // -----------------------------------------------------------
    // Comprobar elementos
    // -----------------------------------------------------------

    if (!slider) {
        console.error(
            "No se encontró #sliderOpacidad"
        );
        return;
    }

    if (!overlay) {
        console.error(
            "No se encontró #overlay"
        );
        return;
    }


    const OPACIDAD_INICIAL = 0.9;


    // -----------------------------------------------------------
    // Aplicar valor
    // -----------------------------------------------------------

    function aplicarOpacidad(valor) {

        overlay.style.setProperty(
            "--overlay-opacity",
            valor
        );

        console.log(
            "Opacidad del overlay:",
            valor
        );
    }


    // -----------------------------------------------------------
    // Estado inicial
    // -----------------------------------------------------------

    slider.value =
        OPACIDAD_INICIAL;

    aplicarOpacidad(
        OPACIDAD_INICIAL
    );


    // -----------------------------------------------------------
    // Slider
    // -----------------------------------------------------------

    slider.addEventListener(
        "input",
        () => {

            aplicarOpacidad(
                slider.value
            );
        }
    );


    // -----------------------------------------------------------
    // Botón restablecer
    // -----------------------------------------------------------

    if (botonReset) {

        botonReset.addEventListener(
            "click",
            () => {

                slider.value =
                    OPACIDAD_INICIAL;

                aplicarOpacidad(
                    OPACIDAD_INICIAL
                );

                console.log(
                    "Opacidad restablecida a 0.9"
                );
            }
        );
    }
}

// ===============================================================
// CONTACTAR ASESOR
// ===============================================================

async function cargarAsesores() {
    try {
        const asesores = await api(
            `${API_URL}/users/asesores`
        );

        const lista =
            document.getElementById(
                "listaAsesores"
            );

        if (!lista) {
            console.error(
                "No se encontró #listaAsesores"
            );
            return;
        }

        lista.innerHTML = "";


        // -------------------------------------------------------
        // SIN ASESORES
        // -------------------------------------------------------

        if (!asesores || asesores.length === 0) {

            const mensaje =
                document.createElement("div");

            mensaje.className =
                "text-muted text-center py-3";

            mensaje.textContent =
                "No hay asesores disponibles.";

            lista.appendChild(mensaje);

            return;
        }


        // -------------------------------------------------------
        // MOSTRAR ASESORES
        // -------------------------------------------------------

        asesores.forEach(asesor => {

            const item =
                document.createElement("div");

            item.className =
                "list-group-item " +
                "d-flex justify-content-between " +
                "align-items-center";


            // Datos
            const datos =
                document.createElement("div");

            const nombre =
                document.createElement("strong");

            nombre.textContent =
                asesor.nombre;


            const email =
                document.createElement("div");

            email.className =
                "text-muted small";

            email.textContent =
                asesor.email;


            datos.appendChild(nombre);
            datos.appendChild(email);


            // Botón correo
            const boton =
                document.createElement("a");

            boton.className =
                "btn btn-outline-primary btn-sm";

            boton.href =
                `mailto:${asesor.email}`;

            boton.innerHTML =
                '<i class="bi bi-envelope"></i> Escribir';


            item.appendChild(datos);
            item.appendChild(boton);

            lista.appendChild(item);
        });


    } catch (error) {

        console.error(
            "Error cargando asesores:",
            error
        );
    }
}

// ===============================================================
// INICIALIZACIÓN
// ===============================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        console.log(
            "dashboard_cliente.js iniciado"
        );

        inicializarControlOpacidad();

        await cargarDatosUsuario();

        await cargarMisPolizas();


        // =======================================================
        // BOTÓN CONTACTAR ASESOR
        // =======================================================

        const btnAsesor =
            document.getElementById(
                "btnAsesor"
            );

        if (btnAsesor) {

            btnAsesor.addEventListener(
                "click",
                async () => {

                    await cargarAsesores();

                    const modalElemento =
                        document.getElementById(
                            "modalAsesores"
                        );

                    const modal =
                        bootstrap.Modal.getOrCreateInstance(
                            modalElemento
                        );

                    modal.show();
                }
            );
        }
    }
);



