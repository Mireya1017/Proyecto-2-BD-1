# Proyecto-2-BD-1

Sistema de gestión de restaurante desarrollado con PostgreSQL y Python.

Permite gestionar usuarios, clientes, reservas, visitas, preferencias, inventario, ventas y reportes administrativos para las sucursales Oakland Mall y Ciudad Cayalá.

## 1. Requisitos

- PostgreSQL instalado y su servicio en ejecución.
- pgAdmin instalado.
- Acceso a PostgreSQL mediante un usuario con permisos para crear bases de datos y sus objetos.
- Python 3.10 o superior.
- Git instalado, si se clonará el repositorio.
- Una terminal Git Bash en Windows para seguir los comandos de esta guía.

La aplicación utiliza consola. No requiere instalar una interfaz gráfica adicional.

## 2. Descargar y localizar el proyecto

Para clonar el repositorio:

```bash
git clone https://github.com/Mireya1017/Proyecto-2-BD-1.git
cd Proyecto-2-BD-1
```

Si el repositorio es privado, GitHub solicitará autenticación y la cuenta deberá tener acceso.

Si ya se descargó o clonó, abrir su carpeta en VS Code. No es necesario clonarlo nuevamente.

Para actualizar una copia existente, con los cambios locales previamente guardados:

```bash
git switch main
git pull --ff-only origin main
```

Todos los comandos de Python de esta guía se ejecutan desde la raíz de `Proyecto-2-BD-1`, donde se encuentran `README.md` y `requirements.txt`.

### Organización

- `sql_datos/`: creación de la base, restricciones, índices, triggers, datos iniciales, vistas y consultas de apoyo.
- `funcionalidades_py/`: conexión, autenticación, transacciones y lógica del sistema.
- `funcionalidades_py/consola/`: menús, entrada de datos y presentación de resultados.
- `docs/`: documentación del proyecto.
- `requirements.txt`: dependencias de Python.
- `config.example.ini`: plantilla de configuración.
- `config.ini`: configuración local que cada persona debe preparar.

La carpeta `.venv/`, los archivos `__pycache__/` y `config.ini` están excluidos de Git.

## 3. Crear una base de datos vacía

Para replicar la instalación, utilizar una base nueva y vacía.

1. Abrir pgAdmin.
2. Conectarse al servidor PostgreSQL.
3. Hacer clic derecho sobre `Databases`.
4. Seleccionar `Create → Database`.
5. Escribir `restaurante_revision`.
6. Pulsar `Save`.

Si ese nombre ya existe, utilizar otro nombre para una base nueva. No eliminar una base existente para repetir la instalación.

Hacer clic derecho sobre la base recién creada y seleccionar `Query Tool`.

Ejecutar:

```sql
SELECT current_database();
```

El resultado debe coincidir con el nombre elegido.

Mantener todas las ejecuciones SQL siguientes en esa misma base.

Si ya se tiene una base correctamente instalada con los seis scripts del siguiente apartado, se puede omitir su creación y pasar a configurar Python.

## 4. Crear la estructura y cargar los datos

Los archivos necesarios están en `sql_datos/`.

Ejecutarlos completos en este orden:

1. `estructura.sql`
2. `restricciones.sql`
3. `indices.sql`
4. `triggers.sql`
5. `datos_iniciales.sql`
6. `vistas_reportes.sql`

Para cada archivo:

1. Abrirlo con la opción de abrir archivo del Query Tool.
2. Comprobar que el Query Tool siga conectado a la base elegida.
3. Seleccionar todo el contenido del editor.
4. Pulsar F5.
5. Revisar la pestaña `Messages`.
6. Continuar únicamente si terminó sin errores.

Los primeros cinco archivos incluyen `BEGIN` y `COMMIT`. El sexto crea la vista utilizada por el reporte acumulado de sucursales.

Si aparece un error, detener la instalación y ejecutar por separado:

```sql
ROLLBACK;
```

Corregir la causa antes de repetir el archivo que falló.

Los archivos anteriores que finalizaron correctamente con `COMMIT` ya están guardados. No deben ejecutarse nuevamente en esa base.

