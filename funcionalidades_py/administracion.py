# funcionalidades_py/administracion.py
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.usuarios import validar_permiso
from datetime import date

def _validar_periodo(p_inicio, p_fin):
    try:
        v_inicio = (
            date.fromisoformat(p_inicio)
            if isinstance(p_inicio, str)
            else p_inicio
        )

        v_fin = (
            date.fromisoformat(p_fin)
            if isinstance(p_fin, str)
            else p_fin
        )
    except ValueError:
        raise ValueError("Las fechas deben tener formato AAAA-MM-DD.")

    if v_inicio is not None and v_fin is not None:
        if v_inicio > v_fin:
            raise ValueError(
                "La fecha inicial no puede ser posterior a la final."
            )

    return v_inicio, v_fin


def consultar_bitacora(p_sesion: dict, p_filtros: dict | None = None) -> list[dict]:
    """
    Consulta los registros de auditoría de la tabla bitacora (exclusivo para administrador).
    Permite filtrar por fecha_desde, fecha_hasta, id_usuario, tabla y operacion.
    """
    validar_permiso(p_sesion, ("administrador",))
    v_filtros = p_filtros or {}

    v_desde = v_filtros.get("fecha_desde")
    v_hasta = v_filtros.get("fecha_hasta")
    v_desde, v_hasta = _validar_periodo(v_desde, v_hasta)
    v_id_usuario = v_filtros.get("id_usuario")
    v_tabla = (v_filtros.get("tabla") or "").strip().lower() or None
    v_operacion = (v_filtros.get("operacion") or "").strip().upper() or None
    v_limite = int(v_filtros.get("limite", 100))

    if v_limite <= 0:
        raise ValueError("El límite debe ser mayor que cero.")

    if v_operacion not in (None, "INSERT", "UPDATE", "DELETE"):
        raise ValueError(
            "La operación debe ser INSERT, UPDATE o DELETE."
        )

    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                SELECT b.id_bitacora,
                       b.fecha_hora,
                       b.id_usuario,
                       COALESCE(u.nombre_usuario, 'SIN_USUARIO (SCRIPT/INICIAL)') AS nombre_usuario,
                       b.tabla,
                       b.operacion,
                       b.registro
                FROM bitacora b
                LEFT JOIN usuario u ON u.id_usuario = b.id_usuario
                WHERE (%s::timestamp IS NULL OR b.fecha_hora >= %s::timestamp)
                  AND (%s::date IS NULL OR b.fecha_hora < (%s::date + INTERVAL '1 day'))
                  AND (%s::integer IS NULL OR b.id_usuario = %s::integer)
                  AND (%s::varchar IS NULL OR LOWER(b.tabla) = %s::varchar)
                  AND (%s::varchar IS NULL OR b.operacion = %s::varchar)
                ORDER BY b.fecha_hora DESC, b.id_bitacora DESC
                LIMIT %s::integer;
                """,
                (
                    v_desde, v_desde,
                    v_hasta, v_hasta,
                    v_id_usuario, v_id_usuario,
                    v_tabla, v_tabla,
                    v_operacion, v_operacion,
                    v_limite,
                ),
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()


def generar_reporte_sucursales(
    p_sesion: dict,
    p_fecha_inicio: str | None = None,
    p_fecha_fin: str | None = None,
    p_id_sucursal: int | None = None,
    p_incluir_canceladas: bool = False,
) -> list[dict]:
    """
    Reporte de sucursales según cantidad de reservas, cantidad de ventas e importe vendido.
    Agrega reservas y ventas por separado mediante CTEs antes de combinarlas.
    """
    validar_permiso(p_sesion, ("administrador",))

    p_fecha_inicio, p_fecha_fin = _validar_periodo(
        p_fecha_inicio,
        p_fecha_fin
    )

    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                WITH reservas_agrupadas AS (
                    SELECT
                        r.id_sucursal,
                        COUNT(r.id_reserva) AS cantidad_reservas
                    FROM reserva r
                    WHERE (%s::timestamp IS NULL OR r.fecha_hora_inicio >= %s::timestamp)
                      AND (%s::date IS NULL OR r.fecha_hora_inicio < (%s::date + INTERVAL '1 day'))
                      AND (%s::boolean = TRUE OR r.estado <> 'cancelada')
                    GROUP BY r.id_sucursal
                ),
                importes_por_venta AS (
                    SELECT
                        v.id_venta,
                        vi.id_sucursal,
                        COALESCE(SUM(dv.cantidad * dv.precio_unitario), 0.00) AS importe_venta
                    FROM venta v
                    JOIN visita vi ON vi.id_visita = v.id_visita
                    LEFT JOIN detalle_venta dv ON dv.id_venta = v.id_venta
                    WHERE (%s::timestamp IS NULL OR v.fecha_hora >= %s::timestamp)
                      AND (%s::date IS NULL OR v.fecha_hora < (%s::date + INTERVAL '1 day'))
                    GROUP BY v.id_venta, vi.id_sucursal
                ),
                ventas_agrupadas AS (
                    SELECT
                        iv.id_sucursal,
                        COUNT(iv.id_venta) AS cantidad_ventas,
                        COALESCE(SUM(iv.importe_venta), 0.00) AS importe_vendido
                    FROM importes_por_venta iv
                    GROUP BY iv.id_sucursal
                )
                SELECT
                    s.id_sucursal,
                    s.nombre AS sucursal,
                    s.direccion,
                    COALESCE(ra.cantidad_reservas, 0) AS cantidad_reservas,
                    COALESCE(va.cantidad_ventas, 0) AS cantidad_ventas,
                    COALESCE(va.importe_vendido, 0.00)::NUMERIC(12,2) AS importe_vendido
                FROM sucursal s
                LEFT JOIN reservas_agrupadas ra ON ra.id_sucursal = s.id_sucursal
                LEFT JOIN ventas_agrupadas va ON va.id_sucursal = s.id_sucursal
                WHERE (%s::integer IS NULL OR s.id_sucursal = %s::integer)
                ORDER BY importe_vendido DESC, cantidad_ventas DESC, cantidad_reservas DESC, s.id_sucursal ASC;
                """,
                (
                    p_fecha_inicio, p_fecha_inicio,
                    p_fecha_fin, p_fecha_fin,
                    p_incluir_canceladas,
                    p_fecha_inicio, p_fecha_inicio,
                    p_fecha_fin, p_fecha_fin,
                    p_id_sucursal, p_id_sucursal,
                ),
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()