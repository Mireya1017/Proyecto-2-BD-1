-- ==============================================================================
-- Extensión Opcional: Tablas de Proveedores y Compras
-- Complemento para el requerimiento de compras e inventario coordinado (Pablo y Nathalie)
-- ==============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS proveedor (
    id_proveedor INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS compra (
    id_compra INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_proveedor INTEGER NOT NULL,
    id_sucursal INTEGER NOT NULL,
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (total >= 0),

    FOREIGN KEY (id_proveedor)
        REFERENCES proveedor (id_proveedor),

    FOREIGN KEY (id_sucursal)
        REFERENCES sucursal (id_sucursal)
);

CREATE TABLE IF NOT EXISTS detalle_compra (
    id_compra INTEGER NOT NULL,
    id_insumo INTEGER NOT NULL,
    cantidad NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0),

    PRIMARY KEY (id_compra, id_insumo),

    FOREIGN KEY (id_compra)
        REFERENCES compra (id_compra),

    FOREIGN KEY (id_insumo)
        REFERENCES insumo (id_insumo)
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_bitacora_proveedor') THEN
        CREATE TRIGGER trg_bitacora_proveedor
        AFTER INSERT OR UPDATE OR DELETE ON proveedor
        FOR EACH ROW
        EXECUTE FUNCTION fn_registrar_bitacora('id_proveedor');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_bitacora_compra') THEN
        CREATE TRIGGER trg_bitacora_compra
        AFTER INSERT OR UPDATE OR DELETE ON compra
        FOR EACH ROW
        EXECUTE FUNCTION fn_registrar_bitacora('id_compra');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_bitacora_detalle_compra') THEN
        CREATE TRIGGER trg_bitacora_detalle_compra
        AFTER INSERT OR UPDATE OR DELETE ON detalle_compra
        FOR EACH ROW
        EXECUTE FUNCTION fn_registrar_bitacora('id_compra', 'id_insumo');
    END IF;
END $$;

COMMIT;