Los scripts de creación y carga inicial se utilizan una sola vez sobre una base vacía. Para repetir la instalación completa, crear otra base vacía.

### Archivos que no forman parte de esta carga

No ejecutar como parte de la instalación:

- `datos_prueba.sql`
- `inventario_consultas.sql`
- `reportes_nathalie.sql`

Contienen datos de demostración o consultas de apoyo. Las consultas utilizadas por los menús ya están implementadas en Python.

Tampoco es necesario ejecutar los archivos Python de pruebas para instalar o abrir el sistema.

### Verificar la carga inicial

Ejecutar:

```sql
SELECT 'Tablas' AS elemento, COUNT(*) AS cantidad
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'

UNION ALL
SELECT 'Sucursales', COUNT(*) FROM sucursal

UNION ALL
SELECT 'Mesas', COUNT(*) FROM mesa

UNION ALL
SELECT 'Productos', COUNT(*) FROM plato

UNION ALL
SELECT 'Insumos', COUNT(*) FROM insumo

UNION ALL
SELECT 'Recetas', COUNT(*) FROM receta

UNION ALL
SELECT 'Lotes', COUNT(*) FROM lote;
```

Resultados esperados inmediatamente después de la carga:

- Tablas: 16.
- Sucursales: 2.
- Mesas: 12.
- Productos: 7.
- Insumos: 9.
- Recetas: 21.
- Lotes: 18.

El orden de las filas puede variar.

Comprobar que todavía no existen usuarios:

```sql
SELECT COUNT(*) AS usuarios_iniciales
FROM usuario;
```

El resultado debe ser `0`, antes de crear el primer administrador.

Los datos iniciales no incluyen clientes, reservas, visitas ni ventas.

### Verificar la vista

```sql
SELECT *
FROM vw_resumen_historico_sucursales
ORDER BY importe_vendido DESC, id_sucursal;
```

En una instalación nueva deben aparecer las dos sucursales, con reservas, ventas e importes en cero.

### Verificar la bitácora

```sql
SELECT
    id_bitacora,
    id_usuario,
    tabla,
    registro,
    operacion,
    fecha_hora
FROM bitacora
ORDER BY id_bitacora DESC
LIMIT 10;
```

Deben aparecer inserciones de la carga inicial.

`id_usuario` puede ser `NULL` porque la carga se ejecuta directamente, sin una sesión de la aplicación.

Los precios, cantidades y fechas son datos de ejemplo. Las fechas de recepción y caducidad de los lotes iniciales se calculan a partir del día de ejecución de la carga.

## 5. Preparar Python

Abrir una terminal Git Bash desde la raíz del repositorio.

Comprobar Python:

```bash
python --version
```

Crear el entorno virtual si todavía no existe:

```bash
python -m venv .venv
```

Activarlo:

```bash
source .venv/Scripts/activate
```

Debe aparecer `(.venv)` en la terminal.

Activar el entorno cada vez que se abra una terminal nueva.

### Alternativa en PowerShell

Si se utiliza una terminal PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después repetir la activación.

Este ajuste se aplica únicamente a esa sesión de PowerShell. Los comandos de PowerShell no se ejecutan en Git Bash.

### Instalar dependencias

Con el entorno activo:

```bash
python -m pip install -r requirements.txt
```

Comprobar Psycopg:

```bash
python -c "import psycopg; print(psycopg.__version__)"
```

Con las dependencias actuales debe mostrar `3.3.6`.

## 6. Configurar la conexión

En la raíz del repositorio, copiar `config.example.ini` y nombrar la copia `config.ini`.

Desde Git Bash, si todavía no existe:

```bash
cp config.example.ini config.ini
```

Si ya existe `config.ini`, editarlo sin reemplazarlo.

Completar los datos:

```ini
[postgresql]
host = localhost
port = 5432
dbname = restaurante_revision
user = postgres
password = CAMBIAR_AQUI
```

Reemplazar:

