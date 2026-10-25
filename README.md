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

Abrir la carpeta del repositorio y comprobar que dentro de `bd/` estén estos cinco archivos:

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
