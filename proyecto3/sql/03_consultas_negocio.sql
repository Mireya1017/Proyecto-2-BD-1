/*
================================================================================
Archivo:      proyecto3/sql/03_consultas_negocio.sql
Autor:        Pablo Andrés Fuentes Barillas
Ejecutar las 7 consultas de negocio requeridas sobre las vistas
              analíticas de restaurante_olap para análisis operacional entre
              Oakland Mall y Ciudad Cayalá y validación de indicadores.
Vistas creadas por proyecto3/sql/02_vistas_analiticas.sql:
              - vw_demanda_atencion
              - vw_reservas_estado
              - vw_duracion_visitas
              - vw_liberacion_mesas
              - vw_capacidad_asignada
              - vw_uso_mesas
Conjuntos de resultados analíticos para:
              1. Demanda por día y hora
              2. Comparación entre sucursales
              3. Reservas por estado y sus porcentajes
              4. Duración promedio de visitas
              5. Tiempo promedio hasta liberación
              6. Aprovechamiento de capacidad
              7. Uso de mesas
Ejecución:    psql -U postgres -d restaurante_olap -f proyecto3/sql/03_consultas_negocio.sql
================================================================================
*/

-- -----------------------------------------------------------------------------
-- 1. DEMANDA POR DÍA Y HORA
-- Muestra el comportamiento de visitas y comensales por día de la semana y
-- franja horaria de llegada en cada sucursal.
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    dia_semana,
    nombre_dia,
    id_hora,
    etiqueta_hora,
    SUM(cantidad_visitas) AS total_visitas,
    SUM(total_personas) AS total_personas,
    SUM(visitas_con_reserva) AS visitas_con_reserva,
    SUM(visitas_sin_reserva) AS visitas_sin_reserva,
    ROUND(
        SUM(total_personas)::NUMERIC / NULLIF(SUM(cantidad_visitas), 0),
        2
    ) AS promedio_personas_por_visita
FROM vw_demanda_atencion
GROUP BY
    id_sucursal,
    nombre_sucursal,
    dia_semana,
    nombre_dia,
    id_hora,
    etiqueta_hora
ORDER BY
    id_sucursal,
    dia_semana,
    id_hora;


-- -----------------------------------------------------------------------------
-- 2. COMPARACIÓN ENTRE SUCURSALES
-- Consolida el desempeño global de Oakland Mall vs. Ciudad Cayalá combinando
-- volumen de atención, duración promedio y aprovechamiento ponderado.
-- -----------------------------------------------------------------------------
WITH resumen_visitas AS (
    SELECT
        id_sucursal,
        nombre_sucursal,
        COUNT(id_visita) AS total_visitas,
        SUM(cantidad_personas) AS total_personas,
        SUM(capacidad_asignada) AS total_capacidad_asignada,
        ROUND(
            (SUM(cantidad_personas)::NUMERIC / NULLIF(SUM(capacidad_asignada), 0)) * 100.0,
            2
        ) AS aprovechamiento_agregado_pct
    FROM vw_capacidad_asignada
    GROUP BY
        id_sucursal,
        nombre_sucursal
),
resumen_duracion AS (
    SELECT
        id_sucursal,
        ROUND(AVG(duracion_visita_minutos), 2) AS duracion_promedio_visita_min
    FROM vw_duracion_visitas
    GROUP BY
        id_sucursal
),
resumen_reservas AS (
    SELECT
        id_sucursal,
        SUM(cantidad_reservas) AS total_reservas,
        SUM(CASE WHEN estado = 'atendida' THEN cantidad_reservas ELSE 0 END) AS reservas_atendidas,
        ROUND(
            (SUM(CASE WHEN estado = 'atendida' THEN cantidad_reservas ELSE 0 END)::NUMERIC
            / NULLIF(SUM(cantidad_reservas), 0)) * 100.0,
            2
        ) AS tasa_efectividad_reservas_pct
    FROM vw_reservas_estado
    GROUP BY
        id_sucursal
)
SELECT
    rv.id_sucursal,
    rv.nombre_sucursal,
    rv.total_visitas,
    rv.total_personas,
    rv.total_capacidad_asignada,
    rv.aprovechamiento_agregado_pct,
    rd.duracion_promedio_visita_min,
    COALESCE(rr.total_reservas, 0) AS total_reservas,
    COALESCE(rr.reservas_atendidas, 0) AS reservas_atendidas,
    rr.tasa_efectividad_reservas_pct
FROM resumen_visitas rv
LEFT JOIN resumen_duracion rd ON rv.id_sucursal = rd.id_sucursal
LEFT JOIN resumen_reservas rr ON rv.id_sucursal = rr.id_sucursal
ORDER BY
    rv.id_sucursal;