- `host`: dirección del servidor PostgreSQL. Utilizar `localhost` cuando se ejecute en la misma computadora.
- `port`: puerto configurado en PostgreSQL.
- `dbname`: nombre exacto de la base creada y cargada.
- `user`: usuario de PostgreSQL con permisos sobre esa base.
- `password`: contraseña de ese usuario de PostgreSQL.

Si se creó una base con otro nombre, modificar `dbname`.

El usuario de PostgreSQL es distinto del usuario que inicia sesión en la aplicación.

Guardar el archivo antes de ejecutar Python.

`config.ini` contiene información personal y no debe publicarse. `config.example.ini` debe conservar únicamente valores de ejemplo.

### Comprobar la conexión

```bash
python -m funcionalidades_py.prueba_conexion
```

Debe mostrar:

- Conexión exitosa.
- Nombre de la base configurada.
- Usuario de PostgreSQL.

Al revisar datos en pgAdmin, utilizar el mismo servidor, puerto y base que aparecen en la configuración de Python.

Cambiar de rama en Git no cambia los datos de PostgreSQL. Cada base tiene sus propios usuarios y registros.

## 7. Abrir el sistema

Con el entorno virtual activo, ejecutar desde la raíz:

```bash
python -m funcionalidades_py.inicio
```

La pantalla de acceso muestra:

```text
1. Iniciar sesión
2. Crear primer administrador
0. Salir
```

### Crear el primer administrador

En una instalación nueva:

1. Seleccionar `2`.
2. Consultar la lista de sucursales mostrada.
3. Ingresar un nombre de usuario.
4. Ingresar una contraseña de al menos seis caracteres.
5. Repetir la contraseña.
6. Ingresar el ID de su sucursal habitual.
7. Esperar la confirmación del registro.

La contraseña no se muestra mientras se escribe. Es normal: se utiliza `getpass`.

La creación inicial solo se permite cuando la tabla `usuario` está vacía.

No se proporcionan credenciales predeterminadas. La persona que instala el sistema elige las del primer administrador.

### Iniciar sesión

1. Seleccionar `1`.
2. Ingresar el nombre de usuario registrado.
3. Ingresar su contraseña.
4. Pulsar Enter.

El acceso correcto muestra la bienvenida y el menú principal con el ID, rol y sucursal del usuario.

Las contraseñas se almacenan mediante PBKDF2-HMAC-SHA256 con sal aleatoria; no se guardan como texto plano.

Si ya existen usuarios, utilizar una cuenta registrada. No intentar crear nuevamente al primer administrador.

### Cerrar sesión y salir

- La opción `0` de un submenú vuelve al menú principal.
- La opción `0` del menú principal cierra la sesión y vuelve a la pantalla de acceso.
- La opción `0` de la pantalla de acceso termina el programa.

Si se modifica código, guardar los archivos y cerrar el programa antes de ejecutarlo nuevamente.

## 8. Opciones y permisos

El administrador puede ver las siguientes opciones:

```text
1. Gestión de clientes
2. Preferencias de clientes
3. Historial de clientes
4. Reportes de clientes
5. Gestión de visitas
6. Gestión de usuarios
7. Gestión de reservas
8. Administración
9. Ventas
10. Inventario
11. Reportes de inventario y ventas
0. Cerrar sesión
```

Permisos:

- Administrador: gestión de usuarios, todas las sucursales, operaciones del restaurante, bitácora y reportes.
- Gerente: operaciones de reservas, visitas, ventas e inventario de su sucursal, además de clientes y preferencias.
- Mesero: operaciones de reservas, visitas y ventas de su sucursal, además de clientes y preferencias.

Los clientes y sus preferencias son compartidos entre sucursales.

Las visitas y reservas del historial se filtran por sucursal para gerente y mesero.

Algunas opciones no aparecen según el rol. Los números conservan su identificación, por lo que pueden existir saltos.

## 9. Gestión de usuarios

Acceso: administrador, opción `6`.

### Registrar usuario

1. Seleccionar `1. Registrar usuario`.
2. Consultar las sucursales mostradas.
3. Ingresar nombre de usuario.
4. Ingresar y confirmar contraseña.
5. Indicar uno de estos roles:

