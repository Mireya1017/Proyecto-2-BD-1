# Proyecto-2-BD-1

Sistema de restaurante con PostgreSQL y Python.

## Estado actual

Se encuentran implementados:

- Creación de la base de datos, restricciones, índices y bitácora.
- Datos iniciales de Oakland Mall y Ciudad Cayalá.
- Conexión compartida entre Python y PostgreSQL.
- Manejo compartido de sesiones y transacciones.
- Registro, búsqueda y consulta de clientes.
- Registro y consulta de platos favoritos.
- Historial de visitas, reservas y preferencias.
- Registro de visitas con y sin reserva.
- Consulta de mesas disponibles para una llegada.
- Registro de salidas y liberación de mesas después de la limpieza.
- Top 10 de clientes frecuentes por visitas.
- Top 5 de clientes con más reservas y sus favoritos.
- Menú de consola para las funcionalidades anteriores.

El acceso actual al menú utiliza una sesión de prueba. Todavía falta integrar la autenticación real, los módulos restantes de reservas, inventario y ventas, y las demás opciones y reportes del sistema.

## Organización del repositorio

- `sql_datos/`: scripts para crear y cargar la base de datos.
- `funcionalidades_py/`: conexión, transacciones y lógica del sistema.
- `funcionalidades_py/consola/`: entrada de datos y presentación de resultados.
- `docs/`: documentación del proyecto.
- `requirements.txt`: dependencias de Python.
- `config.example.ini`: ejemplo de configuración.
- `README.md`: instrucciones de instalación y ejecución.

`config.ini` y `.venv/` son archivos y carpetas locales excluidos de Git.

## 1. Requisitos

- PostgreSQL instalado y su servicio en ejecución.
- pgAdmin instalado.
- Un usuario de PostgreSQL con permisos para crear la base y sus objetos.
- Python 3.10 o superior.
- Una copia descargada o clonada del repositorio.
- Para los comandos de terminal de esta guía: Windows con Git Bash.

Si el repositorio ya está clonado, se puede actualizar desde su carpeta raíz:

```bash
git switch main
git pull --ff-only origin main
```

Guardar los cambios locales antes de cambiar de rama. Si Git informa un error, resolverlo antes de continuar.

## 2. Crear la base de datos

Si ya se tiene una base creada y cargada con estos scripts, omitir su creación y pasar a configurar Python.

Para replicar la instalación desde cero:

1. Abrir pgAdmin.
2. Conectarse al servidor PostgreSQL.
3. Hacer clic derecho sobre `Databases`.
4. Seleccionar `Create → Database`.
5. Escribir `restaurante_prueba`.
6. Pulsar `Save`.

Debe ser una base nueva y vacía. Si ese nombre ya existe, utilizar otro y conservar ese nombre para la configuración posterior.

En las pruebas del equipo se utilizó `restaurante`. Cada instalación debe configurar el nombre de la base que realmente utilizará.

### Comprobar la base seleccionada

Hacer clic derecho sobre la base recién creada y abrir `Query Tool`.

Ejecutar:

```sql
SELECT current_database();
```

El resultado debe coincidir con el nombre elegido.

Todos los scripts y consultas posteriores deben ejecutarse en esa misma base.

## 3. Ejecutar los scripts SQL

Comprobar que dentro de `sql_datos/` estén:

- `estructura.sql`
- `restricciones.sql`
- `indices.sql`
- `triggers.sql`
- `datos_iniciales.sql`

Desde el Query Tool, abrir y ejecutar los archivos completos en este orden:

1. `estructura.sql`
2. `restricciones.sql`
3. `indices.sql`
4. `triggers.sql`
5. `datos_iniciales.sql`

Para cada archivo:

1. Abrirlo en el Query Tool conectado a la base elegida.
2. Seleccionar todo su contenido.
3. Pulsar F5.
4. Revisar la pestaña `Messages`.
5. Continuar únicamente si terminó sin errores.

Cada archivo incluye `BEGIN` y `COMMIT`.

Si aparece un error, detener la carga y ejecutar por separado:

```sql
ROLLBACK;
```

Corregir la causa antes de repetir el archivo que falló.

Los archivos anteriores que terminaron correctamente con `COMMIT` ya están guardados y no deben ejecutarse otra vez en esa base.

Para repetir la instalación completa, utilizar otra base vacía.

### Comprobar la estructura y los datos iniciales

Después de ejecutar los cinco archivos:

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

