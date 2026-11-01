# -----------------------------------------------------------
# Historial de visitas, reservas y visitas, reservas y preferencias (juntos)
# -----------------------------------------------------------

from funcionalidades_py.preferencias import consultar_preferencias

# -----------------------------------------------------------

def historial_visitas(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar el historial.")

    id_cliente = p_datos["id_cliente"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                v.id_visita,
                v.fecha_hora_llegada,
                v.fecha_hora_salida,
                v.cantidad_personas,
                v.observaciones,
                v.id_reserva,
                v.id_sucursal
            FROM visita v
            WHERE v.id_cliente = %s
            ORDER BY v.fecha_hora_llegada DESC,
                     v.id_visita DESC;
            """,
            (id_cliente,)
        )

        return cursor.fetchall()

# -----------------------------------------------------------

def historial_reservas(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar reservas.")

    id_cliente = p_datos["id_cliente"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                r.id_reserva,
                r.fecha_hora_inicio,
                r.fecha_hora_fin_estimada,
                r.cantidad_personas,
                r.estado,
                r.id_sucursal
            FROM reserva r
            WHERE r.id_cliente = %s
            ORDER BY r.fecha_hora_inicio DESC,
                     r.id_reserva DESC;
            """,
            (id_cliente,)
        )

        return cursor.fetchall()

# -----------------------------------------------------------

def obtener_historial_cliente(p_conexion, p_sesion, p_datos):
    id_cliente = p_datos["id_cliente"]

    datos = {"id_cliente": id_cliente}

    visitas = historial_visitas(
        p_conexion, p_sesion, datos
    )

    reservas = historial_reservas(
        p_conexion, p_sesion, datos
    )

    preferencias = consultar_preferencias(
        p_conexion, p_sesion, datos
    )

    return {
        "id_cliente": id_cliente,
        "visitas": visitas,
        "reservas": reservas,
        "preferencias": preferencias
    }

# -----------------------------------------------------------

# FIN DEL CÓDIGO :)