```text
administrador
gerente
mesero
```

6. Ingresar el ID de sucursal habitual.

El nombre de usuario debe ser único.

### Listar usuarios

Seleccionar `2. Listar usuarios`.

Se muestran ID, nombre de usuario, rol y sucursal. No se muestran contraseñas ni hashes.

## 10. Clientes y preferencias

### Registrar cliente

En opción `1. Gestión de clientes`:

1. Seleccionar registrar cliente.
2. Ingresar nombre.
3. Ingresar teléfono o dejarlo vacío.
4. Conservar el ID generado para utilizarlo en reservas, visitas y preferencias.

El nombre es obligatorio y admite hasta 120 caracteres. El teléfono admite hasta 20 caracteres.

El teléfono vacío se guarda como `NULL`.

### Buscar y consultar clientes

- Buscar por nombre permite coincidencias parciales sin distinguir mayúsculas y minúsculas.
- Una búsqueda de nombre vacía devuelve todos los clientes.
- Consultar por ID muestra el cliente específico.

### Platos favoritos

En opción `2. Preferencias de clientes`:

- Agregar favorito solicita ID de cliente e ID de producto.
- Consultar favoritos solicita ID de cliente.

El cliente y el producto deben existir. Una misma preferencia no puede registrarse dos veces.

Para conocer los IDs de productos desde la aplicación, entrar a `9. Ventas` y seleccionar registrar venta: se muestra el menú con IDs antes de solicitar los datos. También pueden consultarse desde pgAdmin:

```sql
SELECT id_plato, nombre, precio
FROM plato
ORDER BY id_plato;
```

No asumir que un nombre siempre tiene el mismo ID en todas las bases.

## 11. Gestión de reservas

Acceso: opción `7`.

### Registrar reserva

Seleccionar `1. Registrar reserva`.

Ingresar:

1. ID del cliente existente.
2. Sucursal, si se utiliza una sesión de administrador.
3. Fecha y hora inicial.
4. Fecha y hora final estimada.
5. Cantidad de personas.
6. Zona: `interior` o `exterior`.
7. IDs de mesas disponibles, separados por coma.

Formato de fecha y hora:

```text
AAAA-MM-DD HH:MM
```

La hora final debe ser posterior a la inicial.

Gerente y mesero utilizan automáticamente su sucursal.

La consola muestra las mesas disponibles para el horario y zona indicados.

Las mesas seleccionadas deben existir, pertenecer a la sucursal, estar en la misma zona y tener capacidad conjunta suficiente.

El sistema rechaza superposiciones con otras reservas confirmadas o atendidas. Una reserva puede comenzar exactamente cuando termina otra.

La reserva y sus mesas se guardan en una misma transacción.

### Consultar reservas

Seleccionar `2. Consultar reservas`.

El administrador puede consultar todas. Gerente y mesero consultan únicamente las de su sucursal.

Se muestran cliente, sucursal, fechas, personas, estado y mesas.

### Modificar reserva

Seleccionar `3. Modificar reserva`.

Indicar el ID de reserva.

Dejar vacío un dato para conservarlo:

- Inicio.
- Fin estimado.
- Cantidad de personas.
- IDs de mesas.

Solo se modifican reservas confirmadas. El cambio vuelve a validar horarios, capacidad y asignación de mesas.

### Cancelar reserva

Seleccionar `4. Cancelar reserva`.

Indicar el ID.

La reserva cambia a `cancelada`, pero conserva sus asignaciones históricas. Deja de bloquear el horario reservado.

### Registrar inasistencia

Seleccionar `5. Marcar inasistencia`.

Utilizarla cuando el personal determine que el cliente no asistió.

Las reservas atendidas no pueden anularse mediante estas operaciones.

## 12. Visitas, salidas y liberación de mesas

Acceso: opción `5`.

### Registrar llegada

Seleccionar `1. Registrar llegada`.

Ingresar:

1. ID de cliente.
2. Sucursal, si el usuario es administrador.
3. Cantidad de personas.
4. ID de reserva, o dejar vacío si no tiene.
5. IDs de mesas, separados por coma.
6. Observaciones opcionales.