Resultados esperados inmediatamente después de la carga inicial:

- Tablas: 16.
- Sucursales: 2.
- Mesas: 12.
- Productos: 7.
- Insumos: 9.
- Recetas: 21.
- Lotes: 18.

El orden de las filas puede variar. Las cantidades pueden cambiar después de utilizar el sistema.

La carga inicial no crea usuarios, clientes, reservas, visitas ni ventas.

Los precios, existencias y caducidades son datos de ejemplo. Las fechas de los lotes dependen del día de ejecución de la carga.

### Comprobar la bitácora

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

Deben aparecer operaciones `INSERT` correspondientes a la carga inicial.

El usuario puede aparecer como `NULL` porque estos scripts se ejecutan sin una sesión de la aplicación.

La bitácora guarda la identificación del registro afectado; no almacena una copia completa de todos sus campos.

## 4. Preparar Python

Abrir una terminal Git Bash en la raíz de `Proyecto-2-BD-1`, donde están `README.md` y `requirements.txt`.

La raíz es la carpeta del repositorio, independientemente de la rama seleccionada.

Comprobar Python:

```bash
python --version
```

Crear el entorno virtual si todavía no existe:

```bash
python -m venv .venv
```

Activarlo en Git Bash:

```bash
source .venv/Scripts/activate
```

Debe aparecer `(.venv)` en la terminal.

Activar el entorno cada vez que se abra una terminal nueva.

### Alternativa en PowerShell

Si se utiliza una terminal PowerShell, el comando de activación es:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts, ejecutar en esa misma terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después repetir el comando de activación.

Este ajuste se aplica únicamente a esa sesión de PowerShell. Los comandos anteriores de PowerShell no se ejecutan en Git Bash.

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

## 5. Configurar la conexión

En la raíz del repositorio, copiar `config.example.ini` y nombrar la copia `config.ini`.

Desde Git Bash, si todavía no existe:

```bash
cp config.example.ini config.ini
```

Si ya existe, editarlo sin reemplazarlo.

Completar sus valores:

```ini
[postgresql]
host = localhost
port = 5432
dbname = restaurante_prueba
user = postgres
password = CAMBIAR_AQUI
```

- `host`: dirección del servidor PostgreSQL.
- `port`: puerto de ese servidor.
- `dbname`: nombre exacto de la base creada y cargada.
- `user`: usuario de PostgreSQL con acceso a la base.
- `password`: contraseña de ese usuario.

Si se utilizará la base `restaurante`, escribir:

```ini
dbname = restaurante
```

Guardar el archivo.

El usuario de PostgreSQL es distinto de los usuarios de la aplicación almacenados en la tabla `usuario`.

`config.ini` es personal y no debe subirse a Git. `config.example.ini` debe contener únicamente valores de ejemplo.

### Verificar la conexión

Desde la raíz del repositorio:

```bash
python -m funcionalidades_py.prueba_conexion
```

Debe mostrar:

- Conexión exitosa.
- Nombre de la base configurada.
- Usuario de PostgreSQL.

Al consultar datos desde pgAdmin, abrir exactamente esa misma base. También deben coincidir el servidor y el puerto.

Los datos de una base no se comparten automáticamente con otra base ni con las computadoras de los demás integrantes.

## 6. Comprobaciones de Python

### Sintaxis e imports

```bash
python -m compileall funcionalidades_py
```

No deben aparecer errores de sintaxis o sangría.

Comprobar los imports del menú:

```bash
python -c "from funcionalidades_py.menu_principal import menu_principal; print('Menú e imports cargados correctamente')"
```

Estas comprobaciones no validan por sí solas las consultas ni el funcionamiento completo con PostgreSQL.

### Sesión de ejemplo

```bash
python -m funcionalidades_py.prueba_sesion
```

Debe mostrar el usuario de ejemplo `1`, rol `gerente` y sucursal `2`.

Esta prueba construye un diccionario en memoria; no crea un usuario ni comprueba sus credenciales.

### Contexto de bitácora

```bash
python -m funcionalidades_py.prueba_transacciones
```

Debe mostrar el identificador `1` dentro de la transacción y `None` después del rollback.

### Manejo de errores

```bash
python -m funcionalidades_py.prueba_operacion
```

Debe encontrar Oakland Mall, mostrar un error intencional de división por cero y realizar otra consulta exitosa después del error.

La división por cero forma parte de la prueba.

