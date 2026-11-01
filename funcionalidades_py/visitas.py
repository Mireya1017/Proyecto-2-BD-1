# -----------------------------------------------------------
# Registra visitas, salidas y mesas liberadas
# -----------------------------------------------------------

def registrar_visita(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para registrar visitas.")

    v_id_cliente = p_datos["id_cliente"]
    v_id_sucursal = p_datos["id_sucursal"]
    v_personas = p_datos["cantidad_personas"]
    v_id_reserva = p_datos.get("id_reserva")
    v_mesas = p_datos.get("mesas", [])
    v_observaciones = p_datos.get("observaciones")

    if v_personas <= 0:
        raise ValueError("La cantidad de personas debe ser mayor que cero.")

    if not v_mesas:
        raise ValueError("Debe seleccionar al menos una mesa.")

    if len(v_mesas) != len(set(v_mesas)):
        raise ValueError("No debe seleccionar la misma mesa dos veces.")

    if p_sesion["rol"] != "administrador":
        if v_id_sucursal != p_sesion["id_sucursal"]:
            raise PermissionError(
                "No puede registrar visitas de otra sucursal."
            )

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(
            "SELECT id_cliente FROM cliente WHERE id_cliente = %s;",
            (v_id_cliente,)
        )

        if v_cursor.fetchone() is None:
            raise ValueError("El cliente no existe.")

        # Si llega con reserva, comprobar sus datos.
        if v_id_reserva is not None:
            v_cursor.execute(
                """
                SELECT id_cliente, id_sucursal, estado
                FROM reserva
                WHERE id_reserva = %s;
                """,
                (v_id_reserva,)
            )

            v_reserva = v_cursor.fetchone()

            if v_reserva is None:
                raise ValueError("La reserva no existe.")

            if v_reserva[0] != v_id_cliente:
                raise ValueError("La reserva pertenece a otro cliente.")

            if v_reserva[1] != v_id_sucursal:
                raise ValueError("La reserva pertenece a otra sucursal.")

            if v_reserva[2] != "confirmada":
                raise ValueError("La reserva debe estar confirmada.")

        # Obtener las mesas seleccionadas.
        v_cursor.execute(
            """
            SELECT id_mesa, id_sucursal, capacidad, zona
            FROM mesa
            WHERE id_mesa = ANY(%s);
            """,
            (v_mesas,)
        )

        v_datos_mesas = v_cursor.fetchall()

        if len(v_datos_mesas) != len(v_mesas):
            raise ValueError("Una o más mesas no existen.")

        v_capacidad = 0
        v_zonas = set()

        for v_mesa in v_datos_mesas:
            if v_mesa[1] != v_id_sucursal:
                raise ValueError(
                    "Todas las mesas deben pertenecer a la sucursal."
                )

            v_capacidad += v_mesa[2]
            v_zonas.add(v_mesa[3])

        if len(v_zonas) > 1:
            raise ValueError(
                "Las mesas deben pertenecer a la misma zona."
            )

        if v_capacidad < v_personas:
            raise ValueError(
                "Las mesas no tienen capacidad suficiente."
            )

        # Una mesa sigue ocupada hasta que se registra su liberación.
        v_cursor.execute(
            """
            SELECT id_mesa
            FROM visita_mesa
            WHERE id_mesa = ANY(%s)
              AND fecha_hora_liberacion IS NULL;
            """,
            (v_mesas,)
        )

        if v_cursor.fetchone() is not None:
            raise ValueError(
                "Una de las mesas está ocupada o pendiente de limpieza."
            )

        # Comprobar reservas que están vigentes en este momento.
        # La reserva de esta misma llegada se excluye.
        v_cursor.execute(
            """
            SELECT r.id_reserva
            FROM reserva r
            INNER JOIN reserva_mesa rm
                ON rm.id_reserva = r.id_reserva
            WHERE rm.id_mesa = ANY(%s)
              AND r.estado IN ('confirmada', 'atendida')
              AND r.fecha_hora_inicio <= CURRENT_TIMESTAMP
              AND r.fecha_hora_fin_estimada > CURRENT_TIMESTAMP
              AND (%s::INTEGER IS NULL OR r.id_reserva <> %s);
            """,
            (v_mesas, v_id_reserva, v_id_reserva)
        )

        if v_cursor.fetchone() is not None:
            raise ValueError(
                "Una de las mesas está reservada para otro grupo "
                "en este horario."
            )

        # Registrar la llegada.
        v_cursor.execute(
            """
            INSERT INTO visita (
                id_cliente,
                id_sucursal,
                id_reserva,
                fecha_hora_llegada,
                cantidad_personas,
                observaciones
            )
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            RETURNING id_visita;
            """,
            (
                v_id_cliente,
                v_id_sucursal,
                v_id_reserva,
                v_personas,
                v_observaciones
            )
        )

        v_id_visita = v_cursor.fetchone()[0]

        # Asociar todas las mesas a la visita.
        for v_id_mesa in v_mesas:
            v_cursor.execute(
                """
                INSERT INTO visita_mesa (id_visita, id_mesa)
                VALUES (%s, %s);
                """,
                (v_id_visita, v_id_mesa)
            )

        if v_id_reserva is not None:
            v_cursor.execute(
                """
                UPDATE reserva
                SET estado = 'atendida'
                WHERE id_reserva = %s;
                """,
                (v_id_reserva,)
            )

    return v_id_visita


def registrar_salida(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para registrar salidas.")

    id_visita = p_datos["id_visita"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_sucursal, fecha_hora_salida
            FROM visita
            WHERE id_visita = %s
            FOR UPDATE;
            """,
            (id_visita,)
        )

        visita = cursor.fetchone()

        if visita is None:
            raise ValueError("La visita no existe.")

        id_sucursal = visita[0]
        fecha_salida = visita[1]

        if p_sesion["rol"] != "administrador":
            if id_sucursal != p_sesion["id_sucursal"]:
                raise PermissionError(
                    "No puede registrar salidas de otra sucursal."
                )

        if fecha_salida is not None:
            raise ValueError(
                "Esta visita ya tiene una salida registrada."
            )

        cursor.execute(
            """
            UPDATE visita
            SET fecha_hora_salida = CURRENT_TIMESTAMP
            WHERE id_visita = %s
            RETURNING fecha_hora_salida;
            """,
            (id_visita,)
        )

        fecha_registrada = cursor.fetchone()[0]

    return {
        "id_visita": id_visita,
        "fecha_hora_salida": fecha_registrada
    }


def liberar_mesa(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para liberar mesas.")

    id_visita = p_datos["id_visita"]
    id_mesa = p_datos["id_mesa"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_sucursal, fecha_hora_salida
            FROM visita
            WHERE id_visita = %s
            FOR UPDATE;
            """,
            (id_visita,)
        )

        visita = cursor.fetchone()

        if visita is None:
            raise ValueError("La visita no existe.")

        if p_sesion["rol"] != "administrador":
            if visita[0] != p_sesion["id_sucursal"]:
                raise PermissionError(
                    "No puede liberar mesas de otra sucursal."
                )

        if visita[1] is None:
            raise ValueError(
                "Primero debe registrar la salida del cliente."
            )

        cursor.execute(
            """
            SELECT vm.fecha_hora_liberacion
            FROM visita_mesa vm
            INNER JOIN mesa m
                ON vm.id_mesa = m.id_mesa
            WHERE vm.id_visita = %s
              AND vm.id_mesa = %s
              AND m.id_sucursal = %s
            FOR UPDATE OF vm;
            """,
            (id_visita, id_mesa, visita[0])
        )

        mesa = cursor.fetchone()

        if mesa is None:
            raise ValueError(
                "La mesa no pertenece a esta visita y sucursal."
            )

        if mesa[0] is not None:
            raise ValueError("La mesa ya fue liberada.")

        cursor.execute(
            """
            UPDATE visita_mesa
            SET fecha_hora_liberacion = CURRENT_TIMESTAMP
            WHERE id_visita = %s
              AND id_mesa = %s
            RETURNING fecha_hora_liberacion;
            """,
            (id_visita, id_mesa)
        )

        fecha_liberacion = cursor.fetchone()[0]

    return {
        "id_visita": id_visita,
        "id_mesa": id_mesa,
        "fecha_hora_liberacion": fecha_liberacion
    }

def consultar_mesas_disponibles(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar mesas.")

    v_id_sucursal = p_datos["id_sucursal"]
    v_id_reserva = p_datos.get("id_reserva")

    if p_sesion["rol"] != "administrador":
        if v_id_sucursal != p_sesion["id_sucursal"]:
            raise PermissionError("No puede consultar otra sucursal.")

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(
            """
            SELECT m.id_mesa, m.numero, m.capacidad, m.zona
            FROM mesa m
            WHERE m.id_sucursal = %s
              AND NOT EXISTS (
                  SELECT 1
                  FROM visita_mesa vm
                  WHERE vm.id_mesa = m.id_mesa
                    AND vm.fecha_hora_liberacion IS NULL
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM reserva_mesa rm
                  INNER JOIN reserva r
                      ON r.id_reserva = rm.id_reserva
                  WHERE rm.id_mesa = m.id_mesa
                    AND r.estado IN ('confirmada', 'atendida')
                    AND r.fecha_hora_inicio <= CURRENT_TIMESTAMP
                    AND r.fecha_hora_fin_estimada > CURRENT_TIMESTAMP
                    AND (
                        %s::INTEGER IS NULL
                        OR r.id_reserva <> %s
                    )
              )
            ORDER BY m.numero;
            """,
            (v_id_sucursal, v_id_reserva, v_id_reserva)
        )

        return v_cursor.fetchall()


# FIN DEL CÓDIGO :)