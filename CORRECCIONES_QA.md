# Correcciones QA de SegurAR

Fecha: 27/09/2026. Se mantuvieron los dashboards, los roles y el modelo funcional de usuarios y pólizas. No se restablecieron cambios ajenos que ya estaban en el repositorio.

## Activación en la PC (Python 3.13)

No se agregaron dependencias de Python ni es necesario activar PowerShell. Antes de desplegar, detener el backend y respaldar segurar.db. No ejecutar pruebas contra esa base.

Desde la raíz del proyecto:

```powershell
cd C:\CODEX\PROYECTOS\UTN\TRABAJO-PRACTIVO-DE-GESTION
.\.venv\Scripts\python.exe -m backend.manage reset-password admin@demo.com
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

El primer comando pide la nueva contraseña dos veces, sin mostrarla ni guardarla en el historial. Usarlo solo si esa cuenta existe y aún tiene la contraseña demo publicada; reemplazar el email para otras cuentas. Las claves demo publicadas quedan rechazadas, no se genera una nueva clave conocida. Las demás credenciales válidas se conservan. Para una instalación vacía: `python -m backend.manage create-admin EMAIL --nombre NOMBRE`.

Al iniciar se agrega la tabla **sesiones** si falta, sin reescribir usuarios ni pólizas. Todos los tokens antiguos dejan de ser válidos: cada usuario debe iniciar sesión nuevamente. No se crean datos demo automáticamente. El comando opcional `python -m backend.init_demo` solicita claves nuevas y no sobrescribe cuentas existentes.

Frontend, en una segunda terminal:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory login
```

Abrir http://127.0.0.1:5500/ y recargar sin caché (Ctrl+F5). El frontend sigue en `login/`; su entrada es `login/index.html`.

CORS permite por defecto únicamente http://127.0.0.1:5500 y http://localhost:5500. Si se usa otro origen, configurar `CORS_ORIGINS` en .env como lista separada por comas y reiniciar. La URL de API predeterminada sigue siendo http://127.0.0.1:8000. Para otro despliegue, definir `window.SEGURAR_API_URL` antes de cargar common.js. No se cambió .env.

## Cambios, en el orden de prioridad del informe

| ID | Prioridad | Corrección | Archivos principales | Verificación |
|---|---|---|---|---|
| 01 | Crítica | JWT vinculado a sesión aleatoria en SQLite; el ID reutilizado no hereda el token eliminado. | backend/models.py, auth_utils.py, routers/auth.py | Borrar cliente ID 3, crear admin ID 3: token anterior recibe 401. |
| 02 | Alta | Inicio sin cuentas demo automáticas; claves publicadas rechazadas, sin credenciales en pantalla; comando de restablecimiento local. | main.py, init_demo.py, manage.py, auth_utils.py, login/index.html | Login con clave publicada rechazado y nuevo password demo devuelve 422. |
| 03 | Alta | Datos del informe insertados con textContent; escape contextual en tablas de administración y error de login. | informes.js, dashboard_admin.js, common.js, script.js | Cadenas img/svg/script se muestran como texto, no como HTML ejecutable. |
| 04 | Alta | Revocación real al salir, cambiar clave o cambiar rol; la eliminación de usuario borra sus sesiones. | routers/auth.py, routers/users.py, logout.js | Token revocado recibe 401; otra sesión no cerrada sigue válida. |
| 05 | Alta | Nuevas claves PBKDF2-SHA256 (600.000 iteraciones), sin truncamiento; migración de bcrypt tras autenticación. | auth_utils.py, schemas.py, script.js | Contraseñas con igual prefijo de 72 bytes y distinto sufijo ya no coinciden. |
| 06 | Media | PUT parcial no depende de la variable nombre; nombre vacío se rechaza. | routers/users.py | PUT de solo email, solo clave y objeto vacío sin error 500. |
| 07 | Media | Regla de estado central y dinámica en respuestas CRUD/informes; persistencia calculada al guardar. | policy_rules.py, schemas.py, routers/polizas.py, routers/informes.py | Estado y totales coinciden en límites -1, 0, 7, 8, 30, 31, 60, 61 días. |
| 08 | Media | POST /users/ acepta tipo_poliza opcional y guarda cliente/póliza en una transacción. | schemas.py, routers/users.py, dashboard_admin.js | Fallo forzado al insertar póliza devuelve 409 y no deja usuario creado. |
| 09 | Media | PDF incluye todos los resultados filtrados; eliminación de limit(10000). | routers/informes.py | 10.001 filas llegan al generador, comprobado con generador sustituido; no se midió el rendimiento del PDF de ese tamaño. |
| 10 | Media | Tabla, resumen, paginación y exportación usan la misma copia de filtros aplicados; aviso de cambios sin aplicar. | informes.js | Editar Auto a Vida sin aplicar mantiene PDF con Auto. |
| 11 | Media | Gráficos de barras HTML, sin Chart.js ni dependencia de un CDN para visualizar los datos. | informes.js, informes_admin.html, informes_cliente.html | Tabla y gráficos funcionan sin objeto Chart disponible. |
| 12 | Media | Un fallo de red/500 conserva sesión; solo 401 limpia credenciales. | common.js, guard.js | Simulaciones de fallo de red, 500 y 401. |
| 13 | Media | Carga/error explícitos, eliminación de resultados viejos, cancelación y protección contra respuestas fuera de orden. Errores de dashboards visibles. | informes.js, common.js, dashboard_admin.js, dashboard_cliente.js | Error tras filtrar deja tabla vacía y PDF deshabilitado; respuesta tardía no pisa filtros nuevos. |
| 14 | Media | Fechas del formulario sin toISOString; fecha de negocio argentina centralizada en backend. | common.js, dashboard_admin.js, policy_rules.py | Prueba de serialización por componentes locales; altas conjuntas calculadas en servidor. |
| 15 | Media | Comparación heredada Unicode con bytes UTF-8 y migración posterior a hash. | auth_utils.py, routers/auth.py | Login con contraseña antigua con ñ y migración comprobada. |
| 16 | Media | Inicialización demo explícita, atómica y mensajes compatibles con consola Windows. | init_demo.py | Sin emojis en mensajes; revisión estática. No se ejecutó contra datos reales. |
| 17 | Media | Validaciones 422 muestran campo y mensaje, no [object Object]. | common.js, script.js, dashboards | Prueba del formateador con detail como lista. |
| 18 | Baja | Guard de dashboard e informes usa rol de /auth/me, no rol local alterable. | guard.js | Rol local admin y rol real cliente no permiten abrir informe admin. |
| 19 | Baja | Cada gráfico tiene título, categorías, cantidades y resumen; estructura de tabla accesible sin depender de color. | informes.js, informes_*.html | Pruebas de renderizado DOM; revisión de semántica HTML. |
| 20 | Baja | Resúmenes del PDF reconocen empates y ausencia de datos. | reportes_pdf.py | Pruebas de textos y revisión visual de empate Auto/Vida. |
| 21 | Baja | Etiquetas de fechas vinculadas a los inputs por for/id. | informes_*.html | Comprobación de ambos documentos. |