Los cuatro módulos de prueba de conexión, sesión, contexto y operación no modifican las tablas. Sus identificadores de ejemplo no deben utilizarse como sesiones autenticadas.

## 7. Preparar el usuario para probar el menú

La carga SQL inicial no crea usuarios.

Mientras se integra la autenticación real, ejecutar:

```bash
python -m funcionalidades_py.preparar_usuario_prueba
```

Este script:

- Busca la sucursal Oakland Mall.
- Crea el usuario `prueba_revision_yu` con rol `administrador`.
- Guarda un hash generado a partir de una contraseña aleatoria.
- Muestra el identificador real del usuario y su sucursal.
- Si el nombre ya existe, conserva ese usuario y muestra sus datos.

Este comando sí guarda información en PostgreSQL. La creación inicial puede quedar auditada con usuario `NULL`, porque todavía no hay una sesión de aplicación establecida.

No se debe asumir que el identificador generado será `1`.

Este usuario se utiliza mediante el acceso de prueba descrito a continuación. No se proporciona una contraseña para iniciar sesión con él.

El formato de hash utilizado por este script deberá coordinarse con el mecanismo definitivo de autenticación antes de reutilizarlo para cuentas reales.

## 8. Abrir el menú de prueba

Ejecutar:

```bash
python -m funcionalidades_py.prueba_menu
```

El script busca `prueba_revision_yu`, toma su ID, rol y sucursal y construye la sesión.

Debe mostrar:

```text
MODO DE PRUEBA: sesión sin autenticación.
```

Este acceso permite probar las funcionalidades implementadas. No valida credenciales ni sustituye el inicio de sesión definitivo.

Las operaciones que se completen correctamente desde el menú sí se guardan en la base configurada.

### Opciones disponibles

- `1`: gestión de clientes.
- `2`: preferencias de clientes.
- `3`: historial de clientes.
- `4`: reportes de clientes, visible para el administrador.
- `5`: gestión de visitas.
- `0`: salir del menú principal.

La opción `0` de cada submenú regresa al menú principal.

Después de modificar código, guardar los archivos y salir del programa antes de ejecutarlo de nuevo.

## 9. Uso de las funcionalidades

### Clientes

Permite registrar nombre y teléfono opcional, buscar por nombre y consultar por ID.

El nombre es obligatorio y admite hasta 120 caracteres. El teléfono admite hasta 20 caracteres.

El teléfono vacío se guarda como `NULL`.

La búsqueda por nombre no distingue mayúsculas de minúsculas y permite coincidencias parciales. Una búsqueda vacía devuelve todos los clientes.

Los clientes son compartidos entre sucursales.

### Preferencias

Permite agregar y consultar los productos favoritos de un cliente utilizando sus identificadores.

Para consultar los productos disponibles desde pgAdmin:

```sql
SELECT id_plato, nombre, precio
FROM plato
ORDER BY id_plato;
```

Una misma combinación de cliente y producto no puede repetirse.

El cliente y el producto deben existir. Las preferencias son compartidas entre sucursales.

### Historial

Muestra visitas, reservas y platos favoritos.

- El administrador consulta visitas y reservas de todas las sucursales.
- Gerente y mesero consultan únicamente las de su sucursal.
- Los favoritos del cliente se mantienen compartidos.

Si el cliente no existe, se informa el error.

### Registrar una llegada

En gestión de visitas, seleccionar registrar llegada.

Ingresar:

1. ID del cliente existente.
2. ID de sucursal, si la sesión es de administrador. Para otros roles se utiliza su sucursal.
3. Cantidad de personas.
4. ID de reserva, o dejar vacío si no tiene.
5. IDs de mesas separados por coma.
6. Observaciones opcionales.

Antes de solicitar las mesas, el programa muestra su ID, número, capacidad y zona.

Se ingresan los valores de `id_mesa`, no el número de mesa dentro de la sucursal.

Las mesas deben:

- Pertenecer a la sucursal.
- Estar en la misma zona.
- Tener capacidad conjunta suficiente.
- Estar liberadas.
- No estar asignadas a otra reserva vigente en ese momento.

El personal determina cuáles pueden juntarse físicamente.

Si se indica una reserva, debe estar confirmada y pertenecer al cliente y a la sucursal seleccionados.

La visita, sus mesas y el cambio de la reserva a `atendida` se guardan dentro de una misma transacción.

La consulta de disponibilidad actual no estima si la visita terminará antes de una reserva futura.

### Salida y liberación

Primero registrar la salida utilizando el ID de visita.

