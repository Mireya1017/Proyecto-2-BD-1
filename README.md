# Proyecto-2-BD-1
Proyecto #2, avances y resultados

### Creación y carga de la base de datos

#### Requisitos

- PostgreSQL instalado y su servicio en ejecución.
- pgAdmin instalado.
- Acceso al servidor PostgreSQL con un usuario que pueda crear bases de datos.
- Una copia descargada o clonada de este repositorio.

Los siguientes pasos crean únicamente la base de datos. No requieren ejecutar la aplicación de Python.

#### 1. Localizar los archivos

Abrir la carpeta del repositorio y comprobar que dentro de `sql_datos/` estén estos cinco archivos:

- `estructura.sql`
- `restricciones.sql`
- `indices.sql`
- `triggers.sql`
- `datos_iniciales.sql`

Utilizar los archivos completos del repositorio.

#### 2. Crear una base vacía

1. Abrir pgAdmin.
2. En el panel izquierdo, desplegar `Servers` y conectarse al servidor PostgreSQL.
3. Introducir la contraseña del servidor si se solicita.
4. Hacer clic derecho sobre `Databases`.
5. Seleccionar `Create → Database`.
6. Escribir `restaurante_prueba` en el nombre y pulsar `Save`.

Si ese nombre ya existe, crear otra base con un nombre diferente. Debe ser una base nueva y vacía.

#### 3. Comprobar la conexión

Hacer clic derecho sobre la base recién creada y seleccionar `Query Tool`.

Ejecutar:

```sql
SELECT current_database();
```

El resultado debe coincidir con el nombre de la base que se acaba de crear.

Todos los archivos siguientes deben ejecutarse en esa misma base.

#### 4. Ejecutar los archivos

Desde el Query Tool, utilizar la opción de abrir archivo de la barra de herramientas para abrir cada archivo SQL de la carpeta `bd/`.

Ejecutarlos en este orden:

1. `estructura.sql`
2. `restricciones.sql`
3. `indices.sql`
4. `triggers.sql`
5. `datos_iniciales.sql`

Para cada archivo:

1. Abrirlo en el Query Tool conectado a la base de prueba.
2. Hacer clic dentro del editor y seleccionar todo su contenido.
3. Pulsar F5 para ejecutar el archivo completo.
4. Revisar la pestaña `Messages`.
5. Continuar únicamente si la ejecución terminó sin errores.

Cada archivo incluye `BEGIN` y `COMMIT`. No es necesario agregar instrucciones adicionales para confirmar sus cambios.

Si aparece un error, detener la carga y ejecutar por separado:

```sql
ROLLBACK;
```

Corregir la causa antes de continuar. Los archivos anteriores que terminaron correctamente con `COMMIT` ya están guardados y no deben ejecutarse otra vez en esa base.

Los scripts se ejecutan una sola vez sobre una base vacía. Para repetir la instalación completa, crear otra base vacía.

#### 5. Verificar la estructura y los datos

Después de ejecutar los cinco archivos, abrir una consulta en la misma base y ejecutar:

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

Los resultados esperados son:

- Tablas: 16.
- Sucursales: 2.
- Mesas: 12.
- Productos: 7.
- Insumos: 9.
- Recetas: 21.
- Lotes: 18.

El orden de las filas del resultado puede variar.

#### 6. Verificar la auditoría

Ejecutar:

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

Deben aparecer entradas de las inserciones realizadas durante la carga, con operación `INSERT`.

El campo `id_usuario` puede aparecer en `NULL`, porque la carga se ejecuta directamente mediante scripts, sin un usuario autenticado en la aplicación.

#### Consideraciones sobre la carga

- Los identificadores se generan automáticamente y no deben escribirse manualmente.
- Los precios, cantidades y caducidades son datos de ejemplo.
- Las fechas de recepción y caducidad dependen del día en que se ejecuta la carga.
- No se crean usuarios, clientes, reservas, visitas ni ventas iniciales.
- Las consultas de comprobación no modifican los datos.
- Si los cinco archivos terminan sin errores y las comprobaciones coinciden, la creación y carga inicial quedaron completadas.
## Conexión compartida con Python

Esta parte permite conectar Python con PostgreSQL, compartir los datos de sesión y ejecutar operaciones dentro de una transacción.

### 1. Preparar Python

Tener Python 3.10 o superior instalado.

Abrir la carpeta del repositorio en VS Code y utilizar una terminal Git Bash.

La terminal debe estar en la raíz de `Proyecto-2-BD-1`, donde están `README.md` y `requirements.txt`.

Comprobar Python:

```bash
python --version
```

Crear el entorno virtual, si todavía no existe:

```bash
python -m venv .venv
```

Activarlo:

```bash
source .venv/Scripts/activate
```

Debe aparecer `(.venv)` en la terminal. Activarlo cada vez que se abra una terminal nueva para trabajar con el proyecto.

### 2. Instalar las dependencias

Con el entorno activo, ejecutar:

```bash
python -m pip install -r requirements.txt
```

El archivo instala Psycopg, la librería utilizada para conectar Python con PostgreSQL.