Antes de pedir las mesas, el programa muestra ID, número, capacidad y zona de las disponibles en ese momento.

Se ingresan los valores de `id_mesa`, no el número de mesa dentro de la sucursal.

El personal selecciona las mesas. Si se juntan varias, determina cuáles pueden unirse físicamente.

El sistema comprueba sucursal, zona, capacidad, ocupación, limpieza pendiente y reservas vigentes de otros grupos.

Si se indica una reserva, debe estar confirmada y pertenecer al cliente y a la sucursal seleccionados.

Se guardan la visita, las mesas y el cambio de la reserva a `atendida` en una misma transacción.

Conservar el ID de visita para registrar ventas y la salida.

### Registrar salida

Seleccionar `2. Registrar salida` e ingresar el ID de visita.

La salida queda registrada, pero las mesas siguen pendientes de liberación.

### Liberar mesa

Después de la limpieza:

1. Seleccionar `3. Liberar mesa después de limpieza`.
2. Ingresar ID de visita.
3. Ingresar ID de mesa.

No se permite liberar una mesa antes de registrar la salida.

Si la visita utilizó varias mesas, liberar cada una.

### Historial

La opción principal `3` muestra visitas, reservas, favoritos y observaciones del cliente.

Administrador consulta todas las sucursales. Gerente y mesero ven únicamente las visitas y reservas de su sucursal.

## 13. Inventario

Acceso: administrador y gerente, opción `10`.

El administrador elige sucursal. El gerente utiliza su sucursal asignada.

### Consultar existencias

Seleccionar `1`.

Se muestran ID del insumo, nombre, unidad, existencia utilizable y mínimo.

Los lotes vencidos no se consideran utilizables.

### Consultar lotes

Seleccionar `2` e indicar el ID del insumo.

Se muestran lote, caducidad, cantidad, unidad y estado.

Un lote vencido conserva su cantidad histórica, aunque no esté disponible para ventas.

### Consultar alertas

Seleccionar `3`.

Se muestran:

- Existencias por debajo del mínimo.
- Lotes con cantidad disponible que caducan entre hoy y los próximos siete días.
- Porcentaje disponible respecto al stock inicial de referencia.

Para este proyecto, el cálculo del porcentaje es:

```text
Porcentaje disponible =
(existencia utilizable / stock inicial de referencia) × 100
```

Se genera alerta al 15 % o menos.

Esta referencia es una interpretación documentada del equipo, porque la guía no define expresamente la base del porcentaje.

Los insumos sin referencia siguen mostrando existencias y alertas por mínimo, pero su porcentaje se indica como `Sin referencia`.

La ventana de próxima caducidad utilizada es de siete días.

### Registrar entrada

Seleccionar `4`.

Ingresar:

1. ID del insumo existente.
2. Fecha de recepción.
3. Fecha de caducidad.
4. Cantidad recibida.
5. Confirmación `SI`.

Formato de fechas:

```text
AAAA-MM-DD
```

La cantidad debe ser positiva y admitir la precisión de `NUMERIC(12,3)`. La caducidad no puede ser anterior a la recepción.

Cada entrada crea un lote nuevo.

No cambiar la caducidad de un lote vencido para volverlo utilizable. Registrar una entrada nueva con sus propias fechas.

No volver a ejecutar `datos_iniciales.sql` para reponer inventario.

## 14. Ventas

Acceso: opción `9`.

### Consultar menú

Seleccionar `1`.

Se muestran productos y precios actuales.

### Registrar venta

Seleccionar `2`.

Se muestra el menú con los IDs de productos.

Ingresar:

1. ID de una visita existente y abierta.
2. Cantidad de productos diferentes.
3. ID y cantidad de cada producto.

Cada producto se indica una sola vez con su cantidad total.

El sistema:

- Verifica acceso a la sucursal de la visita.
- Rechaza visitas finalizadas.
- Obtiene los precios de PostgreSQL.
- Suma los ingredientes necesarios de toda la venta.
- Comprueba inventario utilizable.
- Consume primero los lotes con menor fecha de caducidad.
- Desempata lotes con igual caducidad por menor ID.
- Guarda venta, detalles y descuento de ingredientes en una sola transacción.

