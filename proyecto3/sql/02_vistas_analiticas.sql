/*
================================================================================
Archivo:      proyecto3/sql/02_vistas_analiticas.sql
Autor:        Pablo Andrés Fuentes Barillas
   Definir las 6 vistas analíticas base sobre el modelo estrella de
              restaurante_olap para alimentar consultas de negocio y el tablero
              de visualización sin duplicar conteos ni promedios.
Tablas creadas por proyecto3/sql/01_modelo_estrella.sql:
              - dim_sucursal, dim_mesa, dim_fecha, dim_hora
              - fact_reserva, fact_visita, fact_uso_mesa
Creación o reemplazo de las vistas:
              1. vw_demanda_atencion
              2. vw_reservas_estado
              3. vw_duracion_visitas
              4. vw_liberacion_mesas
              5. vw_capacidad_asignada
              6. vw_uso_mesas
Ejecución:    psql -U postgres -d restaurante_olap -f proyecto3/sql/02_vistas_analiticas.sql
================================================================================
*/

-- -----------------------------------------------------------------------------
-- 1. vw_demanda_atencion
-- Nivel de detalle: Sucursal, fecha y hora (basado en llegada real de visita).
-- Regla: Contar filas y sumar personas únicamente desde fact_visita para evitar
--        duplicaciones por visitas que ocupan múltiples mesas.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_demanda_atencion AS
SELECT
    fv.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fv.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_mes,
    df.dia_semana,
    df.nombre_dia,
    fv.id_hora,
    dh.etiqueta AS etiqueta_hora,
    COUNT(fv.id_visita) AS cantidad_visitas,
    SUM(fv.cantidad_personas) AS total_personas,
    COUNT(fv.id_reserva_origen) AS visitas_con_reserva,
    COUNT(fv.id_visita) - COUNT(fv.id_reserva_origen) AS visitas_sin_reserva
FROM fact_visita fv
INNER JOIN dim_sucursal ds ON fv.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fv.id_fecha = df.id_fecha
INNER JOIN dim_hora dh ON fv.id_hora = dh.id_hora
GROUP BY
    fv.id_sucursal,
    ds.nombre,
    fv.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_mes,
    df.dia_semana,
    df.nombre_dia,
    fv.id_hora,
    dh.etiqueta;


-- -----------------------------------------------------------------------------
-- 2. vw_reservas_estado
-- Nivel de detalle: Sucursal, fecha prevista y estado de reserva.
-- Regla: Incluye porcentaje por estado final respecto al total de reservas de
--        esa sucursal y fecha (usando NULLIF para evitar división entre cero).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_reservas_estado AS
SELECT
    fr.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fr.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_mes,
    df.dia_semana,
    df.nombre_dia,
    fr.estado,
    COUNT(fr.id_reserva) AS cantidad_reservas,
    SUM(fr.cantidad_personas) AS total_personas_reservadas,
    ROUND(
        (COUNT(fr.id_reserva)::NUMERIC / NULLIF(SUM(COUNT(fr.id_reserva)) OVER (PARTITION BY fr.id_sucursal, fr.id_fecha), 0)) * 100.0,
        2
    ) AS porcentaje_estado_dia
FROM fact_reserva fr
INNER JOIN dim_sucursal ds ON fr.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fr.id_fecha = df.id_fecha
GROUP BY
    fr.id_sucursal,
    ds.nombre,
    fr.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_mes,
    df.dia_semana,
    df.nombre_dia,
    fr.estado;


-- -----------------------------------------------------------------------------
-- 3. vw_duracion_visitas
-- Nivel de detalle: Una visita (fila de fact_visita).
-- Fórmula: (fecha_hora_salida - fecha_hora_llegada) expresada en minutos.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_duracion_visitas AS
SELECT
    fv.id_visita,
    fv.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fv.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_semana,
    df.nombre_dia,
    fv.id_hora,
    dh.etiqueta AS etiqueta_hora,
    fv.id_reserva_origen,
    CASE
        WHEN fv.id_reserva_origen IS NOT NULL THEN 'Con reserva'
        ELSE 'Sin reserva'
    END AS tipo_visita,
    fv.fecha_hora_llegada,
    fv.fecha_hora_salida,
    fv.cantidad_personas,
    ROUND(
        EXTRACT(EPOCH FROM (fv.fecha_hora_salida - fv.fecha_hora_llegada)) / 60.0,
        2
    ) AS duracion_visita_minutos