Comprobar su instalación:

```bash
python -c "import psycopg; print(psycopg.__version__)"
```

Con las dependencias actuales debe mostrar `3.3.6`.

### 3. Configurar la conexión

En la raíz del repositorio, copiar `config.example.ini` y nombrar la copia `config.ini`.

Si ya existe `config.ini`, editarlo en lugar de reemplazarlo.

Completar sus valores:

```ini
[postgresql]
host = localhost
port = 5432
dbname = restaurante_prueba
user = postgres
password = CAMBIAR_AQUI
```

- `host`: dirección del servidor PostgreSQL. Para una instalación local se utiliza `localhost`.
- `port`: puerto configurado en PostgreSQL.
- `dbname`: nombre exacto de la base creada y cargada siguiendo los pasos de SQL. Si se utilizó otro nombre, reemplazar `restaurante_prueba`.
- `user`: usuario de PostgreSQL con acceso a esa base.
- `password`: contraseña de ese usuario.

El usuario de PostgreSQL es distinto de los usuarios de la aplicación almacenados en la tabla `usuario`.

Guardar el archivo antes de ejecutar las pruebas.

`config.ini` es una configuración personal y está excluido de Git mediante `.gitignore`. El archivo `config.example.ini` sí se conserva en el repositorio para que cada integrante prepare su configuración.

### 4. Archivos compartidos

Los archivos Python están en `funcionalidades_py/`.

- `conexion.py`: contiene `obtener_conexion()`, que lee `config.ini` y abre una conexión.
- `sesion.py`: contiene `crear_sesion(p_id_usuario, p_rol, p_id_sucursal)`, que devuelve un diccionario con esos tres datos.
- `transacciones.py`: contiene `establecer_usuario_bitacora()` y `ejecutar_transaccion()`.

`crear_sesion()` organiza los datos y comprueba que el rol sea válido. No verifica contraseñas ni realiza el inicio de sesión.

El módulo de autenticación debe construir la sesión utilizando los datos reales del usuario después de validar sus credenciales.

### 5. Ejecutar las pruebas

Ejecutar los comandos desde la raíz del repositorio, con el entorno virtual activo y PostgreSQL en funcionamiento.

Primero comprobar la conexión:

```bash
python -m funcionalidades_py.prueba_conexion
```

Debe mostrar una conexión exitosa, el nombre de la base indicada en `config.ini` y el usuario de PostgreSQL.

Comprobar la estructura de la sesión:

```bash
python -m funcionalidades_py.prueba_sesion
```

Debe mostrar el usuario de ejemplo `1`, el rol `gerente` y la sucursal `2`.

Comprobar el contexto del usuario de bitácora:

```bash
python -m funcionalidades_py.prueba_transacciones
```

Debe mostrar el identificador `1` dentro de la transacción y `None` después del rollback.

Comprobar la ejecución compartida y el manejo de errores:

```bash
python -m funcionalidades_py.prueba_operacion
```

Debe encontrar Oakland Mall, mostrar un error intencional de división por cero y realizar otra consulta exitosa después del error.

La división por cero es parte de la prueba; no indica un fallo de instalación.

Estas pruebas no modifican las tablas. Las sesiones utilizadas son ejemplos en memoria y no representan un inicio de sesión real ni comprueban la existencia de esos usuarios.

### 6. Acuerdo para utilizar las transacciones

Los módulos deben utilizar:

```python
ejecutar_transaccion(p_sesion, p_operacion, p_datos)
```

Sus parámetros son:

- `p_sesion`: diccionario del usuario autenticado.
- `p_operacion`: función que realizará la operación.
- `p_datos`: diccionario con los datos necesarios.

La función recibida como operación debe aceptar tres parámetros, en este orden:

```python
def nombre_operacion(p_conexion, p_sesion, p_datos):
```

Al pasarla a `ejecutar_transaccion`, se escribe su nombre sin paréntesis.

La operación debe:

- Utilizar la conexión recibida.
- Comprobar los permisos y la sucursal que correspondan.
- Ejecutar consultas con parámetros.
- Devolver el resultado necesario.
- Permitir que los errores lleguen al manejador compartido.

No debe abrir otra conexión ni ejecutar `commit`, `rollback` o `close`.

`ejecutar_transaccion()` establece el usuario responsable para la bitácora, ejecuta la operación, confirma con `commit` si termina correctamente y revierte con `rollback` si falla. Finalmente cierra la conexión.

El resultado se devuelve después de que el commit termina correctamente. Esto incluye la comprobación de las restricciones diferidas de capacidad y horarios.
La consola debe capturar los errores comunicados y mostrarlos al usuario.

### 7. Uso con usuarios reales

Antes de registrar cambios auditados, la sesión debe contener un `id_usuario` existente en la tabla `usuario`, obtenido del inicio de sesión real.
No deben utilizarse las sesiones de ejemplo de los archivos de prueba para registrar operaciones reales. Cada reserva y sus mesas, cada visita y sus mesas, y cada venta con sus detalles y consumo de ingredientes deben ejecutarse dentro de su respectiva transacción completa.