No utiliza lotes vencidos.

Al finalizar muestra el ID de venta, ID de visita y total.

El precio aplicado se conserva en el detalle aunque posteriormente cambie el precio del menú.

La venta no registra automáticamente la salida del cliente. La salida y liberación se realizan desde gestión de visitas.

## 15. Reportes administrativos

Todos los reportes están restringidos al administrador.

### Reportes de clientes: opción `4`

Incluye:

- Top 10 de clientes frecuentes por cantidad de visitas.
- Top 5 de clientes con más reservas y sus favoritos.

Solicitan fecha inicial y final en formato `AAAA-MM-DD`.

La fecha final incluye el día completo. Para consultar un solo día, ingresar la misma fecha en ambos campos.

El Top 5 excluye reservas canceladas e incluye los demás estados.

Los reportes consideran todas las sucursales y resuelven empates por ID de cliente.

### Administración: opción `8`

Incluye:

1. Consulta de bitácora.
2. Reporte de sucursales.

La bitácora permite filtrar por fechas, usuario, tabla y operación. Los filtros vacíos no restringen los resultados. Se muestran hasta 100 registros.

Las operaciones válidas son `INSERT`, `UPDATE` y `DELETE`.

El reporte de sucursales permite filtrar por período y sucursal. Muestra reservas no canceladas, cantidad de ventas e importe vendido.

Sin fechas utiliza `vw_resumen_historico_sucursales`. Con fechas utiliza una consulta con CTEs.

Reservas y ventas se agrupan por separado para evitar multiplicar conteos e importes.

Las sucursales sin movimientos aparecen con valores en cero.

### Inventario y ventas: opción `11`

Incluye:

1. Top 10 de productos más vendidos.
2. Reporte mensual de inventario.
3. Insumos bajo mínimo.

El Top 10 considera todas las fechas y sucursales. Ordena por unidades vendidas y calcula ingresos con los precios históricos del detalle.

El reporte mensual solicita año, mes y sucursal. Muestra:

- Lotes cuya caducidad pertenece al mes seleccionado.
- Existencias actuales por debajo del mínimo.
- Alertas actuales del 15 %.

Las cantidades corresponden al momento de consulta. El reporte no reconstruye existencias al cierre de meses anteriores.

En una instalación nueva, los reportes de clientes y ventas pueden no tener resultados hasta registrar operaciones.

## 16. Recorrido recomendado para comprobar el sistema

Después de instalar y crear al administrador:

1. Iniciar sesión.
2. Registrar un cliente y conservar su ID.
3. Consultarlo por ID.
4. Agregar un producto favorito y consultarlo.
5. Registrar una reserva para un horario elegido, seleccionando mesas de la lista disponible.
6. Consultar la reserva.
7. Registrar una llegada sin reserva y conservar el ID de visita.
8. Consultar inventario para confirmar que los ingredientes del producto que se venderá estén utilizables.
9. Registrar una venta para esa visita.
10. Consultar el Top 10 de productos y el reporte de sucursales.
11. Consultar la bitácora filtrando tabla `venta` y operación `INSERT`.
12. Registrar la salida de la visita.
13. Liberar sus mesas después de la limpieza.
14. Consultar el historial del cliente.

Las pruebas con reserva asociada deben utilizar una reserva confirmada del cliente y sucursal de la llegada.

Si falta inventario vigente, registrar entradas desde inventario antes de vender.

Los identificadores se generan automáticamente. Utilizar los mostrados por el programa; no copiar IDs de pruebas de otra computadora o base.

Los datos de prueba permanecen guardados cuando la operación termina correctamente.

## 17. Transacciones, integridad y auditoría

Las operaciones de escritura utilizan el manejador compartido:

```python
ejecutar_transaccion(p_sesion, p_operacion, p_datos)
```

Cada operación recibe:

```python
def nombre_operacion(p_conexion, p_sesion, p_datos):
```

