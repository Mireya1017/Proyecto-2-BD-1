BEGIN;

CREATE OR REPLACE FUNCTION fn_registrar_bitacora()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_datos JSONB;
    v_registro JSONB := '{}'::JSONB;
    v_campo TEXT;
    v_id_usuario INTEGER;
BEGIN
    -- En una eliminación tomamos el registro anterior.
    IF TG_OP = 'DELETE' THEN
        v_datos := to_jsonb(OLD);
    ELSE
        v_datos := to_jsonb(NEW);
    END IF;

    -- Recogemos los campos que forman la PK.
    FOREACH v_campo IN ARRAY TG_ARGV
    LOOP
        v_registro := v_registro || jsonb_build_object(
            v_campo,
            v_datos -> v_campo
        );
    END LOOP;
    v_id_usuario := NULLIF(
        current_setting('app.id_usuario', true),
        ''
    )::INTEGER;

    INSERT INTO bitacora (
        id_usuario,
        tabla,
        registro,
        operacion
    )
    VALUES (
        v_id_usuario,
        TG_TABLE_NAME,
        v_registro::TEXT,
        TG_OP
    );
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_bitacora_sucursal
AFTER INSERT OR UPDATE OR DELETE ON sucursal
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_sucursal');

CREATE TRIGGER trg_bitacora_cliente
AFTER INSERT OR UPDATE OR DELETE ON cliente
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_cliente');

CREATE TRIGGER trg_bitacora_mesa
AFTER INSERT OR UPDATE OR DELETE ON mesa
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_mesa');

CREATE TRIGGER trg_bitacora_reserva
AFTER INSERT OR UPDATE OR DELETE ON reserva
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_reserva');

CREATE TRIGGER trg_bitacora_reserva_mesa
AFTER INSERT OR UPDATE OR DELETE ON reserva_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora(
    'id_reserva', 'id_mesa'
);

CREATE TRIGGER trg_bitacora_visita
AFTER INSERT OR UPDATE OR DELETE ON visita
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_visita');

CREATE TRIGGER trg_bitacora_visita_mesa
AFTER INSERT OR UPDATE OR DELETE ON visita_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora(
    'id_visita', 'id_mesa'
);

CREATE TRIGGER trg_bitacora_plato
AFTER INSERT OR UPDATE OR DELETE ON plato
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_plato');

CREATE TRIGGER trg_bitacora_preferencia_cliente
AFTER INSERT OR UPDATE OR DELETE ON preferencia_cliente
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora(
    'id_cliente', 'id_plato'
);

CREATE TRIGGER trg_bitacora_insumo
AFTER INSERT OR UPDATE OR DELETE ON insumo
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_insumo');

CREATE TRIGGER trg_bitacora_receta
AFTER INSERT OR UPDATE OR DELETE ON receta
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora(
    'id_plato', 'id_insumo'
);

CREATE TRIGGER trg_bitacora_lote
AFTER INSERT OR UPDATE OR DELETE ON lote
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_lote');

CREATE TRIGGER trg_bitacora_venta
AFTER INSERT OR UPDATE OR DELETE ON venta
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_venta');

CREATE TRIGGER trg_bitacora_detalle_venta
AFTER INSERT OR UPDATE OR DELETE ON detalle_venta
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora(
    'id_venta', 'id_plato'
);

CREATE TRIGGER trg_bitacora_usuario
AFTER INSERT OR UPDATE OR DELETE ON usuario
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_bitacora('id_usuario');

COMMIT;
