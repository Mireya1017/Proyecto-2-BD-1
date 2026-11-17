# Acuerdos de Integración del Equipo

## 1. Conexión Compartida a PostgreSQL
- Todos los integrantes deben importar `transaccion` de `app.database`.
- Ningún módulo debe crear una cadena de conexión propia o configurar drivers independientes.
- Las credenciales se leen exclusivamente desde variables de entorno o archivo `.env`.

## 2. Identificación del Usuario y Auditoría
- Al ejecutar operaciones transaccionales, se debe proporcionar `id_usuario=sesion.id_usuario`.
- El gestor `transaccion` invoca `SELECT set_config('app.id_usuario', %s, true);`.
- El parámetro `true` garantiza ámbito local a la transacción: al ejecutarse `COMMIT` o `ROLLBACK`, la variable se borra automáticamente, evitando contaminación entre sesiones.

## 3. Roles y Matriz de Permisos
| Módulo / Operación | Administrador | Gerente | Mesero |
| :--- | :---: | :---: | :---: |
| Administración de Usuarios | Sí (Global) | No | No |
| Consulta de Bitácora | Sí (Global) | No | No |
| Reporte de Sucursales | Sí (Global) | No | No |
| Gestión de Reservas | Sí (Todas las sedes) | Sí (Su sucursal) | Sí (Su sucursal) |
| Proveedores y Compras | Sí (Todas las sedes) | Sí (Su sucursal) | No |

## 4. Reporte de Sucursales sin Multiplicación de Totales
- Para consolidar reservas y ventas, se utilizan dos CTEs (`metricas_reservas` y `metricas_ventas`) independientes.
- Ambas se unen a la tabla `sucursal` mediante `LEFT JOIN`.
- Esto previene el producto cartesiano `reservas * ventas` garantizando cifras exactas.