La salida no libera automáticamente las mesas.

Después de limpiarlas, seleccionar liberar mesa e ingresar el ID de visita y el ID de mesa.

El sistema impide liberar una mesa antes de registrar la salida.

### Reportes de clientes

Disponibles únicamente para administrador:

- Top 10 de clientes frecuentes, contado por visitas.
- Top 5 de clientes con más reservas, incluyendo sus favoritos.

Ingresar las fechas en formato:

```text
AAAA-MM-DD
```

La fecha final es inclusiva. Para consultar un solo día, ingresar la misma fecha como inicial y final.

El Top 5 excluye reservas canceladas; incluye los demás estados.

Los reportes consideran todas las sucursales. Los empates se ordenan por ID del cliente.

En una instalación nueva pueden no existir visitas o reservas. En ese caso se muestra un mensaje sin resultados.

## 10. Transacciones y bitácora

Los módulos utilizan:

```python
ejecutar_transaccion(p_sesion, p_operacion, p_datos)
```

La función recibida como operación debe aceptar:

```python
def nombre_operacion(p_conexion, p_sesion, p_datos):
```

Se pasa su nombre sin paréntesis.

La operación debe:

- Utilizar la conexión recibida.
- Comprobar permisos y sucursal.
- Ejecutar SQL con parámetros.
- Devolver el resultado necesario.
- Propagar los errores al manejador compartido.

No debe abrir otra conexión ni ejecutar `commit`, `rollback` o `close`.

El manejador compartido establece el usuario para la bitácora, ejecuta la operación y confirma los cambios con `commit`.

Si falla, ejecuta `rollback` y comunica el error. Finalmente cierra la conexión.

La confirmación también comprueba las restricciones diferidas.

Los pasos que forman una sola operación deben utilizar la misma conexión y transacción. Por ejemplo:

- Reserva y asignación de mesas.
- Visita, asignación de mesas y actualización de reserva.
- Venta, detalles y descuento de ingredientes, cuando se integre ese módulo.

No se requiere desarrollar escenarios adicionales de reservas simultáneas de mesas. Se mantienen las validaciones normales de disponibilidad y las transacciones.

### Verificar una operación auditada

Después de registrar un cliente desde el menú:

```sql
SELECT
    id_usuario,
    tabla,
    registro,
    operacion,
    fecha_hora
FROM bitacora
WHERE tabla = 'cliente'
ORDER BY id_bitacora DESC
LIMIT 10;
```

La inserción debe tener el ID del usuario de la sesión utilizada.

Las operaciones revertidas no deben dejar cambios ni entradas de bitácora confirmadas.

## 11. Pruebas realizadas y pendientes

Durante la revisión se comprobaron:

- Sintaxis e imports.
- Conexión con PostgreSQL.
- Registro y consulta de clientes.
- Auditoría de una inserción realizada desde Python.
- Consulta de favoritos y rechazo de favoritos duplicados.
- Historial y filtro por sucursal.
- Consulta de mesas disponibles.
- Llegadas con y sin reserva.
- Cambio de reserva a `atendida`.
- Rechazo de liberación antes de registrar la salida.
- Registro de salida y liberación posterior.
- Reportes de clientes con datos y sin resultados.

Estas comprobaciones se realizaron con una sesión de prueba. No equivalen a una validación completa del sistema integrado.

Queda pendiente:

- Conectar la autenticación real.
- Integrar los módulos restantes de reservas, inventario y ventas.
- Coordinar la disponibilidad utilizada por reservas y llegadas.
- Agregar las opciones y reportes restantes al menú.
- Probar los flujos completos con usuarios autenticados y sus permisos.
- Actualizar estas instrucciones al incorporar los módulos restantes.

Los registros creados durante las pruebas son locales. Subir código a Git no sube los datos de PostgreSQL.


## 12. Usuarios, autenticación y reservas

Se encuentran integrados:

- Registro del primer administrador cuando la tabla `usuario` está vacía.
- Registro de usuarios desde una sesión de administrador.
- Protección de contraseñas mediante PBKDF2-HMAC-SHA256 con sal aleatoria.
- Inicio y cierre de sesión.
- Validación de permisos por rol y sucursal.
- Consulta de disponibilidad de mesas por sucursal, horario y zona.
- Registro, búsqueda y modificación de reservas.
- Cancelación y registro de inasistencia, conservando las mesas históricas.
- Consulta administrativa de bitácora.
- Reporte de reservas y ventas por sucursal.