La operación utiliza la conexión recibida. El manejador establece el usuario de bitácora, ejecuta la operación y confirma con `commit`.

Si ocurre un error, ejecuta `rollback` y lo comunica. Finalmente cierra la conexión.

Las operaciones no deben abrir otra conexión ni confirmar parcialmente sus cambios.

Las restricciones diferidas se comprueban al confirmar la transacción.

La base utiliza llaves primarias, foráneas, restricciones, índices y triggers para proteger la integridad.

La bitácora registra automáticamente inserciones, actualizaciones y eliminaciones de las tablas auditadas. Guarda tabla, operación, identificación del registro, usuario y fecha.

No guarda una copia completa de todos los campos anteriores y nuevos.

La carga SQL y la creación inicial del administrador pueden registrar usuario `NULL`. Las operaciones posteriores utilizan el usuario de la sesión.

No se desarrollan escenarios adicionales de reservas simultáneas de mesas. Se mantienen las transacciones y las validaciones normales de disponibilidad y consistencia.

## 18. Comprobaciones y solución de problemas

### Revisar sintaxis

```bash
python -m compileall funcionalidades_py
```

### Revisar imports del arranque

```bash
python -c "from funcionalidades_py.inicio import iniciar_programa; print('Inicio y menús cargados correctamente')"
```

Estas comprobaciones no ejecutan los flujos de negocio ni sustituyen las pruebas con PostgreSQL.

### No se encuentra Psycopg

Activar el entorno virtual y ejecutar:

```bash
python -m pip install -r requirements.txt
```

### No se encuentra config.ini

Crear el archivo en la raíz del repositorio, junto a `README.md`, siguiendo el apartado de configuración.

### Error de conexión

Comprobar:

- Servicio PostgreSQL en ejecución.
- Servidor y puerto.
- Nombre de base.
- Usuario y contraseña de PostgreSQL.
- Que los cambios de `config.ini` estén guardados.

### PostgreSQL indica que una tabla no existe

Comprobar la base seleccionada y que los scripts se hayan ejecutado completos en el orden indicado.

### No existe vw_resumen_historico_sucursales

Ejecutar `sql_datos/vistas_reportes.sql` en la misma base utilizada por Python.

### Usuario o contraseña incorrectos

Utilizar una cuenta creada en la base configurada. Las cuentas de otra base no están disponibles automáticamente.

Si la base está recién instalada y vacía de usuarios, crear primero al administrador.

### Ya existe al menos un usuario

La creación inicial del administrador está bloqueada porque ya existen cuentas. Iniciar sesión con una cuenta disponible.

### Inventario insuficiente

Consultar existencias y lotes de la sucursal de la visita. Los lotes vencidos no cuentan como disponibles.

Registrar entradas nuevas cuando corresponda.

### La mesa no está disponible

Comprobar reservas del horario y visitas sin liberación. Registrar la salida no libera la mesa automáticamente.

### No aparecen datos en pgAdmin

Comprobar:

```sql
SELECT current_database();
```

La conexión de pgAdmin debe coincidir con el servidor, puerto y base utilizados por Python.

### Error de sangría o sintaxis

Revisar el archivo y línea que muestra Python. Guardar y volver a ejecutar.

### Cambié código, pero sigue funcionando la versión anterior

Cerrar el programa completamente y ejecutar nuevamente:

```bash
python -m funcionalidades_py.inicio
```

## 19. Archivos de pruebas y datos locales

El punto de entrada normal es:

```bash
python -m funcionalidades_py.inicio
```

Los archivos prueba_*.py son herramientas de desarrollo.. Algunos crean datos, utilizan sesiones simuladas o están preparados para condiciones específicas.

No ejecutarlos todos como parte de la instalación.

No se necesitan usuarios de prueba predefinidos para replicar la aplicación: el primer administrador se crea desde la pantalla de acceso.

Git almacena el código, no los registros de PostgreSQL. Subir o descargar cambios del repositorio no copia usuarios, ventas ni inventario entre computadoras.

Para conectar varias instalaciones a una misma base, sus archivos `config.ini` deben apuntar al mismo servidor y base accesibles.
