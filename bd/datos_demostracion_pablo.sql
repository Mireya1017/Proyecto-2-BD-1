-- ==============================================================================
-- DATOS DE DEMOSTRACIÓN Y PRUEBAS - PABLO (INTEGRANTE 2)
-- ==============================================================================

BEGIN;

-- 1. USUARIOS DEL SISTEMA
INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
SELECT 
    'admin_pablo',
    'pbkdf2_sha256$100000$11111111111111111111111111111111$4f8dd3a5788a2a297d4f6c6a25f5ce120547e0fed19f4c89fe9409bf019e836d',
    'administrador',
    s.id_sucursal
FROM sucursal s
WHERE s.nombre = 'Oakland Mall'
ON CONFLICT (nombre_usuario) DO NOTHING;

INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
SELECT 
    'gerente_oakland',
    'pbkdf2_sha256$100000$22222222222222222222222222222222$efeb6b6a7435359db04c999050508949d23f4d4d2cdff3aa35d40d6d9328f1e5',
    'gerente',
    s.id_sucursal
FROM sucursal s
WHERE s.nombre = 'Oakland Mall'
ON CONFLICT (nombre_usuario) DO NOTHING;

INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
SELECT 
    'gerente_cayala',
    'pbkdf2_sha256$100000$22222222222222222222222222222222$efeb6b6a7435359db04c999050508949d23f4d4d2cdff3aa35d40d6d9328f1e5',
    'gerente',
    s.id_sucursal
FROM sucursal s
WHERE s.nombre = 'Ciudad Cayalá'
ON CONFLICT (nombre_usuario) DO NOTHING;

INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
SELECT 
    'mesero_oakland',
    'pbkdf2_sha256$100000$33333333333333333333333333333333$c59d16e5b6cf59e7d564003e6a947fe61749966949c33697f67de6d711610877',
    'mesero',
    s.id_sucursal
FROM sucursal s
WHERE s.nombre = 'Oakland Mall'
ON CONFLICT (nombre_usuario) DO NOTHING;

INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
SELECT 
    'mesero_cayala',
    'pbkdf2_sha256$100000$33333333333333333333333333333333$c59d16e5b6cf59e7d564003e6a947fe61749966949c33697f67de6d711610877',
    'mesero',
    s.id_sucursal
FROM sucursal s
WHERE s.nombre = 'Ciudad Cayalá'
ON CONFLICT (nombre_usuario) DO NOTHING;

-- 2. CLIENTES DE DEMOSTRACIÓN
INSERT INTO cliente (nombre, telefono)
VALUES
    ('Carlos Mendoza', '5551-1111'),
    ('Ana Lucía Gómez', '5552-2222'),
    ('Fernando Castillo', '5553-3333'),
    ('Sofía Morales', '5554-4444'),
    ('Diego Herrera', '5555-5555')
ON CONFLICT DO NOTHING;