Los archivos principales son:

- `funcionalidades_py/usuarios.py`
- `funcionalidades_py/reservas.py`
- `funcionalidades_py/administracion.py`
- `funcionalidades_py/consola/consola_pablo.py`
- `funcionalidades_py/inicio.py`

### Acceso mediante autenticación real

Con el entorno virtual activo y la conexión configurada, ejecutar desde la raíz:

```bash
python -m funcionalidades_py.inicio
```

Para una instalación nueva:

1. Seleccionar `2. Crear primer administrador`.
2. Ingresar nombre de usuario, contraseña, confirmación y sucursal habitual.
3. Seleccionar `1. Iniciar sesión`.
4. Ingresar las credenciales recién creadas.

La creación del primer administrador solo funciona cuando no existen usuarios.

Si ya existen usuarios, iniciar sesión con una cuenta disponible. Un administrador autenticado puede crear las demás cuentas desde gestión de usuarios.

El programa definitivo utiliza este acceso. `prueba_menu.py` es una herramienta de pruebas que omite la autenticación.

### Opciones integradas del menú

- `1`: gestión de clientes.
- `2`: preferencias.
- `3`: historial de clientes.
- `4`: reportes de clientes, solo administrador.
- `5`: gestión de visitas.
- `6`: gestión de usuarios, solo administrador.
- `7`: gestión de reservas.
- `8`: administración, solo administrador.
- `0`: cerrar sesión.

### Permisos

El administrador puede operar sobre todas las sucursales y gestionar usuarios.

Gerente y mesero tienen restringidas las operaciones de reservas y visitas a su sucursal.

La bitácora y los reportes administrativos están restringidos al administrador.

### Reporte de sucursales

Agrupa reservas y ventas por separado mediante CTEs antes de combinar sus resultados. Así evita multiplicar cantidades e importes.

Por defecto excluye las reservas canceladas. Los importes utilizan el precio guardado en cada detalle de venta.

Las fechas finales ingresadas en las consultas administrativas incluyen el día completo.

## 13. Inventario y ventas

Los módulos están desarrollados y se encuentran en revisión para integrarlos al menú principal.

### Funcionalidades

- Existencias utilizables por sucursal, excluyendo lotes vencidos.
- Consulta de lotes y fechas de caducidad.
- Entradas directas de inventario.
- Alertas por existencias inferiores al mínimo.
- Alertas de próxima caducidad, con ventana provisional de siete días.
- Porcentaje disponible respecto al stock inicial de referencia.
- Ventas asociadas a visitas abiertas.
- Consumo conjunto de ingredientes de todos los productos de la venta.
- Consumo FEFO: primero los lotes que caducan antes, con desempate por ID.
- Registro de precios históricos en los detalles de venta.
- Top 10 de productos por unidades vendidas.
- Reporte de caducidades por mes y alertas de existencias actuales.

Cada entrada o venta se ejecuta mediante el manejador compartido de transacciones.

Una venta guarda cabecera, detalles y descuento de ingredientes en la misma transacción. Si falla, sus cambios deben revertirse.

### Integración pendiente

La consola `funcionalidades_py/consola/consola_nathalie.py` proporciona:

- `menu_inventario(p_sesion)`
- `menu_ventas(p_sesion)`
- `menu_reportes_nathalie(p_sesion)`

Inventario permite administrador y gerente, respetando la sucursal del gerente.

Ventas permite administrador, gerente y mesero, respetando la sucursal de la visita.

Los reportes permiten únicamente administrador.

Las sesiones deben proceder del inicio de sesión real.

### Interpretaciones y limitaciones

El 15 % utiliza como referencia las cantidades de la carga inicial. Es una interpretación documentada del equipo: la guía no define expresamente la base del porcentaje.

Los insumos sin referencia conservan su consulta de existencias y alerta por mínimo, pero no tienen un porcentaje calculado.

El reporte mensual selecciona lotes por su fecha de caducidad. Las cantidades y alertas de existencias corresponden al momento de consulta, no al cierre histórico del mes.

### Validación

La entrega incluye pruebas individuales de entradas, ventas, FEFO, auditoría, reportes y reversión de transacciones.

Después de los ajustes y la integración se comprobarán los flujos en la base local utilizada por el equipo.

Los IDs, cantidades y resultados de las pruebas individuales no deben asumirse como datos presentes en otras instalaciones.

Consultar `docs/modulo_nathalie.md` para los contratos de las funciones.
