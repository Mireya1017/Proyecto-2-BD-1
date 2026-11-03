-- MODULO DE INVENTARIO Y VENTAS
-- Responsable: Nathalie
-- Consulta 1: Existencias utilizables por sucursal
-- Los lotes vencidos no se consideran disponibles.

SELECT
    s.nombre AS sucursal,
    i.nombre AS insumo,
    i.unidad_medida,
    i.existencia_minima,
    COALESCE(
        SUM(
            CASE
                WHEN l.fecha_caducidad >= CURRENT_DATE
                THEN l.cantidad_disponible
                ELSE 0
            END
        ), 0
    ) AS existencia_utilizable
FROM sucursal AS s
CROSS JOIN insumo AS i
LEFT JOIN lote AS l
    ON l.id_sucursal = s.id_sucursal
    AND l.id_insumo = i.id_insumo
GROUP BY
    s.id_sucursal,
    s.nombre,
    i.id_insumo,
    i.nombre,
    i.unidad_medida,
    i.existencia_minima
ORDER BY
    s.nombre,
    i.nombre;

-- =====================================================
-- CONSULTA 2: LOTES Y FECHAS DE CADUCIDAD
-- Responsable: Nathalie
-- =====================================================

SELECT
    s.nombre AS sucursal,
    i.nombre AS insumo,
    l.id_lote,
    l.fecha_recepcion,
    l.fecha_caducidad,
    l.cantidad_disponible,
    i.unidad_medida,
    CASE
        WHEN l.fecha_caducidad < CURRENT_DATE
            THEN 'Vencido'
        WHEN l.cantidad_disponible = 0
            THEN 'Agotado'
        ELSE 'Utilizable'
    END AS estado_lote
FROM lote AS l
JOIN insumo AS i
    ON l.id_insumo = i.id_insumo
JOIN sucursal AS s
    ON l.id_sucursal = s.id_sucursal
ORDER BY
    s.nombre,
    i.nombre,
    l.fecha_caducidad,
    l.id_lote;

-- =====================================================
-- CONSULTA 3: ALERTAS POR EXISTENCIAS BAJAS
-- Responsable: Nathalie
-- Utiliza CTE para calcular existencias por sucursal.
-- Muestra insumos por debajo de su minimo establecido.
-- =====================================================
WITH existencias AS (
    SELECT
        s.id_sucursal,
        s.nombre AS sucursal,
        i.id_insumo,
        i.nombre AS insumo,
        i.unidad_medida,
        i.existencia_minima,
        COALESCE(
            SUM(l.cantidad_disponible) FILTER (
                WHERE l.fecha_caducidad >= CURRENT_DATE
            ), 0
        ) AS existencia_utilizable
    FROM sucursal AS s
    CROSS JOIN insumo AS i
    LEFT JOIN lote AS l
        ON l.id_sucursal = s.id_sucursal
       AND l.id_insumo = i.id_insumo
    GROUP BY
        s.id_sucursal,
        s.nombre,
        i.id_insumo,
        i.nombre,
        i.unidad_medida,
        i.existencia_minima
)
SELECT
    sucursal,
    insumo,
    unidad_medida,
    existencia_minima,
    existencia_utilizable
FROM existencias
WHERE existencia_utilizable < existencia_minima
ORDER BY sucursal, insumo;

-- =====================================================
-- CONSULTA 4: ALERTAS DE PROXIMA CADUCIDAD
-- Responsable: Nathalie
-- Ventana provisional: 7 dias
-- =====================================================

SELECT
    s.nombre AS sucursal,
    i.nombre AS insumo,
    l.id_lote,
    l.fecha_caducidad,
    l.cantidad_disponible,
    i.unidad_medida,
    l.fecha_caducidad - CURRENT_DATE AS dias_restantes
FROM lote AS l
JOIN insumo AS i
    ON l.id_insumo = i.id_insumo
JOIN sucursal AS s
    ON l.id_sucursal = s.id_sucursal
WHERE l.fecha_caducidad >= CURRENT_DATE
  AND l.fecha_caducidad <= CURRENT_DATE + 7
  AND l.cantidad_disponible > 0
ORDER BY
    l.fecha_caducidad,
    s.nombre,
    i.nombre,
    l.id_lote;

-- =====================================================
-- CONSULTA 5: CALCULO DE INGREDIENTES POR VENTA
-- Responsable: Nathalie
-- Simulacion: 2 bowls de pollo y 1 wrap de pollo
-- =====================================================
WITH productos_venta AS (
    SELECT 1 AS id_plato, 2 AS cantidad
    UNION ALL
    SELECT 3 AS id_plato, 1 AS cantidad
),
consumo AS (
    SELECT
        r.id_insumo,
        SUM(r.cantidad * pv.cantidad)
            AS cantidad_necesaria
    FROM productos_venta AS pv
    JOIN receta AS r
        ON pv.id_plato = r.id_plato
    GROUP BY r.id_insumo
)
SELECT
    i.nombre AS ingrediente,
    c.cantidad_necesaria,
    i.unidad_medida
FROM consumo AS c
JOIN insumo AS i
    ON c.id_insumo = i.id_insumo
ORDER BY i.nombre;
-- =====================================================
-- CONSULTA 6: VERIFICACION DE INVENTARIO PARA VENTAS
-- Responsable: Nathalie
-- Verifica ingredientes antes de registrar una venta.
-- =====================================================
WITH productos_venta AS (
    SELECT 1 AS id_plato, 2 AS cantidad
    UNION ALL
    SELECT 3 AS id_plato, 1 AS cantidad
),
ingredientes_necesarios AS (
    SELECT
        r.id_insumo,
        SUM(r.cantidad * pv.cantidad)
            AS cantidad_necesaria
    FROM productos_venta AS pv
    JOIN receta AS r
        ON pv.id_plato = r.id_plato
    GROUP BY r.id_insumo
),
existencias AS (
    SELECT
        i.id_insumo,
        i.nombre AS ingrediente,
        i.unidad_medida,
        COALESCE(
            SUM(l.cantidad_disponible) FILTER (
                WHERE l.fecha_caducidad >= CURRENT_DATE
            ), 0
        ) AS cantidad_disponible
    FROM insumo AS i
    LEFT JOIN lote AS l
        ON i.id_insumo = l.id_insumo
       AND l.id_sucursal = 1
    GROUP BY
        i.id_insumo,
        i.nombre,
        i.unidad_medida
)
SELECT
    e.ingrediente,
    n.cantidad_necesaria,
    e.cantidad_disponible,
    e.unidad_medida,
    CASE
        WHEN e.cantidad_disponible >= n.cantidad_necesaria
            THEN 'SUFICIENTE'
        ELSE 'INSUFICIENTE'
    END AS estado
FROM ingredientes_necesarios AS n
JOIN existencias AS e
    ON n.id_insumo = e.id_insumo
ORDER BY e.ingrediente;