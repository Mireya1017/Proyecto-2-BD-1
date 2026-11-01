# -----------------------------------------------------------
# Registra visitas, salidas y mesas liberadas
# -----------------------------------------------------------

def registrar_visita(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para registrar visitas.")

    id_cliente = p_datos["id_cliente"]
    id_sucursal = p_datos["id_sucursal"]
    cantidad_personas = p_datos["cantidad_personas"]
    observaciones = p_datos.get("observaciones")

    if cantidad_personas <= 0:
        raise ValueError("La cantidad de personas debe ser mayor que cero.")

    if p_sesion["rol"] != "administrador":
        if id_sucursal != p_sesion["id_sucursal"]:
            raise PermissionError(
                "No puede registrar visitas de otra sucursal."
            )

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_cliente
            FROM cliente
            WHERE id_cliente = %s;
            """,
            (id_cliente,)
        )

        if cursor.fetchone() is None:
            raise ValueError("El cliente no existe.")

    # Pendiente: comprobar disponibilidad y asignar mesas.
    raise NotImplementedError(
        "Falta integrar la disponibilidad de mesas."
    )


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


# FIN DEL CÓDIGO :)