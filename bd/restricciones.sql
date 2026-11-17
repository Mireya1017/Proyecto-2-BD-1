BEGIN;

ALTER TABLE reserva
    ADD CONSTRAINT uq_reserva_cliente_sucursal
    UNIQUE (
        id_reserva,
        id_cliente,
        id_sucursal
    );

ALTER TABLE visita
    ADD CONSTRAINT fk_visita_reserva_cliente_sucursal
    FOREIGN KEY (
        id_reserva,
        id_cliente,
        id_sucursal
    )
    REFERENCES reserva (
        id_reserva,
        id_cliente,
        id_sucursal
    );

CREATE OR REPLACE FUNCTION fn_validar_sucursal_mesa()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_sucursal_operacion INTEGER;
    v_id_sucursal_mesa INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'reserva_mesa' THEN
        SELECT id_sucursal
        INTO STRICT v_id_sucursal_operacion
        FROM reserva
        WHERE id_reserva = NEW.id_reserva
        FOR SHARE;

    ELSIF TG_TABLE_NAME = 'visita_mesa' THEN
        SELECT id_sucursal
        INTO STRICT v_id_sucursal_operacion
        FROM visita
        WHERE id_visita = NEW.id_visita
        FOR SHARE;
    END IF;

    SELECT id_sucursal
    INTO STRICT v_id_sucursal_mesa
    FROM mesa
    WHERE id_mesa = NEW.id_mesa
    FOR SHARE;

    IF v_id_sucursal_operacion <> v_id_sucursal_mesa THEN
        RAISE EXCEPTION
            'La mesa debe pertenecer a la misma sucursal que la reserva o visita';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_sucursal_reserva_mesa
BEFORE INSERT OR UPDATE ON reserva_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_validar_sucursal_mesa();

CREATE TRIGGER trg_validar_sucursal_visita_mesa
BEFORE INSERT OR UPDATE ON visita_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_validar_sucursal_mesa();

CREATE OR REPLACE FUNCTION fn_proteger_cambio_sucursal()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_hay_conflicto BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'reserva' THEN
        SELECT EXISTS (
            SELECT 1
            FROM reserva_mesa AS rm
            JOIN mesa AS m
                ON m.id_mesa = rm.id_mesa
            WHERE rm.id_reserva = NEW.id_reserva
              AND m.id_sucursal <> NEW.id_sucursal
        )
        INTO v_hay_conflicto;

    ELSIF TG_TABLE_NAME = 'visita' THEN
        SELECT EXISTS (
            SELECT 1
            FROM visita_mesa AS vm
            JOIN mesa AS m
                ON m.id_mesa = vm.id_mesa
            WHERE vm.id_visita = NEW.id_visita
              AND m.id_sucursal <> NEW.id_sucursal
        )
        INTO v_hay_conflicto;

    ELSIF TG_TABLE_NAME = 'mesa' THEN
        SELECT
            EXISTS (
                SELECT 1
                FROM reserva_mesa AS rm
                JOIN reserva AS r
                    ON r.id_reserva = rm.id_reserva
                WHERE rm.id_mesa = NEW.id_mesa
                  AND r.id_sucursal <> NEW.id_sucursal
            )
            OR EXISTS (
                SELECT 1
                FROM visita_mesa AS vm
                JOIN visita AS v
                    ON v.id_visita = vm.id_visita
                WHERE vm.id_mesa = NEW.id_mesa
                  AND v.id_sucursal <> NEW.id_sucursal
            )
        INTO v_hay_conflicto;
    END IF;

    IF v_hay_conflicto THEN
        RAISE EXCEPTION
            'No se puede cambiar la sucursal: existen asignaciones de mesas incompatibles';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_proteger_sucursal_reserva
BEFORE UPDATE OF id_sucursal ON reserva
FOR EACH ROW
WHEN (OLD.id_sucursal IS DISTINCT FROM NEW.id_sucursal)
EXECUTE FUNCTION fn_proteger_cambio_sucursal();