-- -----------------------------------------------------------------------------
-- 3. RESERVAS POR ESTADO Y SUS PORCENTAJES
-- Calcula la distribución de estados finales por sucursal.
-- Fórmula: (Reservas de ese estado / Reservas con estado final) * 100.
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    estado,
    SUM(cantidad_reservas) AS total_reservas_estado,
    SUM(total_personas_reservadas) AS total_personas_reservadas,
    ROUND(
        (SUM(cantidad_reservas)::NUMERIC
        / NULLIF(SUM(SUM(cantidad_reservas)) OVER (PARTITION BY id_sucursal), 0)) * 100.0,
        2
    ) AS porcentaje_estado_sucursal
FROM vw_reservas_estado
GROUP BY
    id_sucursal,
    nombre_sucursal,
    estado
ORDER BY
    id_sucursal,
    total_reservas_estado DESC;


-- -----------------------------------------------------------------------------
-- 4. DURACIÓN PROMEDIO DE VISITAS
-- Evalúa el tiempo real de permanencia (salida - llegada) segmentado por
-- sucursal y tipo de visita (Con reserva vs. Sin reserva).
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    tipo_visita,
    COUNT(id_visita) AS cantidad_visitas,
    ROUND(AVG(duracion_visita_minutos), 2) AS duracion_promedio_min,
    MIN(duracion_visita_minutos) AS duracion_minima_min,
    MAX(duracion_visita_minutos) AS duracion_maxima_min
FROM vw_duracion_visitas
GROUP BY
    id_sucursal,
    nombre_sucursal,
    tipo_visita
ORDER BY
    id_sucursal,
    tipo_visita;


-- -----------------------------------------------------------------------------
-- 5. TIEMPO PROMEDIO HASTA LIBERACIÓN
-- Calcula el intervalo promedio entre la salida del cliente y la liberación de
-- la mesa por sucursal y zona.
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    zona,
    COUNT(*) AS total_asignaciones,
    ROUND(AVG(tiempo_liberacion_minutos), 2) AS tiempo_promedio_liberacion_min,
    MIN(tiempo_liberacion_minutos) AS tiempo_minimo_liberacion_min,
    MAX(tiempo_liberacion_minutos) AS tiempo_maximo_liberacion_min
FROM vw_liberacion_mesas
GROUP BY
    id_sucursal,
    nombre_sucursal,
    zona
ORDER BY
    id_sucursal,
    zona;


-- -----------------------------------------------------------------------------
-- 6. APROVECHAMIENTO DE CAPACIDAD
-- Calcula el aprovechamiento agregado ponderado por sucursal y mes.
-- Regla: Suma de personas / Suma de capacidad asignada * 100 (nunca AVG simple).
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    anio,
    mes,
    nombre_mes,
    COUNT(id_visita) AS total_visitas,
    SUM(cantidad_personas) AS total_personas,
    SUM(capacidad_asignada) AS total_capacidad_asignada,
    SUM(capacidad_asignada) - SUM(cantidad_personas) AS sillas_ociosas_en_asignacion,
    ROUND(
        (SUM(cantidad_personas)::NUMERIC / NULLIF(SUM(capacidad_asignada), 0)) * 100.0,
        2
    ) AS aprovechamiento_agregado_pct
FROM vw_capacidad_asignada
GROUP BY
    id_sucursal,
    nombre_sucursal,
    anio,
    mes,
    nombre_mes
ORDER BY
    id_sucursal,
    anio,
    mes;


-- -----------------------------------------------------------------------------
-- 7. USO DE MESAS
-- Analiza la frecuencia de asignación y los minutos totales y promedio de uso
-- (liberación - llegada) por mesa física en cada sucursal.
-- -----------------------------------------------------------------------------
SELECT
    id_sucursal,
    nombre_sucursal,
    id_mesa,
    numero_mesa,
    zona,
    capacidad AS capacidad_mesa,
    COUNT(id_visita_origen) AS veces_asignada,
    SUM(minutos_ocupacion_cliente) AS total_minutos_cliente,
    SUM(minutos_liberacion) AS total_minutos_liberacion,
    SUM(minutos_uso_mesa) AS total_minutos_uso_mesa,
    ROUND(AVG(minutos_uso_mesa), 2) AS promedio_minutos_uso_por_asignacion
FROM vw_uso_mesas
GROUP BY
    id_sucursal,
    nombre_sucursal,
    id_mesa,
    numero_mesa,
    zona,
    capacidad
ORDER BY
    id_sucursal,
    total_minutos_uso_mesa DESC,
    numero_mesa;