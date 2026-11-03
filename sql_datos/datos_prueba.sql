-- sql_datos/datos_prueba_pablo.sql
-- Datos de demostración y prueba para las operaciones de Pablo (Clientes y Reservas con mesas).
-- Se ejecutan dentro de una transacción para que los triggers validen capacidad y horarios al hacer COMMIT.

BEGIN;

-- 1. Inserción de clientes de ejemplo
INSERT INTO cliente (nombre, telefono)
VALUES
    ('Carlos Méndez', '5555-1020'),
    ('Ana Lucía Morales', '5555-3040')
ON CONFLICT DO NOTHING;

-- 2. Registro de una reserva de prueba con asignación de mesa en la misma transacción
WITH nuevo_cli AS (
    SELECT id_cliente FROM cliente WHERE nombre = 'Carlos Méndez' ORDER BY id_cliente LIMIT 1
),
mesa_disp AS (
    SELECT id_mesa, id_sucursal
    FROM mesa
    WHERE id_sucursal = 1 AND zona = 'interior' AND capacidad >= 2
    ORDER BY id_mesa LIMIT 1
),
ins_reserva AS (
    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio,
        fecha_hora_fin_estimada, cantidad_personas, estado
    )
    SELECT
        nc.id_cliente,
        md.id_sucursal,
        TIMESTAMP '2026-11-20 19:00:00',
        TIMESTAMP '2026-11-20 21:00:00',
        2,
        'confirmada'
    FROM nuevo_cli nc
    CROSS JOIN mesa_disp md
    RETURNING id_reserva
)
INSERT INTO reserva_mesa (id_reserva, id_mesa)
SELECT ir.id_reserva, md.id_mesa
FROM ins_reserva ir
CROSS JOIN mesa_disp md;

COMMIT;