CREATE TRIGGER trg_proteger_sucursal_visita
BEFORE UPDATE OF id_sucursal ON visita
FOR EACH ROW
WHEN (OLD.id_sucursal IS DISTINCT FROM NEW.id_sucursal)
EXECUTE FUNCTION fn_proteger_cambio_sucursal();

CREATE TRIGGER trg_proteger_sucursal_mesa
BEFORE UPDATE OF id_sucursal ON mesa
FOR EACH ROW
WHEN (OLD.id_sucursal IS DISTINCT FROM NEW.id_sucursal)
EXECUTE FUNCTION fn_proteger_cambio_sucursal();

CREATE OR REPLACE FUNCTION fn_validar_zona_mesas()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_zona TEXT;
    v_id_mesa_anterior INTEGER;
    v_hay_conflicto BOOLEAN;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        v_id_mesa_anterior := OLD.id_mesa;
    END IF;

    -- Bloqueamos la reserva o visita para coordinar
    -- asignaciones simultáneas al mismo grupo.
    IF TG_TABLE_NAME = 'reserva_mesa' THEN
        PERFORM id_reserva
        FROM reserva
        WHERE id_reserva = NEW.id_reserva
        FOR UPDATE;
    ELSE
        PERFORM id_visita
        FROM visita
        WHERE id_visita = NEW.id_visita
        FOR UPDATE;
    END IF;

    SELECT zona INTO STRICT v_zona
    FROM mesa
    WHERE id_mesa = NEW.id_mesa
    FOR SHARE;

    IF TG_TABLE_NAME = 'reserva_mesa' THEN
        SELECT EXISTS (
            SELECT 1
            FROM reserva_mesa AS rm
            JOIN mesa AS m
                ON m.id_mesa = rm.id_mesa
            WHERE rm.id_reserva = NEW.id_reserva
              AND m.zona <> v_zona
              AND (
                  v_id_mesa_anterior IS NULL
                  OR rm.id_mesa <> v_id_mesa_anterior
              )
        )
        INTO v_hay_conflicto;

    ELSE
        SELECT EXISTS (
            SELECT 1
            FROM visita_mesa AS vm
            JOIN mesa AS m
                ON m.id_mesa = vm.id_mesa
            WHERE vm.id_visita = NEW.id_visita
              AND m.zona <> v_zona
              AND (
                  v_id_mesa_anterior IS NULL
                  OR vm.id_mesa <> v_id_mesa_anterior
              )
        )
        INTO v_hay_conflicto;
    END IF;

    IF v_hay_conflicto THEN
        RAISE EXCEPTION
            'Las mesas de una reserva o visita deben ser de la misma zona';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_asegurar_zona_reserva_mesa
BEFORE INSERT OR UPDATE ON reserva_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_validar_zona_mesas();

CREATE TRIGGER trg_asegurar_zona_visita_mesa
BEFORE INSERT OR UPDATE ON visita_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_validar_zona_mesas();

CREATE OR REPLACE FUNCTION fn_proteger_cambio_zona()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_hay_conflicto BOOLEAN;
BEGIN
    -- Coordinamos el cambio con las asignaciones del grupo.
    PERFORM r.id_reserva
    FROM reserva AS r
    WHERE EXISTS (
        SELECT 1
        FROM reserva_mesa AS rm
        WHERE rm.id_reserva = r.id_reserva
          AND rm.id_mesa = NEW.id_mesa
    )
    ORDER BY r.id_reserva
    FOR UPDATE;

    PERFORM v.id_visita
    FROM visita AS v
    WHERE EXISTS (
        SELECT 1
        FROM visita_mesa AS vm
        WHERE vm.id_visita = v.id_visita
          AND vm.id_mesa = NEW.id_mesa
    )
    ORDER BY v.id_visita
    FOR UPDATE;

    SELECT
        EXISTS (
            SELECT 1
            FROM reserva_mesa AS asignada
            JOIN reserva_mesa AS otra
                ON otra.id_reserva = asignada.id_reserva
            JOIN mesa AS m
                ON m.id_mesa = otra.id_mesa
            WHERE asignada.id_mesa = NEW.id_mesa
              AND otra.id_mesa <> NEW.id_mesa
              AND m.zona <> NEW.zona
        )
        OR EXISTS (
            SELECT 1
            FROM visita_mesa AS asignada
            JOIN visita_mesa AS otra
                ON otra.id_visita = asignada.id_visita
            JOIN mesa AS m
                ON m.id_mesa = otra.id_mesa
            WHERE asignada.id_mesa = NEW.id_mesa
              AND otra.id_mesa <> NEW.id_mesa
              AND m.zona <> NEW.zona
        )
    INTO v_hay_conflicto;

    IF v_hay_conflicto THEN
        RAISE EXCEPTION
            'No se puede cambiar la zona: dejaría mesas de distintas zonas en una reserva o visita';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_proteger_zona_mesa
