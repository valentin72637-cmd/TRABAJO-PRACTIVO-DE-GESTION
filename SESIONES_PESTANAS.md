# Sesiones independientes por pestaña - SegurAR

## Causa comprobada

Antes del ajuste, login/app/script.js guardaba token, userId, nombre, email y role en localStorage. common.js leía ese token al preparar cada petición; guard.js y los dashboards consultaban datos del mismo almacenamiento, y logout.js borraba credenciales compartidas.

localStorage pertenece al origen del sitio, no a una pestaña: el segundo login reemplazaba la identidad utilizada por la primera. No se encontró autenticación mediante cookies ni sincronización por BroadcastChannel o eventos storage. El backend ya emitía un jti distinto por login y /auth/logout eliminaba únicamente esa sesión.

Se revisó git status antes de editar: había numerosos cambios locales y archivos sin seguimiento. No se restableció ni eliminó ninguno de ellos.

## Solución aplicada

- Todas las credenciales y datos de identidad se leen, guardan y eliminan en sessionStorage.
- common.js conserva la preparación central de Authorization: Bearer y el manejo de 401. Un 401 tardío de un token anterior tampoco borra un login nuevo de la misma pestaña.
- guard.js sigue consultando /auth/me: el rol guardado en el navegador no autoriza operaciones.
- Los dashboards esperan al guard antes de pedir datos; la protección para no eliminar al administrador actual usa ahora el userId de la pestaña.
- logout.js espera a que la pestaña se inicialice y revoca solo su token.
- Las preferencias visuales de opacidad permanecen en localStorage. No son credenciales.
- No se migran tokens antiguos desde localStorage: al actualizar, hay que iniciar sesión nuevamente en cada pestaña. Tampoco se borran globalmente las claves de otras pestañas.
- Se conserva la revocación de todas las sesiones de una cuenta por cambio de contraseña o rol en el backend. No existía un botón independiente de “cerrar todas las sesiones”.

### Apertura y duplicación

sessionStorage puede copiarse inicialmente si la nueva pestaña tiene opener o al duplicar una pestaña. Copiar el JWT sin otra medida haría que logout revocara el token de ambas.

common.js reserva un identificador aleatorio mediante Web Locks mientras el documento está activo. Si otra pestaña intenta usar una copia de ese identificador, elimina únicamente sus credenciales copiadas, genera otro ID y pide un login propio; no llama a /auth/logout con el token heredado.

La reserva se libera en pagehide para permitir navegación y recarga. Si el documento vuelve desde BFCache se recarga para revalidar la sesión. Una pestaña nueva sin credenciales empieza en login. No se transmiten JWT ni contraseñas mediante los locks.

Referencias: [sessionStorage y copia por opener](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage), [Web Locks](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API).

## Archivos modificados

Todos los paths siguientes son relativos a la raíz del proyecto:

1. login/app/common.js
2. login/app/script.js
3. login/app/guard.js
4. login/app/logout.js
5. login/app/dashboard_admin.js
6. login/app/dashboard_cliente.js
7. tests/frontend.test.cjs
8. tests/test_regressions.py

Archivos nuevos: tests/serve_tab_fixture.py (servidor de prueba aislado) y SESIONES_PESTANAS.md (este informe).

Se confirmó que login/app/logout.html ya carga common.js y logout.js; no requirió cambios. informes.js usa el helper común, por lo que tampoco requirió cambios. No se modificaron backend/auth_utils.py, los routers de producción, .env, requisitos ni SQLite.

## Verificaciones realizadas

**28 pruebas Python y 18 pruebas JavaScript aprobadas.** También pasó la comprobación sintáctica de todos los JS.

