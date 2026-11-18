BEGIN;

CREATE TABLE sucursal (
    id_sucursal INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL
);

CREATE TABLE cliente (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    telefono VARCHAR(20)
);

CREATE TABLE mesa (
    id_mesa INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_sucursal INTEGER NOT NULL,
    numero INTEGER NOT NULL CHECK (numero > 0),
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    zona VARCHAR(10) NOT NULL
        CHECK (zona IN ('interior', 'exterior')),

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal),

    UNIQUE (id_sucursal, numero)
);

CREATE TABLE reserva (
    id_reserva INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    id_sucursal INTEGER NOT NULL,
    fecha_hora_inicio TIMESTAMP NOT NULL,
    fecha_hora_fin_estimada TIMESTAMP NOT NULL,
    cantidad_personas INTEGER NOT NULL
        CHECK (cantidad_personas > 0),
    estado VARCHAR(15) NOT NULL DEFAULT 'confirmada'
        CHECK (
            estado IN (
                'confirmada',
                'cancelada',
                'atendida',
                'no_asistio'
            )
        ),

    FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente),

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal),

    CHECK (fecha_hora_fin_estimada > fecha_hora_inicio)
);

CREATE TABLE reserva_mesa (
    id_reserva INTEGER NOT NULL,
    id_mesa INTEGER NOT NULL,

    PRIMARY KEY (id_reserva, id_mesa),

    FOREIGN KEY (id_reserva)
        REFERENCES reserva (id_reserva),

    FOREIGN KEY (id_mesa)
        REFERENCES mesa (id_mesa)
);

CREATE TABLE visita (
    id_visita INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    id_sucursal INTEGER NOT NULL,
    id_reserva INTEGER UNIQUE,
    fecha_hora_llegada TIMESTAMP NOT NULL,
    fecha_hora_salida TIMESTAMP,
    cantidad_personas INTEGER NOT NULL
        CHECK (cantidad_personas > 0),
    observaciones TEXT,

    FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente),

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal),

    FOREIGN KEY (id_reserva)
        REFERENCES reserva (id_reserva),

    CHECK (
        fecha_hora_salida IS NULL
        OR fecha_hora_salida >= fecha_hora_llegada
    )
);

CREATE TABLE visita_mesa (
    id_visita INTEGER NOT NULL,
    id_mesa INTEGER NOT NULL,
    fecha_hora_liberacion TIMESTAMP,

    PRIMARY KEY (id_visita, id_mesa),

    FOREIGN KEY (id_visita)
        REFERENCES visita (id_visita),

    FOREIGN KEY (id_mesa)
        REFERENCES mesa (id_mesa)
);

CREATE UNIQUE INDEX uq_mesa_sin_liberar
ON visita_mesa (id_mesa)
WHERE fecha_hora_liberacion IS NULL;

CREATE TABLE plato (
    id_plato INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    precio NUMERIC(10,2) NOT NULL
        CHECK (precio > 0)
);

CREATE TABLE preferencia_cliente (
    id_cliente INTEGER NOT NULL,
    id_plato INTEGER NOT NULL,

    PRIMARY KEY (id_cliente, id_plato),

    FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente),

    FOREIGN KEY (id_plato)
        REFERENCES plato (id_plato)
);

CREATE TABLE insumo (
    id_insumo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    unidad_medida VARCHAR(10) NOT NULL
        CHECK (unidad_medida IN ('gramos', 'unidades')),
    existencia_minima NUMERIC(12,3) NOT NULL
        CHECK (existencia_minima >= 0)
);

CREATE TABLE receta (
    id_plato INTEGER NOT NULL,
    id_insumo INTEGER NOT NULL,
    cantidad NUMERIC(12,3) NOT NULL
        CHECK (cantidad > 0),

    PRIMARY KEY (id_plato, id_insumo),

    FOREIGN KEY (id_plato)
        REFERENCES plato (id_plato),

    FOREIGN KEY (id_insumo)
        REFERENCES insumo (id_insumo)
);

CREATE TABLE lote (
    id_lote INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_insumo INTEGER NOT NULL,
    id_sucursal INTEGER NOT NULL,
    fecha_recepcion DATE NOT NULL,
    fecha_caducidad DATE NOT NULL,
    cantidad_disponible NUMERIC(12,3) NOT NULL
        CHECK (cantidad_disponible >= 0),

    FOREIGN KEY (id_insumo)
        REFERENCES insumo (id_insumo),

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal),

    CHECK (fecha_caducidad >= fecha_recepcion)
);

CREATE TABLE venta (
    id_venta INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_visita INTEGER NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,

    FOREIGN KEY (id_visita)
        REFERENCES visita (id_visita)
);

CREATE TABLE detalle_venta (
    id_venta INTEGER NOT NULL,
    id_plato INTEGER NOT NULL,
    cantidad INTEGER NOT NULL
        CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL
        CHECK (precio_unitario > 0),

    PRIMARY KEY (id_venta, id_plato),

    FOREIGN KEY (id_venta)
        REFERENCES venta (id_venta),

    FOREIGN KEY (id_plato)
        REFERENCES plato (id_plato)
);

CREATE TABLE usuario (
    id_usuario INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena_hash TEXT NOT NULL,
    rol VARCHAR(15) NOT NULL
        CHECK (rol IN ('administrador', 'gerente', 'mesero')),
    id_sucursal INTEGER NOT NULL,

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal)
);

CREATE TABLE bitacora (
    id_bitacora INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INTEGER,
    tabla VARCHAR(63) NOT NULL,
    registro TEXT NOT NULL,
    operacion VARCHAR(6) NOT NULL
        CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
);

COMMIT;