BEFORE UPDATE OF zona ON mesa
FOR EACH ROW
WHEN (OLD.zona IS DISTINCT FROM NEW.zona)
EXECUTE FUNCTION fn_proteger_cambio_zona();

CREATE OR REPLACE FUNCTION fn_validar_liberacion_mesa()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_fecha_salida TIMESTAMP;
BEGIN
    SELECT fecha_hora_salida
    INTO STRICT v_fecha_salida
    FROM visita
    WHERE id_visita = NEW.id_visita
    FOR UPDATE;

    IF NEW.fecha_hora_liberacion IS NOT NULL THEN

        IF v_fecha_salida IS NULL THEN
            RAISE EXCEPTION
                'Debe registrar la salida de la visita antes de liberar la mesa';
        END IF;

        IF NEW.fecha_hora_liberacion < v_fecha_salida THEN
            RAISE EXCEPTION
                'La liberación de la mesa no puede ser anterior a la salida de la visita';
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_liberacion_mesa
BEFORE INSERT OR UPDATE ON visita_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_validar_liberacion_mesa();

CREATE OR REPLACE FUNCTION fn_validar_salida_visita()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_hay_conflicto BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM visita_mesa AS vm
        WHERE vm.id_visita = NEW.id_visita
          AND vm.fecha_hora_liberacion IS NOT NULL
          AND (
              NEW.fecha_hora_salida IS NULL
              OR vm.fecha_hora_liberacion < NEW.fecha_hora_salida
          )
    )
    INTO v_hay_conflicto;

    IF v_hay_conflicto THEN
        RAISE EXCEPTION
            'La salida indicada contradice la liberación de una mesa de esta visita';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_salida_visita
BEFORE UPDATE OF fecha_hora_salida ON visita
FOR EACH ROW
WHEN (
    OLD.fecha_hora_salida
    IS DISTINCT FROM
    NEW.fecha_hora_salida
)
EXECUTE FUNCTION fn_validar_salida_visita();

