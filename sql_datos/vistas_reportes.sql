-- sql_datos/vistas_reportes_pablo.sql
-- Vista base de apoyo para el reporte acumulado de sucursales.
-- Agrega las reservas y las ventas por separado mediante CTEs antes de combinarlas con la sucursal.

CREATE OR REPLACE VIEW vw_resumen_historico_sucursales AS
WITH cte_reservas AS (
    SELECT
        r.id_sucursal,
        COUNT(r.id_reserva) AS cantidad_reservas
    FROM reserva r
    WHERE r.estado <> 'cancelada'
    GROUP BY r.id_sucursal
),
cte_totales_venta AS (
    SELECT
        v.id_venta,
        vi.id_sucursal,
        COALESCE(SUM(dv.cantidad * dv.precio_unitario), 0.00) AS total_venta
    FROM venta v
    JOIN visita vi ON vi.id_visita = v.id_visita
    LEFT JOIN detalle_venta dv ON dv.id_venta = v.id_venta
    GROUP BY v.id_venta, vi.id_sucursal
),
cte_ventas AS (
    SELECT
        tv.id_sucursal,
        COUNT(tv.id_venta) AS cantidad_ventas,
        COALESCE(SUM(tv.total_venta), 0.00) AS importe_vendido
    FROM cte_totales_venta tv
    GROUP BY tv.id_sucursal
)
SELECT
    s.id_sucursal,
    s.nombre AS sucursal,
    COALESCE(r.cantidad_reservas, 0) AS cantidad_reservas,
    COALESCE(ve.cantidad_ventas, 0) AS cantidad_ventas,
    COALESCE(ve.importe_vendido, 0.00)::NUMERIC(12,2) AS importe_vendido
FROM sucursal s
LEFT JOIN cte_reservas r ON r.id_sucursal = s.id_sucursal
LEFT JOIN cte_ventas ve ON ve.id_sucursal = s.id_sucursal
ORDER BY importe_vendido DESC, cantidad_ventas DESC, s.id_sucursal ASC;