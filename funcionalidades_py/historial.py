from funcionalidades_py.clientes import obtener_cliente
from funcionalidades_py.preferencias import consultar_preferencias


def historial_visitas(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar el historial.")

    v_sql = """
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
    """

    v_parametros = [p_datos["id_cliente"]]

    if p_sesion["rol"] != "administrador":
        v_sql += " AND v.id_sucursal = %s"
        v_parametros.append(p_sesion["id_sucursal"])

    v_sql += """
        ORDER BY v.fecha_hora_llegada DESC,
                 v.id_visita DESC;
    """

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(v_sql, v_parametros)
        return v_cursor.fetchall()


def historial_reservas(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar reservas.")

    v_sql = """
        SELECT
            r.id_reserva,
            r.fecha_hora_inicio,
            r.fecha_hora_fin_estimada,
            r.cantidad_personas,
            r.estado,
            r.id_sucursal
        FROM reserva r
        WHERE r.id_cliente = %s
    """

    v_parametros = [p_datos["id_cliente"]]

    if p_sesion["rol"] != "administrador":
        v_sql += " AND r.id_sucursal = %s"
        v_parametros.append(p_sesion["id_sucursal"])

    v_sql += """
        ORDER BY r.fecha_hora_inicio DESC,
                 r.id_reserva DESC;
    """

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(v_sql, v_parametros)
        return v_cursor.fetchall()


def obtener_historial_cliente(p_conexion, p_sesion, p_datos):
    v_cliente = obtener_cliente(p_conexion, p_sesion, p_datos)

    if v_cliente is None:
        raise ValueError("El cliente no existe.")

    v_visitas = historial_visitas(
        p_conexion, p_sesion, p_datos
    )

    v_reservas = historial_reservas(
        p_conexion, p_sesion, p_datos
    )

    v_preferencias = consultar_preferencias(
        p_conexion, p_sesion, p_datos
    )

    return {
        "id_cliente": p_datos["id_cliente"],
        "visitas": v_visitas,
        "reservas": v_reservas,
        "preferencias": v_preferencias
    }