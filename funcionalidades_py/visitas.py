# -----------------------------------------------------------
# Registra visitas
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

# FIN DEL CÓDIGO :)