-- 3. RESERVAS
DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa INTEGER;
    v_id_reserva INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Carlos Mendoza' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Oakland Mall' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 3 LIMIT 1;

    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
    ) VALUES (
        v_id_cliente, v_id_sucursal,
        CURRENT_DATE + INTERVAL '1 day 13:00:00',
        CURRENT_DATE + INTERVAL '1 day 15:00:00',
        4, 'confirmada'
    ) RETURNING id_reserva INTO v_id_reserva;

    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa1 INTEGER;
    v_id_mesa2 INTEGER;
    v_id_reserva INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Ana Lucía Gómez' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Oakland Mall' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa1 FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 1 LIMIT 1;
    SELECT id_mesa INTO v_id_mesa2 FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 2 LIMIT 1;

    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
    ) VALUES (
        v_id_cliente, v_id_sucursal,
        CURRENT_DATE - INTERVAL '1 day 12:00:00',
        CURRENT_DATE - INTERVAL '1 day 14:00:00',
        3, 'atendida'
    ) RETURNING id_reserva INTO v_id_reserva;

    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa1);
    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa2);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa INTEGER;
    v_id_reserva INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Fernando Castillo' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Oakland Mall' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 5 LIMIT 1;

    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
    ) VALUES (
        v_id_cliente, v_id_sucursal,
        CURRENT_DATE + INTERVAL '2 day 19:00:00',
        CURRENT_DATE + INTERVAL '2 day 21:00:00',
        4, 'cancelada'
    ) RETURNING id_reserva INTO v_id_reserva;

    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa INTEGER;
    v_id_reserva INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Sofía Morales' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Ciudad Cayalá' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 3 LIMIT 1;

    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
    ) VALUES (
        v_id_cliente, v_id_sucursal,
        CURRENT_DATE + INTERVAL '1 day 14:00:00',
        CURRENT_DATE + INTERVAL '1 day 16:00:00',
        4, 'confirmada'
    ) RETURNING id_reserva INTO v_id_reserva;

    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa INTEGER;
    v_id_reserva INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Diego Herrera' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Ciudad Cayalá' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 5 LIMIT 1;

    INSERT INTO reserva (
        id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
    ) VALUES (
        v_id_cliente, v_id_sucursal,
        CURRENT_DATE - INTERVAL '1 day 13:00:00',
        CURRENT_DATE - INTERVAL '1 day 15:00:00',
        4, 'atendida'
    ) RETURNING id_reserva INTO v_id_reserva;

    INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (v_id_reserva, v_id_mesa);
END $$;

-- 4. VISITAS Y VENTAS DE EJEMPLO
DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_reserva INTEGER;
    v_id_mesa1 INTEGER;
    v_id_mesa2 INTEGER;
    v_id_visita INTEGER;
    v_id_venta1 INTEGER;
    v_id_venta2 INTEGER;
    v_plato_bowl INTEGER;
    v_plato_sprite INTEGER;
    v_plato_res INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Ana Lucía Gómez' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Oakland Mall' LIMIT 1;
    SELECT id_reserva INTO v_id_reserva FROM reserva WHERE id_cliente = v_id_cliente AND estado = 'atendida' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa1 FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 1 LIMIT 1;
    SELECT id_mesa INTO v_id_mesa2 FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 2 LIMIT 1;

    INSERT INTO visita (
        id_cliente, id_sucursal, id_reserva, fecha_hora_llegada, fecha_hora_salida, cantidad_personas, observaciones
    ) VALUES (
        v_id_cliente, v_id_sucursal, v_id_reserva,
        CURRENT_DATE - INTERVAL '1 day 12:05:00',
        CURRENT_DATE - INTERVAL '1 day 13:50:00',
        3, 'Visita completada con reserva.'
    ) RETURNING id_visita INTO v_id_visita;

    INSERT INTO visita_mesa (id_visita, id_mesa, fecha_hora_liberacion)
    VALUES 
        (v_id_visita, v_id_mesa1, CURRENT_DATE - INTERVAL '1 day 13:55:00'),
        (v_id_visita, v_id_mesa2, CURRENT_DATE - INTERVAL '1 day 13:55:00');

    INSERT INTO venta (id_visita, fecha_hora)
    VALUES (v_id_visita, CURRENT_DATE - INTERVAL '1 day 12:45:00')
    RETURNING id_venta INTO v_id_venta1;

    SELECT id_plato INTO v_plato_bowl FROM plato WHERE nombre = 'Bowl de pollo' LIMIT 1;
    SELECT id_plato INTO v_plato_sprite FROM plato WHERE nombre = 'Sprite en lata' LIMIT 1;

    INSERT INTO detalle_venta (id_venta, id_plato, cantidad, precio_unitario)
    VALUES 
        (v_id_venta1, v_plato_bowl, 2, 35.00),
        (v_id_venta1, v_plato_sprite, 2, 10.00);

    INSERT INTO venta (id_visita, fecha_hora)
    VALUES (v_id_visita, CURRENT_DATE - INTERVAL '1 day 13:30:00')
    RETURNING id_venta INTO v_id_venta2;

    SELECT id_plato INTO v_plato_res FROM plato WHERE nombre = 'Bowl de res' LIMIT 1;

    INSERT INTO detalle_venta (id_venta, id_plato, cantidad, precio_unitario)
    VALUES (v_id_venta2, v_plato_res, 1, 40.00);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_reserva INTEGER;
    v_id_mesa INTEGER;
    v_id_visita INTEGER;
    v_id_venta INTEGER;
    v_plato_wrap INTEGER;
    v_plato_coca INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Diego Herrera' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Ciudad Cayalá' LIMIT 1;
    SELECT id_reserva INTO v_id_reserva FROM reserva WHERE id_cliente = v_id_cliente AND estado = 'atendida' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 5 LIMIT 1;

    INSERT INTO visita (
        id_cliente, id_sucursal, id_reserva, fecha_hora_llegada, fecha_hora_salida, cantidad_personas, observaciones
    ) VALUES (
        v_id_cliente, v_id_sucursal, v_id_reserva,
        CURRENT_DATE - INTERVAL '1 day 13:10:00',
        CURRENT_DATE - INTERVAL '1 day 14:40:00',
        4, 'Almuerzo en terraza exterior.'
    ) RETURNING id_visita INTO v_id_visita;

    INSERT INTO visita_mesa (id_visita, id_mesa, fecha_hora_liberacion)
    VALUES (v_id_visita, v_id_mesa, CURRENT_DATE - INTERVAL '1 day 14:45:00');

    INSERT INTO venta (id_visita, fecha_hora)
    VALUES (v_id_visita, CURRENT_DATE - INTERVAL '1 day 13:50:00')
    RETURNING id_venta INTO v_id_venta;

    SELECT id_plato INTO v_plato_wrap FROM plato WHERE nombre = 'Wrap de res' LIMIT 1;
    SELECT id_plato INTO v_plato_coca FROM plato WHERE nombre = 'Coca-Cola en lata' LIMIT 1;

    INSERT INTO detalle_venta (id_venta, id_plato, cantidad, precio_unitario)
    VALUES 
        (v_id_venta, v_plato_wrap, 2, 35.00),
        (v_id_venta, v_plato_coca, 2, 10.00);