FROM fact_visita fv
INNER JOIN dim_sucursal ds ON fv.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fv.id_fecha = df.id_fecha
INNER JOIN dim_hora dh ON fv.id_hora = dh.id_hora;


-- -----------------------------------------------------------------------------
-- 4. vw_liberacion_mesas
-- Nivel de detalle: Una asignación visita-mesa (fila de fact_uso_mesa).
-- Fórmula: (fecha_hora_liberacion - fecha_hora_salida) expresada en minutos.
-- Límite de interpretación: Representa el intervalo registrado hasta la
--        disponibilidad de la mesa; no equivale a "duración exacta de limpieza".
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_liberacion_mesas AS
SELECT
    fum.id_visita_origen,
    fum.id_mesa,
    dm.numero AS numero_mesa,
    dm.zona,
    dm.capacidad AS capacidad_mesa,
    fum.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fum.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_semana,
    df.nombre_dia,
    fum.fecha_hora_llegada,
    fum.fecha_hora_salida,
    fum.fecha_hora_liberacion,
    ROUND(
        EXTRACT(EPOCH FROM (fum.fecha_hora_liberacion - fum.fecha_hora_salida)) / 60.0,
        2
    ) AS tiempo_liberacion_minutos
FROM fact_uso_mesa fum
INNER JOIN dim_mesa dm ON fum.id_mesa = dm.id_mesa
INNER JOIN dim_sucursal ds ON fum.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fum.id_fecha = df.id_fecha;


-- -----------------------------------------------------------------------------
-- 5. vw_capacidad_asignada
-- Nivel de detalle: Una visita (fila de fact_visita).
-- Fórmula: (cantidad_personas / capacidad_asignada) * 100.
-- Límite de interpretación: Mide aprovechamiento de sillas sobre mesas
--        asignadas en la visita, no ocupación total del salón en la jornada.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_capacidad_asignada AS
SELECT
    fv.id_visita,
    fv.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fv.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_semana,
    df.nombre_dia,
    fv.id_hora,
    dh.etiqueta AS etiqueta_hora,
    fv.id_reserva_origen,
    fv.cantidad_personas,
    fv.capacidad_asignada,
    ROUND(
        (fv.cantidad_personas::NUMERIC / NULLIF(fv.capacidad_asignada, 0)) * 100.0,
        2
    ) AS aprovechamiento_porcentaje
FROM fact_visita fv
INNER JOIN dim_sucursal ds ON fv.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fv.id_fecha = df.id_fecha
INNER JOIN dim_hora dh ON fv.id_hora = dh.id_hora;


-- -----------------------------------------------------------------------------
-- 6. vw_uso_mesas
-- Nivel de detalle: Una asignación visita-mesa (fila de fact_uso_mesa).
-- Fórmula: (fecha_hora_liberacion - fecha_hora_llegada) expresada en minutos.
-- Regla: No incluye cantidad_personas de la visita para impedir sumas
--        duplicadas cuando una visita ocupa varias mesas.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_uso_mesas AS
SELECT
    fum.id_visita_origen,
    fum.id_mesa,
    dm.numero AS numero_mesa,
    dm.capacidad AS capacidad_mesa,
    dm.zona,
    fum.id_sucursal,
    ds.nombre AS nombre_sucursal,
    fum.id_fecha,
    df.fecha,
    df.anio,
    df.mes,
    df.nombre_mes,
    df.dia_semana,
    df.nombre_dia,
    fum.fecha_hora_llegada,
    fum.fecha_hora_salida,
    fum.fecha_hora_liberacion,
    ROUND(
        EXTRACT(EPOCH FROM (fum.fecha_hora_salida - fum.fecha_hora_llegada)) / 60.0,
        2
    ) AS minutos_ocupacion_cliente,
    ROUND(
        EXTRACT(EPOCH FROM (fum.fecha_hora_liberacion - fum.fecha_hora_salida)) / 60.0,
        2
    ) AS minutos_liberacion,
    ROUND(
        EXTRACT(EPOCH FROM (fum.fecha_hora_liberacion - fum.fecha_hora_llegada)) / 60.0,
        2
    ) AS minutos_uso_mesa
FROM fact_uso_mesa fum
INNER JOIN dim_mesa dm ON fum.id_mesa = dm.id_mesa
INNER JOIN dim_sucursal ds ON fum.id_sucursal = ds.id_sucursal
INNER JOIN dim_fecha df ON fum.id_fecha = df.id_fecha;