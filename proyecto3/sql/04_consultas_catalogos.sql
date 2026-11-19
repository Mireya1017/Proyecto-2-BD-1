
-- ============================================================
-- PROYECTO 3 - CONSULTAS ANALITICAS DE CATALOGOS
-- Responsable: Nathalie
--
-- Proposito:
-- Analizar la distribucion y capacidad de mesas
-- por sucursal y zona.
--
-- Entrada:
-- Dimensiones dim_sucursal y dim_mesa del DataMart.
--
-- Salida:
-- Consultas de mesas, capacidad y distribucion.
--
-- Ejecucion:
-- Abrir en pgAdmin conectado a restaurante_olap.
-- Ejecutar despues de cargar las dimensiones.
--
-- Consultas de solo lectura.
-- ============================================================


-- ============================================================
-- CONSULTA 1: MESAS POR SUCURSAL
-- ============================================================

SELECT
    s.id_sucursal,
    s.nombre AS sucursal,
    COUNT(m.id_mesa) AS cantidad_mesas
FROM dim_sucursal AS s
LEFT JOIN dim_mesa AS m
    ON m.id_sucursal = s.id_sucursal
GROUP BY
    s.id_sucursal,
    s.nombre
ORDER BY
    s.id_sucursal;


-- ============================================================
-- CONSULTA 2: CAPACIDAD TOTAL POR SUCURSAL
-- ============================================================

SELECT
    s.id_sucursal,
    s.nombre AS sucursal,
    COALESCE(
        SUM(m.capacidad), 0
    ) AS capacidad_total
FROM dim_sucursal AS s
LEFT JOIN dim_mesa AS m
    ON m.id_sucursal = s.id_sucursal
GROUP BY
    s.id_sucursal,
    s.nombre
ORDER BY
    s.id_sucursal;


-- ============================================================
-- CONSULTA 3: DISTRIBUCION DE MESAS POR ZONA
-- ============================================================

SELECT
    s.id_sucursal,
    s.nombre AS sucursal,
    m.zona,
    COUNT(m.id_mesa) AS cantidad_mesas,
    SUM(m.capacidad) AS capacidad_zona
FROM dim_sucursal AS s
JOIN dim_mesa AS m
    ON m.id_sucursal = s.id_sucursal
GROUP BY
    s.id_sucursal,
    s.nombre,
    m.zona
ORDER BY
    s.id_sucursal,
    m.zona;
