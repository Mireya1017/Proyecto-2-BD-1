-- datos_iniciales.sql
-- Carga inicial de sucursales, mesas, menú, insumos, recetas y lotes; incluye bebidas.
-- Orden de ejecución: 5 de 5. Ejecutar una vez en una base vacía.

BEGIN;

INSERT INTO sucursal (nombre, direccion)
VALUES
    ('Oakland Mall', 'Centro comercial Oakland Mall, Ciudad de Guatemala'),
    ('Ciudad Cayalá', 'Ciudad Cayalá, Ciudad de Guatemala');

INSERT INTO mesa (id_sucursal, numero, capacidad, zona)
SELECT
    s.id_sucursal,
    m.numero,
    m.capacidad,
    m.zona
FROM sucursal AS s
CROSS JOIN (
    VALUES
        (1, 2, 'interior'),
        (2, 2, 'interior'),
        (3, 4, 'interior'),
        (4, 4, 'interior'),
        (5, 4, 'exterior'),
        (6, 6, 'exterior')
) AS m(numero, capacidad, zona)
WHERE s.nombre IN ('Oakland Mall', 'Ciudad Cayalá');

INSERT INTO plato (nombre, precio)
VALUES
    ('Bowl de pollo', 35.00),
    ('Bowl de res', 40.00),
    ('Wrap de pollo', 30.00),
    ('Wrap de res', 35.00);

INSERT INTO insumo (nombre, unidad_medida, existencia_minima)
VALUES
    ('Pollo', 'gramos', 2000),
    ('Carne de res', 'gramos', 2000),
    ('Arroz', 'gramos', 2000),
    ('Frijoles', 'gramos', 1000),
    ('Lechuga', 'gramos', 500),
    ('Tortilla para wrap', 'unidades', 20);

INSERT INTO receta (id_plato, id_insumo, cantidad)
SELECT
    p.id_plato,
    i.id_insumo,
    r.cantidad
FROM (
    VALUES
        ('Bowl de pollo', 'Pollo', 150),
        ('Bowl de pollo', 'Arroz', 100),
        ('Bowl de pollo', 'Frijoles', 80),
        ('Bowl de pollo', 'Lechuga', 30),

        ('Bowl de res', 'Carne de res', 150),
        ('Bowl de res', 'Arroz', 100),
        ('Bowl de res', 'Frijoles', 80),
        ('Bowl de res', 'Lechuga', 30),

        ('Wrap de pollo', 'Pollo', 100),
        ('Wrap de pollo', 'Arroz', 60),
        ('Wrap de pollo', 'Frijoles', 40),
        ('Wrap de pollo', 'Lechuga', 20),
        ('Wrap de pollo', 'Tortilla para wrap', 1),

        ('Wrap de res', 'Carne de res', 100),
        ('Wrap de res', 'Arroz', 60),
        ('Wrap de res', 'Frijoles', 40),
        ('Wrap de res', 'Lechuga', 20),
        ('Wrap de res', 'Tortilla para wrap', 1)
) AS r(plato, insumo, cantidad)
JOIN plato AS p
    ON p.nombre = r.plato
JOIN insumo AS i
    ON i.nombre = r.insumo;

INSERT INTO lote (
    id_insumo,
    id_sucursal,
    fecha_recepcion,
    fecha_caducidad,
    cantidad_disponible
)
SELECT
    i.id_insumo,
    s.id_sucursal,
    CURRENT_DATE,
    CURRENT_DATE + d.dias_caducidad,
    d.cantidad
FROM (
    VALUES
        ('Pollo', 5000, 5),
        ('Carne de res', 5000, 5),
        ('Arroz', 10000, 90),
        ('Frijoles', 8000, 60),
        ('Lechuga', 2000, 4),
        ('Tortilla para wrap', 100, 10)
) AS d(nombre_insumo, cantidad, dias_caducidad)
JOIN insumo AS i
    ON i.nombre = d.nombre_insumo
CROSS JOIN sucursal AS s
WHERE s.nombre IN ('Oakland Mall', 'Ciudad Cayalá');

INSERT INTO plato (nombre, precio)
VALUES
    ('Sprite en lata', 10.00),
    ('Coca-Cola en lata', 10.00),
    ('Agua pura embotellada', 8.00);

INSERT INTO insumo (
    nombre,
    unidad_medida,
    existencia_minima
)
VALUES
    ('Sprite en lata', 'unidades', 12),
    ('Coca-Cola en lata', 'unidades', 12),
    ('Agua pura embotellada', 'unidades', 12);

INSERT INTO receta (id_plato, id_insumo, cantidad)
SELECT
    p.id_plato,
    i.id_insumo,
    1
FROM plato AS p
JOIN insumo AS i
    ON i.nombre = p.nombre
WHERE p.nombre IN (
    'Sprite en lata',
    'Coca-Cola en lata',
    'Agua pura embotellada'
);

INSERT INTO lote (
    id_insumo,
    id_sucursal,
    fecha_recepcion,
    fecha_caducidad,
    cantidad_disponible
)
SELECT
    i.id_insumo,
    s.id_sucursal,
    CURRENT_DATE,
    CURRENT_DATE + 180,
    48
FROM insumo AS i
CROSS JOIN sucursal AS s
WHERE i.nombre IN (
    'Sprite en lata',
    'Coca-Cola en lata',
    'Agua pura embotellada'
)
AND s.nombre IN (
    'Oakland Mall',
    'Ciudad Cayalá'
)
AND NOT EXISTS (
    SELECT 1
    FROM lote AS l
    WHERE l.id_insumo = i.id_insumo
      AND l.id_sucursal = s.id_sucursal
);

COMMIT;
