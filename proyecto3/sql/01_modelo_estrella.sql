-- Proyecto 3: reservas y aprovechamiento de mesas.
-- Ejecutar en la base restaurante_olap.
-- Crear la estructura una sola vez, en una base vacia.

BEGIN;

-- Sucursales: conserva los identificadores del Proyecto 2.
CREATE TABLE dim_sucursal (
    id_sucursal INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,

    CHECK (id_sucursal > 0)
);

-- Mesas: conserva sus identificadores y sucursal de origen.
CREATE TABLE dim_mesa (
    id_mesa INTEGER PRIMARY KEY,
    id_sucursal INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    capacidad INTEGER NOT NULL,
    zona VARCHAR(10) NOT NULL,

    FOREIGN KEY (id_sucursal)
        REFERENCES dim_sucursal (id_sucursal),

    UNIQUE (id_sucursal, numero),

    CHECK (id_mesa > 0),
    CHECK (numero > 0),
    CHECK (capacidad > 0),
    CHECK (zona IN ('interior', 'exterior'))
);

-- Calendario: permite agrupar por fecha, mes y dia.
CREATE TABLE dim_fecha (
    id_fecha INTEGER PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    nombre_mes VARCHAR(15) NOT NULL,
    dia_mes INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    nombre_dia VARCHAR(15) NOT NULL,

    CHECK (id_fecha = anio * 10000 + mes * 100 + dia_mes),
    CHECK (anio = EXTRACT(YEAR FROM fecha)),
    CHECK (mes = EXTRACT(MONTH FROM fecha)),
    CHECK (dia_mes = EXTRACT(DAY FROM fecha)),
    CHECK (dia_semana = EXTRACT(ISODOW FROM fecha))
);

-- Horas: cada fila representa un intervalo de una hora.
CREATE TABLE dim_hora (
    id_hora INTEGER PRIMARY KEY,
    etiqueta VARCHAR(5) NOT NULL UNIQUE,

    CHECK (id_hora BETWEEN 0 AND 23)
);

-- Una fila representa una reserva.
CREATE TABLE fact_reserva (
    id_reserva INTEGER PRIMARY KEY,
    id_sucursal INTEGER NOT NULL,
    id_fecha INTEGER NOT NULL,
    id_hora INTEGER NOT NULL,
    fecha_hora_inicio TIMESTAMP NOT NULL,
    fecha_hora_fin_estimada TIMESTAMP NOT NULL,
    cantidad_personas INTEGER NOT NULL,
    estado VARCHAR(15) NOT NULL,

    FOREIGN KEY (id_sucursal)
        REFERENCES dim_sucursal (id_sucursal),

    FOREIGN KEY (id_fecha)
        REFERENCES dim_fecha (id_fecha),

    FOREIGN KEY (id_hora)
        REFERENCES dim_hora (id_hora),

    CHECK (id_reserva > 0),
    CHECK (cantidad_personas > 0),

    CHECK (
        fecha_hora_fin_estimada > fecha_hora_inicio
    ),

    CHECK (
        estado IN (
            'confirmada',
            'atendida',
            'cancelada',
            'no_asistio'
        )
    ),

    CHECK (
        id_fecha =
        EXTRACT(YEAR FROM fecha_hora_inicio) * 10000
        + EXTRACT(MONTH FROM fecha_hora_inicio) * 100
        + EXTRACT(DAY FROM fecha_hora_inicio)
    ),

    CHECK (
        id_hora = EXTRACT(HOUR FROM fecha_hora_inicio)
    )
);

-- Una fila representa una visita, aunque utilice varias mesas.
CREATE TABLE fact_visita (
    id_visita INTEGER PRIMARY KEY,
    id_sucursal INTEGER NOT NULL,
    id_fecha INTEGER NOT NULL,
    id_hora INTEGER NOT NULL,
    id_reserva_origen INTEGER UNIQUE,
    fecha_hora_llegada TIMESTAMP NOT NULL,
    fecha_hora_salida TIMESTAMP NOT NULL,
    cantidad_personas INTEGER NOT NULL,
    capacidad_asignada INTEGER NOT NULL,

    FOREIGN KEY (id_sucursal)
        REFERENCES dim_sucursal (id_sucursal),

    FOREIGN KEY (id_fecha)
        REFERENCES dim_fecha (id_fecha),

    FOREIGN KEY (id_hora)
        REFERENCES dim_hora (id_hora),

    CHECK (id_visita > 0),
    CHECK (id_reserva_origen > 0),
    CHECK (cantidad_personas > 0),

    CHECK (
        capacidad_asignada >= cantidad_personas
    ),

    CHECK (
        fecha_hora_salida > fecha_hora_llegada
    ),

    CHECK (
        id_fecha =
        EXTRACT(YEAR FROM fecha_hora_llegada) * 10000
        + EXTRACT(MONTH FROM fecha_hora_llegada) * 100
        + EXTRACT(DAY FROM fecha_hora_llegada)
    ),

    CHECK (
        id_hora = EXTRACT(HOUR FROM fecha_hora_llegada)
    )
);

-- Una fila representa una mesa asignada a una visita.
CREATE TABLE fact_uso_mesa (
    id_visita_origen INTEGER NOT NULL,
    id_mesa INTEGER NOT NULL,
    id_sucursal INTEGER NOT NULL,
    id_fecha INTEGER NOT NULL,
    fecha_hora_llegada TIMESTAMP NOT NULL,
    fecha_hora_salida TIMESTAMP NOT NULL,
    fecha_hora_liberacion TIMESTAMP NOT NULL,

    PRIMARY KEY (id_visita_origen, id_mesa),

    FOREIGN KEY (id_mesa)
        REFERENCES dim_mesa (id_mesa),

    FOREIGN KEY (id_sucursal)
        REFERENCES dim_sucursal (id_sucursal),

    FOREIGN KEY (id_fecha)
        REFERENCES dim_fecha (id_fecha),

    CHECK (id_visita_origen > 0),

    CHECK (
        fecha_hora_salida > fecha_hora_llegada
    ),

    CHECK (
        fecha_hora_liberacion >= fecha_hora_salida
    ),

    CHECK (
        id_fecha =
        EXTRACT(YEAR FROM fecha_hora_llegada) * 10000
        + EXTRACT(MONTH FROM fecha_hora_llegada) * 100
        + EXTRACT(DAY FROM fecha_hora_llegada)
    )
);

-- Apoyan las consultas por sucursal, fecha y horario.
CREATE INDEX idx_reserva_sucursal_fecha_hora
ON fact_reserva (id_sucursal, id_fecha, id_hora);

CREATE INDEX idx_visita_sucursal_fecha_hora
ON fact_visita (id_sucursal, id_fecha, id_hora);

CREATE INDEX idx_uso_mesa_sucursal_fecha
ON fact_uso_mesa (id_sucursal, id_fecha);

-- Apoya las consultas del historial de cada mesa.
CREATE INDEX idx_uso_mesa_llegada
ON fact_uso_mesa (id_mesa, fecha_hora_llegada);

COMMIT;