Mejoras complementarias: manejo de conflictos de integridad como HTTP 409 sin exponer SQL, rollback de la sesión ante errores, CORS con orígenes explícitos y preservación de espacios en contraseñas.

## Reglas que se conservaron y límites funcionales

- Vencida: vencimiento anterior a la fecha argentina de referencia.
- Por vencer: desde hoy hasta hoy + 30 días, ambos inclusive.
- Vigente: más de 30 días. La fecha de inicio no genera un cuarto estado.
- El estado guardado antiguo puede diferir del estado actual por el paso del tiempo. Las respuestas públicas lo recalculan; no se reescribe toda la base en cada inicio.
- Los rangos filtran vencimiento, con extremos incluidos. Los tramos incluyen vencidas para que la suma coincida con el total.
- Alta de cliente con póliza: vencimiento al mismo día del año siguiente; 29 de febrero pasa a 28 de febrero. Es continuidad de la función existente, no cálculo de prima.
- Pendiente de decisión comercial: pólizas con inicio futuro, cancelaciones, renovaciones y cambios del plazo de 30 días. No se inventaron campos para estas situaciones.
- El PDF permanece A4 vertical, listado antes que gráficos, con cliente/email solo para administrador.

## Pruebas reproducibles

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node --test tests/frontend.test.cjs
.\.venv\Scripts\python.exe -B -m tests.render_report_fixture
```

Resultado: **20 pruebas de backend + 10 de frontend, todas aprobadas**. Las pruebas Python usan SQLite en memoria y bloquean expresamente conexiones al motor real. Las pruebas JS usan un DOM simulado: no sustituyen un recorrido manual de navegador y celular.

Se verificaron importación de la API sin inicializar datos, sintaxis de los siete JS, `pip check`, PDF vacío y con contenido, y un PDF de dos páginas A4 vertical renderizado e inspeccionado visualmente con texto largo, gráficos y empate de categorías. El generador de muestra solo escribe en tmp/pdfs/qa-correcciones.pdf con datos ficticios. La guía PDF se usó para verificar dimensiones, legibilidad, saltos y orden de la salida.

## Pendientes fuera de los bugs confirmados

- No se efectuó una prueba de carga de exportaciones masivas; al quitar el corte, crece el consumo de memoria del generador.
- No se implementó infraestructura de limitación de intentos de login, despliegue HTTPS ni una política CSP integral. Deben definirse para publicación en Internet.
- No se auditó CVE por versión ni se fijaron todas las dependencias; no se afirma ausencia de vulnerabilidades.
- Bootstrap sigue servido desde CDN. Los gráficos y datos ya no dependen de Chart.js, pero el estilo visual general sí depende de que Bootstrap cargue.
- La garantía de consistencia es por filtros; no hay una instantánea histórica entre consultas si otra persona cambia pólizas mientras se consulta/exporta.
- El entorno completo, las credenciales reales y la navegación móvil requieren validación del operador tras reiniciar. Las pruebas no restablecieron contraseñas reales ni editaron pólizas reales.