CREATE OR REPLACE FUNCTION fn_comprobar_capacidad_reserva(
    p_id_reserva INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_personas INTEGER;
    v_capacidad BIGINT;
BEGIN
    SELECT cantidad_personas
    INTO v_personas
    FROM reserva
    WHERE id_reserva = p_id_reserva;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    SELECT COALESCE(SUM(m.capacidad), 0)
    INTO v_capacidad
    FROM reserva_mesa AS rm
    JOIN mesa AS m
        ON m.id_mesa = rm.id_mesa
    WHERE rm.id_reserva = p_id_reserva;

    IF v_capacidad < v_personas THEN
        RAISE EXCEPTION
            'Reserva %: las mesas admiten % personas y se necesitan %',
            p_id_reserva,
            v_capacidad,
            v_personas;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_capacidad_reserva()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_reserva INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'reserva' THEN
        PERFORM fn_comprobar_capacidad_reserva(
            NEW.id_reserva
        );

    ELSIF TG_TABLE_NAME = 'reserva_mesa' THEN

        IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
            PERFORM fn_comprobar_capacidad_reserva(
                OLD.id_reserva
            );
        END IF;

        IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
            PERFORM fn_comprobar_capacidad_reserva(
                NEW.id_reserva
            );
        END IF;

    ELSIF TG_TABLE_NAME = 'mesa' THEN

        FOR v_id_reserva IN
            SELECT id_reserva
            FROM reserva_mesa
            WHERE id_mesa = NEW.id_mesa
        LOOP
            PERFORM fn_comprobar_capacidad_reserva(
                v_id_reserva
            );
        END LOOP;

    END IF;

    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION fn_bloquear_reservas_capacidad()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_reserva_anterior INTEGER;
    v_id_reserva_nueva INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'reserva_mesa' THEN

        IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
            v_id_reserva_anterior := OLD.id_reserva;
        END IF;

        IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
            v_id_reserva_nueva := NEW.id_reserva;
        END IF;

        PERFORM id_reserva
        FROM reserva
        WHERE id_reserva = v_id_reserva_anterior
           OR id_reserva = v_id_reserva_nueva
        ORDER BY id_reserva
        FOR UPDATE;

    ELSIF TG_TABLE_NAME = 'mesa' THEN

        PERFORM r.id_reserva
        FROM reserva AS r
        JOIN reserva_mesa AS rm
            ON rm.id_reserva = r.id_reserva
        WHERE rm.id_mesa = NEW.id_mesa
        ORDER BY r.id_reserva
        FOR UPDATE OF r;

    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_asegurar_capacidad_reserva_mesa
BEFORE INSERT OR UPDATE OR DELETE ON reserva_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_reservas_capacidad();

CREATE TRIGGER trg_bloquear_capacidad_mesa_reservas
BEFORE UPDATE OF capacidad ON mesa
FOR EACH ROW
WHEN (OLD.capacidad IS DISTINCT FROM NEW.capacidad)
EXECUTE FUNCTION fn_bloquear_reservas_capacidad();

CREATE CONSTRAINT TRIGGER trg_capacidad_reserva
AFTER INSERT OR UPDATE ON reserva
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_capacidad_reserva();

CREATE CONSTRAINT TRIGGER trg_capacidad_reserva_asignaciones
AFTER INSERT OR UPDATE OR DELETE ON reserva_mesa
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_capacidad_reserva();

CREATE CONSTRAINT TRIGGER trg_capacidad_reserva_cambio_mesa
AFTER UPDATE ON mesa
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
WHEN (OLD.capacidad IS DISTINCT FROM NEW.capacidad)
EXECUTE FUNCTION fn_validar_capacidad_reserva();

CREATE OR REPLACE FUNCTION fn_comprobar_capacidad_visita(
    p_id_visita INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_personas INTEGER;
    v_capacidad BIGINT;
BEGIN
    SELECT cantidad_personas
    INTO v_personas
    FROM visita
    WHERE id_visita = p_id_visita;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    SELECT COALESCE(SUM(m.capacidad), 0)
    INTO v_capacidad
    FROM visita_mesa AS vm
    JOIN mesa AS m
        ON m.id_mesa = vm.id_mesa
    WHERE vm.id_visita = p_id_visita;

    IF v_capacidad < v_personas THEN
        RAISE EXCEPTION
            'Visita %: las mesas admiten % personas y se necesitan %',
            p_id_visita,
            v_capacidad,
            v_personas;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validar_capacidad_visita()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_visita INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'visita' THEN
        PERFORM fn_comprobar_capacidad_visita(
            NEW.id_visita
        );

    ELSIF TG_TABLE_NAME = 'visita_mesa' THEN

        IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
            PERFORM fn_comprobar_capacidad_visita(
                OLD.id_visita
            );
        END IF;

        IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
            PERFORM fn_comprobar_capacidad_visita(
                NEW.id_visita
            );
        END IF;

    ELSIF TG_TABLE_NAME = 'mesa' THEN

        FOR v_id_visita IN
            SELECT id_visita
            FROM visita_mesa
            WHERE id_mesa = NEW.id_mesa
        LOOP
            PERFORM fn_comprobar_capacidad_visita(
                v_id_visita
            );
        END LOOP;

    END IF;

    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION fn_bloquear_visitas_capacidad()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_visita_anterior INTEGER;
    v_id_visita_nueva INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'visita_mesa' THEN

        IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
            v_id_visita_anterior := OLD.id_visita;
        END IF;

        IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
            v_id_visita_nueva := NEW.id_visita;
        END IF;

        PERFORM id_visita
        FROM visita
        WHERE id_visita = v_id_visita_anterior
           OR id_visita = v_id_visita_nueva
        ORDER BY id_visita
        FOR UPDATE;

    ELSIF TG_TABLE_NAME = 'mesa' THEN

        PERFORM v.id_visita
        FROM visita AS v
        JOIN visita_mesa AS vm
            ON vm.id_visita = v.id_visita
        WHERE vm.id_mesa = NEW.id_mesa
        ORDER BY v.id_visita
        FOR UPDATE OF v;

    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_asegurar_capacidad_visita_mesa
BEFORE INSERT OR UPDATE OR DELETE ON visita_mesa
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_visitas_capacidad();

CREATE TRIGGER trg_bloquear_capacidad_mesa_visitas
BEFORE UPDATE OF capacidad ON mesa
FOR EACH ROW
WHEN (OLD.capacidad IS DISTINCT FROM NEW.capacidad)
EXECUTE FUNCTION fn_bloquear_visitas_capacidad();

CREATE CONSTRAINT TRIGGER trg_capacidad_visita
AFTER INSERT OR UPDATE ON visita
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_capacidad_visita();

CREATE CONSTRAINT TRIGGER trg_capacidad_visita_asignaciones
AFTER INSERT OR UPDATE OR DELETE ON visita_mesa
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_capacidad_visita();

CREATE CONSTRAINT TRIGGER trg_capacidad_visita_cambio_mesa
AFTER UPDATE ON mesa
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
WHEN (OLD.capacidad IS DISTINCT FROM NEW.capacidad)
EXECUTE FUNCTION fn_validar_capacidad_visita();

CREATE OR REPLACE FUNCTION fn_bloquear_cambios_reservas()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Número fijo que identifica este bloqueo.
    -- Se libera automáticamente al terminar la transacción.
    PERFORM pg_advisory_xact_lock(308802);

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_bloquear_cambios_reserva
BEFORE INSERT OR UPDATE OR DELETE ON reserva
FOR EACH STATEMENT
EXECUTE FUNCTION fn_bloquear_cambios_reservas();

CREATE TRIGGER trg_bloquear_cambios_reserva_mesa
BEFORE INSERT OR UPDATE OR DELETE ON reserva_mesa
FOR EACH STATEMENT
EXECUTE FUNCTION fn_bloquear_cambios_reservas();

CREATE OR REPLACE FUNCTION fn_validar_horario_reserva()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_mesa INTEGER;
BEGIN
    SELECT rm.id_mesa
    INTO v_id_mesa
    FROM reserva AS r
    JOIN reserva_mesa AS rm
        ON rm.id_reserva = r.id_reserva
    JOIN reserva_mesa AS otra_mesa
        ON otra_mesa.id_mesa = rm.id_mesa
        AND otra_mesa.id_reserva <> r.id_reserva
    JOIN reserva AS otra_reserva
        ON otra_reserva.id_reserva = otra_mesa.id_reserva
    WHERE r.id_reserva = NEW.id_reserva
      AND r.estado IN ('confirmada', 'atendida')
      AND otra_reserva.estado IN ('confirmada', 'atendida')
      AND r.fecha_hora_inicio
          < otra_reserva.fecha_hora_fin_estimada
      AND otra_reserva.fecha_hora_inicio
          < r.fecha_hora_fin_estimada
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'La mesa con ID % ya tiene una reserva en ese horario',
            v_id_mesa;
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_horario_reserva
AFTER INSERT OR UPDATE ON reserva
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_horario_reserva();

CREATE CONSTRAINT TRIGGER trg_horario_reserva_mesa
AFTER INSERT OR UPDATE ON reserva_mesa
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION fn_validar_horario_reserva();

COMMIT;