| Escenario | Evidencia |
|---|---|
| Admin primero, cliente después y orden inverso | Pruebas ejecutando script.js, credenciales separadas y roles confirmados por API. |
| Recarga/navegación | Simulación de lifecycle y comprobación visual: dashboard del administrador después de recargar; cliente navega a informes con una sola póliza. |
| Logout de una sesión | Regresión backend/frontend y comprobación visual de cliente cerrado con admin todavía activo; también salida del admin y cliente conservado. |
| Sesión inválida/expirada | Pruebas de 401 y vencimiento en backend; invalidación controlada del admin en QA, mientras el cliente de otra pestaña sigue activo tras recargar. |
| Cliente intenta pantalla/admin API | Bloqueo visual de dashboard admin, pruebas de 403 en endpoints y aislamiento de pólizas. |
| Alta/edición/baja de usuarios y pólizas | Regresiones de backend, incluidas transacciones, validaciones y CRUD de póliza. |
| Búsquedas e informes | Búsqueda visual de QA-HOGAR-B en dashboard admin, filtros de informes por tipo en backend y regresiones de informes. |
| Pestaña nueva | Abierta en el mismo navegador sin adoptar credenciales antiguas de localStorage. |
| Copia con opener | Abrió login con aviso de sesión propia; original mantuvo su sesión. La copia pudo iniciar sesión como cliente y conservarla al invalidar el admin original. |
| Duplicación nativa del menú de Brave | No ejecutada: pendiente de comprobación en el navegador del usuario. El clon de almacenamiento fue probado en unidad y la apertura con opener en navegador. |

La prueba visual utilizó varias pestañas del mismo navegador integrado y perfil, en http://127.0.0.1:8765, con cuentas ficticias y SQLite exclusivamente en memoria. No se usó otro perfil/incógnito para resolver el problema. El servidor de prueba bloquea cualquier conexión al motor real.

Durante la verificación se corrigió un problema del propio servidor de QA: StaticPool comparte una conexión en memoria, de modo que las peticiones se serializan en ese servidor para evitar interferencias entre transacciones. No fue un cambio en el backend de producción.

## Cómo comprobarlo en tu navegador

1. Cerrá las pestañas antiguas de SegurAR. Abrí el login habitual y recargá con Ctrl+F5 para cargar los JS nuevos.
2. En pestaña A, ingresá con tu administrador y su contraseña actual.
3. Abrí otra pestaña escribiendo la misma dirección de login. Ingresá como cliente con su contraseña actual.
4. Volvé a A y recargá: debe seguir como administrador. En B deben aparecer únicamente las pólizas del cliente.
5. Navegá a informes en cada pestaña. Cerrá la sesión de B y recargá A: A debe seguir autenticada.
6. Repetí en orden inverso y cerrando A.
7. Con una pestaña autenticada abierta, usá “Duplicar pestaña”: la copia debe solicitar su propio login; la original debe continuar activa.
8. Desde el cliente intentá abrir dashboard_admin.html o informes_admin.html: debe denegarse el acceso, sin revelar los datos del administrador.

No cambies las contraseñas ni reinicialices la base para estas pruebas. No hace falta instalar dependencias nuevas ni modificar la configuración JWT.

## Límites y comprobaciones pendientes

- Requiere un navegador con Web Locks y crypto.randomUUID, en localhost/127.0.0.1 o HTTPS. Si no están disponibles, muestra un error y no habilita la sesión; no vuelve a localStorage.
- No se probaron todas las versiones de Brave, duplicación desde su menú, restauración masiva tras cerrar el navegador ni suspensión del sistema. Las restauraciones de pestañas dependen del navegador.
- Se validó el flujo de apertura con opener con la pestaña original activa. Una credencial copiada manualmente sigue siendo un Bearer válido: el almacenamiento por pestaña no pretende proteger frente a quien roba y copia un token.
- El CRUD completo se verificó por API; no se recorrió visualmente cada modal de edición. La prueba visual sí cubrió login, navegación, permisos, búsquedas, informes, logout y expiración.
- La actualización requiere login por pestaña, pero conserva usuarios, claves y pólizas.

## Revertir exclusivamente este ajuste

Los ocho archivos existentes se copiaron antes de editarlos a:

`backups/sesiones-pestanas-20260927-233150/`

Para volver al estado exacto previo a este ajuste, restaurar únicamente esos ocho archivos desde la copia, manteniendo sus subcarpetas. No usar git reset/checkout: había cambios anteriores sin commit. Si hubo ediciones posteriores en alguno, comparar primero y revertir solo los bloques de este ajuste.

Los dos archivos nuevos indicados arriba pueden retirarse si se abandona la mejora. No borrar otros tests, respaldos, tmp ni segurar.db. Tras una reversión, cerrar las pestañas de SegurAR y recargar sin caché.

## Ejecutar las pruebas

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node --test tests/frontend.test.cjs
```

Para repetir la prueba visual con datos descartables: `python -B -m tests.serve_tab_fixture`. Solo escucha en 127.0.0.1:8765; las cuentas QA y su clave son exclusivamente de ese entorno y están declaradas en el archivo. No se incorporan a la base real. Detener el proceso al terminar.
