
-- ============================================================
-- PROYECTO 3 - EXTRACCION DE CATALOGOS DEL PROYECTO 2
-- Responsable: Nathalie
--
-- Proposito:
-- Obtener los catalogos originales de sucursales y
-- mesas para generar las fuentes del Proyecto 3.
--
-- Entrada:
-- Base operativa del Proyecto 2 (restaurante).
--
-- Salidas:
-- sucursales.csv y mesas.csv mediante exportacion.
--
-- Ejecucion:
-- Abrir en pgAdmin conectado a la base del Proyecto 2.
-- Ejecutar cada SELECT y exportar los resultados a CSV.
--
-- Consultas de solo lectura.
-- No modifican datos del Proyecto 2.
-- ============================================================


-- CONSULTA 1: CATALOGO DE SUCURSALES

SELECT
    id_sucursal,
    nombre,
    direccion
FROM sucursal
ORDER BY id_sucursal;


-- CONSULTA 2: CATALOGO DE MESAS

SELECT
    id_mesa,
    id_sucursal,
    numero,
    capacidad,
    zona
FROM mesa
ORDER BY id_sucursal, id_mesa;
