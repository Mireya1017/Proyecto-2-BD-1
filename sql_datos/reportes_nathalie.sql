-- =====================================================
-- REPORTE 1: TOP 10 DE PRODUCTOS MAS VENDIDOS
-- Responsable: Nathalie
-- Proyecto 02 - Base de Datos 1
-- =====================================================

WITH ventas_productos AS (
    SELECT
        dv.id_plato,
        SUM(dv.cantidad) AS unidades_vendidas,
        SUM(
            dv.cantidad * dv.precio_unitario
        ) AS ingresos_totales
    FROM detalle_venta AS dv
    JOIN venta AS v
        ON dv.id_venta = v.id_venta
    GROUP BY dv.id_plato
)
SELECT
    p.id_plato,
    p.nombre AS producto,
    vp.unidades_vendidas,
    vp.ingresos_totales
FROM ventas_productos AS vp
JOIN plato AS p
    ON vp.id_plato = p.id_plato
ORDER BY
    vp.unidades_vendidas DESC,
    p.nombre ASC,
    p.id_plato ASC
LIMIT 10;


-- =====================================================
-- REPORTE 2: CADUCIDADES POR MES Y SUCURSAL
-- Responsable: Nathalie
-- Ejemplo: noviembre de 2026, Oakland Mall
-- =====================================================

WITH parametros AS (
    SELECT
        2026::INTEGER AS anio,
        11::INTEGER AS mes,
        1::INTEGER AS id_sucursal
),
periodo AS (
    SELECT
        MAKE_DATE(anio, mes, 1) AS inicio,
        (MAKE_DATE(anio, mes, 1)
            + INTERVAL '1 month')::DATE AS fin,
        id_sucursal
    FROM parametros
)
SELECT
    s.nombre AS sucursal,
    i.nombre AS insumo,
    l.id_lote,
    l.fecha_caducidad,
    l.cantidad_disponible,
    i.unidad_medida
FROM lote AS l
JOIN insumo AS i
    ON l.id_insumo = i.id_insumo
JOIN sucursal AS s
    ON l.id_sucursal = s.id_sucursal
CROSS JOIN periodo AS p
WHERE l.id_sucursal = p.id_sucursal
  AND l.fecha_caducidad >= p.inicio
  AND l.fecha_caducidad < p.fin
ORDER BY
    l.fecha_caducidad,
    i.nombre,
    l.id_lote;