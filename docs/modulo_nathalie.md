# Módulo de inventario y ventas — Nathalie

## Alcance
Inventario por sucursal, consulta de lotes, entradas directas, alertas, ventas con consumo FEFO y dos consultas de reportes. No incluye compras ni proveedores.

## Dependencias
Utiliza `funcionalidades_py.conexion.obtener_conexion`, `sesion.crear_sesion` y `transacciones.ejecutar_transaccion` oficiales. No modificar sus implementaciones. Para operaciones de escritura se requiere una sesión de usuario autenticado existente en la tabla `usuario`.

## Contratos de operaciones
- `registrar_entrada(p_conexion, p_sesion, p_datos) -> id_lote`: `p_datos` requiere `id_insumo`, `id_sucursal`, `fecha_recepcion`, `fecha_caducidad`, `cantidad`. Roles: administrador o gerente de su sucursal. Se ejecuta con `ejecutar_transaccion(p_sesion, registrar_entrada, p_datos)`; **la función no confirma ni revierte**.
- `registrar_venta(p_conexion, p_sesion, p_datos) -> dict`: `p_datos` requiere `id_visita` y `productos=[{id_plato, cantidad}, ...]`. Roles: administrador, gerente o mesero de su sucursal. Visita abierta; precios vigentes guardados en `detalle_venta`; suma ingredientes de todas las líneas; lotes bloqueados y consumidos por fecha de caducidad e ID. Ejecutar con `ejecutar_transaccion`; **la función no confirma ni revierte**.
- `consultar_existencias(id_sucursal, sesion)`, `consultar_lotes(id_sucursal, id_insumo, sesion)`, `consultar_alertas_existencias(id_sucursal, sesion)`, `consultar_alertas_caducidad(id_sucursal, dias=7, *, p_sesion=sesion)`: lecturas protegidas por rol y sucursal.
- `reporte_top_productos(sesion)`, `reporte_caducidades_mensual(sesion, anio, mes, id_sucursal)`: solo administradores. La sesión debe proceder de autenticación, no de un diccionario construido por el usuario.

## Menús para Yu-fong
Importar de `funcionalidades_py.consola.consola_nathalie` las funciones `menu_inventario(p_sesion)`, `menu_ventas(p_sesion)` y `menu_reportes_nathalie(p_sesion)`. No editar `menu_principal.py` desde esta rama; la integración corresponde a su responsable.

## Reportes y limitaciones
- Top 10: ordenado por unidades vendidas, desempate por nombre e ID; ingresos calculados con precio guardado en el detalle. Se debe probar con ventas reales.
- Reporte mensual actual: **lotes cuya fecha de caducidad cae en el mes seleccionado**. Las cantidades son las cantidades *actuales*, NO el stock al cierre del mes consultado. El menú permite además consultar existencias *actuales* por debajo del mínimo; **no equivale a un reporte histórico mensual de agotamiento**.
- El criterio exacto de alerta del 15 % y la ventana definitiva de próxima caducidad siguen pendientes de acuerdo. La ventana de 7 días es provisional. Si se exige histórico mensual de existencias, solicitar a Mireya una migración para registrar movimientos o cortes históricos; no modificar la estructura oficial de manera unilateral.

## Pruebas
`python -m compileall -q funcionalidades_py` valida sintaxis. Las pruebas unitarias existentes cubren rechazos, simulación FEFO y consultas. En base local de pruebas, con usuario autenticado, verificar: entrada exitosa, venta exitosa, detalle y total, lotes consumidos FEFO, bitácora, venta fallida con rollback, y Top 10 con ventas. No ejecutar datos de demostración repetidamente en la BD central.

## Precauciones
No publicar `config.ini`, `.venv`, hashes ni credenciales. La comprobación de rol basada en un diccionario solo es confiable cuando la sesión proviene de autenticación real. Las lecturas antiguas de pruebas sin sesión deben adaptarse al nuevo contrato protegido.
