# -----------------------------------------------------------
# Reportes de los clientes
# -----------------------------------------------------------

# Top 10 clientes frecuentes
def top_clientes_frecuentes(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] != "administrador":
        raise PermissionError(
            "Solo el administrador puede consultar este reporte."
        )

    fecha_inicio = p_datos["fecha_inicio"]
    fecha_fin = p_datos["fecha_fin"]

    if fecha_inicio >= fecha_fin:
        raise ValueError(
            "La fecha inicial debe ser anterior a la fecha final."
        )

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.id_cliente,
                c.nombre,
                COUNT(v.id_visita) AS total_visitas
            FROM cliente c
            INNER JOIN visita v
                ON c.id_cliente = v.id_cliente
            WHERE v.fecha_hora_llegada >= %s
              AND v.fecha_hora_llegada < %s
            GROUP BY c.id_cliente, c.nombre
            ORDER BY total_visitas DESC, c.id_cliente ASC
            LIMIT 10;
            """,
            (fecha_inicio, fecha_fin)
        )

        resultados = cursor.fetchall()

    return resultados

# -----------------------------------------------------------

from funcionalidades_py.preferencias import consultar_preferencias

# Top 5 clientes con más reservas y sus preferencias
def top_clientes_reservas(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] != "administrador":
        raise PermissionError(
            "Solo el administrador puede consultar este reporte."
        )

    fecha_inicio = p_datos["fecha_inicio"]
    fecha_fin = p_datos["fecha_fin"]

    if fecha_inicio >= fecha_fin:
        raise ValueError(
            "La fecha inicial debe ser anterior a la fecha final."
        )

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.id_cliente,
                c.nombre,
                COUNT(r.id_reserva) AS total_reservas
            FROM cliente c
            INNER JOIN reserva r
                ON c.id_cliente = r.id_cliente
            WHERE r.estado <> 'cancelada'
              AND r.fecha_hora_inicio >= %s
              AND r.fecha_hora_inicio < %s
            GROUP BY c.id_cliente, c.nombre
            ORDER BY total_reservas DESC, c.id_cliente ASC
            LIMIT 5;
            """,
            (fecha_inicio, fecha_fin)
        )

        clientes = cursor.fetchall()

    resultados = []

    for cliente in clientes:
        id_cliente = cliente[0]
        nombre = cliente[1]
        total_reservas = cliente[2]

        preferencias = consultar_preferencias(
            p_conexion,
            p_sesion,
            {"id_cliente": id_cliente}
        )

        nombres_platos = [
            plato[1] for plato in preferencias
        ]

        resultados.append({
            "id_cliente": id_cliente,
            "nombre": nombre,
            "total_reservas": total_reservas,
            "preferencias": nombres_platos
        })

    return resultados

# -----------------------------------------------------------

# FIN DEL CÓDIGO :)