# Recuperación de acceso de SegurAR - 27/09/2026

## Diagnóstico confirmado

La configuración de SQLAlchemy apunta a:

`C:\CODEX\PROYECTOS\UTN\TRABAJO-PRACTIVO-DE-GESTION\segurar.db`

La ruta es absoluta y se calcula a partir de backend/database.py, no de la carpeta desde donde se abre la terminal. El proceso que escucha en 8000 utiliza backend.main:app; la API respondió 200 en su raíz y 401 al intento con la credencial demo bloqueada.

La base conserva **4 usuarios: 1 administrador y 3 clientes**, y **4 pólizas**. La cuenta admin@demo.com existe, tiene ID 1 y rol admin. No hay pólizas huérfanas ni errores en PRAGMA foreign_key_check; PRAGMA integrity_check devolvió ok.

El administrador conserva la credencial demo heredada. La autenticación actual rechaza expresamente las claves demo publicadas antes de emitir un token. El intento de restablecimiento mostrado en la captura abortó en la validación y no llegó a guardar una contraseña. La captura no permite distinguir si la nueva entrada era demasiado corta, demasiado larga o una clave demo bloqueada.

No se encontraron otras bases .db/.sqlite/.sqlite3/.bak ni respaldos .backup/.zip en la búsqueda realizada dentro de C:\CODEX antes de crear este respaldo. No se inspeccionaron discos externos ni carpetas fuera de ese alcance.

## Respaldo previo a las modificaciones

Se creó mediante la API de respaldo consistente de SQLite, con origen abierto en modo solo lectura:

`backups/segurar-antes-recuperacion-20260927-223552-6692c974.sqlite3`

Integridad ok y cero relaciones inválidas. La carpeta backups queda ignorada por Git. El archivo contiene datos sensibles: no publicarlo ni adjuntarlo a conversaciones públicas.

No fue necesario recuperar registros: los usuarios y las pólizas ya estaban presentes. No se sobrescribió la base ni se cambió ninguna contraseña real durante las pruebas.

## Cambios realizados

- backend/manage.py: muestra la base y la cuenta encontradas antes de pedir la contraseña; no crea una base vacía si reset-password apunta a un archivo inexistente.
- Explica la escritura oculta y distingue los rechazos por longitud, clave demo publicada y confirmación diferente. Permite reintentar en lugar de terminar inmediatamente.
- Rechaza terminales sin entrada oculta para no exponer la clave.
- Genera y verifica un respaldo consistente antes de guardar. Conserva los datos de la cuenta y sus pólizas, cambia únicamente la contraseña y revoca las sesiones de esa cuenta.
- Cierra explícitamente las conexiones SQLite para evitar archivos bloqueados en Windows.
- Evita mostrar parámetros SQL, contraseñas o hashes en errores.
- tests/test_recovery.py: pruebas del asistente, límites, entrada oculta, archivo inexistente y respaldo.
- .gitignore: excluye backups.
- Este informe documenta el diagnóstico y la operación pendiente.

No se eliminó el bloqueo de claves demo publicadas ni se establecieron credenciales fijas.

## Verificación de recuperación en una copia

Se cargó el respaldo en SQLite en memoria. Se restablecieron únicamente en esa copia las claves con valores aleatorios efímeros que no se muestran ni se usan en la base real.

Se probaron login, /auth/me, /users/, /polizas/ o /polizas/mias y la prohibición de consultar informes de otro cliente:

| Cuenta | Login y permisos | Pólizas visibles |
|---|---|---|
| Administrador ID 1 | Correctos | 4 |
| Cliente ID 2 | Correctos; otro cliente devuelve 403 | 2 |
| Cliente ID 3 | Correctos; otro cliente devuelve 403 | 1 |
| Cliente ID 4 | Correctos; otro cliente devuelve 403 | 1 |

La comparación anterior/posterior verificó todas las filas de pólizas sin cambios y conservó id, nombre, email y rol de todos los usuarios. Las relaciones siguieron íntegras.

## Paso pendiente: contraseña elegida por el titular

En PowerShell de VS Code, no en el chat:

```powershell
cd C:\CODEX\PROYECTOS\UTN\TRABAJO-PRACTIVO-DE-GESTION
.\.venv\Scripts\python.exe -m backend.manage reset-password admin@demo.com
```

1. Confirmar que se muestra la base indicada arriba y la cuenta ID 1, rol admin.
2. Escribir una clave nueva de 8 a 128 caracteres, distinta de las antiguas claves demo. No aparecerán letras ni asteriscos.
3. Repetirla cuando se solicite.
4. Esperar los mensajes de respaldo verificado y Credencial guardada.
5. Ingresar en el navegador con el mismo email y la clave nueva. Reemplazar cualquier contraseña antigua autocompletada.

El acceso real no se considera restablecido hasta guardar la nueva clave y comprobar el ingreso con ella. No es necesario enviar la contraseña al asistente ni crear una cuenta administradora adicional. Si falla, compartir únicamente el mensaje de error.