END $$;

DO $$
DECLARE
    v_id_cliente INTEGER;
    v_id_sucursal INTEGER;
    v_id_mesa INTEGER;
    v_id_visita INTEGER;
    v_id_venta INTEGER;
    v_plato_wrap_pollo INTEGER;
    v_plato_agua INTEGER;
BEGIN
    SELECT id_cliente INTO v_id_cliente FROM cliente WHERE nombre = 'Carlos Mendoza' LIMIT 1;
    SELECT id_sucursal INTO v_id_sucursal FROM sucursal WHERE nombre = 'Oakland Mall' LIMIT 1;
    SELECT id_mesa INTO v_id_mesa FROM mesa WHERE id_sucursal = v_id_sucursal AND numero = 4 LIMIT 1;

    INSERT INTO visita (
        id_cliente, id_sucursal, id_reserva, fecha_hora_llegada, fecha_hora_salida, cantidad_personas, observaciones
    ) VALUES (
        v_id_cliente, v_id_sucursal, NULL,
        CURRENT_DATE - INTERVAL '2 hours',
        CURRENT_DATE - INTERVAL '1 hour',
        2, 'Cliente espontáneo sin reserva.'
    ) RETURNING id_visita INTO v_id_visita;

    INSERT INTO visita_mesa (id_visita, id_mesa, fecha_hora_liberacion)
    VALUES (v_id_visita, v_id_mesa, CURRENT_DATE - INTERVAL '50 minutes');

    INSERT INTO venta (id_visita, fecha_hora)
    VALUES (v_id_visita, CURRENT_DATE - INTERVAL '1 hour 15 minutes')
    RETURNING id_venta INTO v_id_venta;

    SELECT id_plato INTO v_plato_wrap_pollo FROM plato WHERE nombre = 'Wrap de pollo' LIMIT 1;
    SELECT id_plato INTO v_plato_agua FROM plato WHERE nombre = 'Agua pura embotellada' LIMIT 1;

    INSERT INTO detalle_venta (id_venta, id_plato, cantidad, precio_unitario)
    VALUES 
        (v_id_venta, v_plato_wrap_pollo, 1, 30.00),
        (v_id_venta, v_plato_agua, 1, 8.00);
END $$;

COMMIT;
