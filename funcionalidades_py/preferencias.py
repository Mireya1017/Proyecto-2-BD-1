# -----------------------------------------------------------
# Permitir que un cliente tenga varios productos favoritos,
# sin registrar dos veces la misma preferencia
# -----------------------------------------------------------

# Registra una preferencia de un cliente
def agregar_preferencia(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para agregar preferencias.")

    id_cliente = p_datos["id_cliente"]
    id_plato = p_datos["id_plato"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM preferencia_cliente
            WHERE id_cliente = %s
              AND id_plato = %s;
            """,
            (id_cliente, id_plato)
        )

        if cursor.fetchone() is not None:
            raise ValueError("El cliente ya tiene este plato como favorito.")

        cursor.execute(
            """
            INSERT INTO preferencia_cliente (id_cliente, id_plato)
            VALUES (%s, %s);
            """,
            (id_cliente, id_plato)
        )

    return "Preferencia registrada correctamente."

# -----------------------------------------------------------

# Basado en el ID del cliente, devuelve los platos favoritos
def consultar_preferencias(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar preferencias.")

    id_cliente = p_datos["id_cliente"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.id_plato, p.nombre, p.precio
            FROM preferencia_cliente pc
            INNER JOIN plato p
                ON pc.id_plato = p.id_plato
            WHERE pc.id_cliente = %s
            ORDER BY p.nombre;
            """,
            (id_cliente,)
        )

        preferencias = cursor.fetchall()

    return preferencias

# FIN DEL CÓDIGO :)