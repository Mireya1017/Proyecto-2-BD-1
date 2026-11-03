
# =====================================================
# REPORTES DE INVENTARIO Y VENTAS
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from datetime import date
from funcionalidades_py.conexion import obtener_conexion


# =====================================================
# VALIDACION DE PERMISOS
# =====================================================

def validar_permiso_reportes(p_sesion):
    """
    Verifica que el usuario tenga rol administrador.

    La sesion debe provenir del modulo de
    autenticacion del sistema.
    """

    if not isinstance(p_sesion, dict):
        raise PermissionError(
            "Se requiere una sesion valida."
        )

    if p_sesion.get("rol") != "administrador":
        raise PermissionError(
            "Solo los administradores pueden consultar reportes."
        )


# =====================================================
# REPORTE 1: TOP 10 DE PRODUCTOS MAS VENDIDOS
# =====================================================

def reporte_top_productos(p_sesion):
    """
    Devuelve los 10 productos mas vendidos,
    ordenados por cantidad de unidades.

    Incluye los ingresos calculados con el precio
    aplicado en cada detalle de venta.

    Solo permite acceso a administradores.
    """

    validar_permiso_reportes(p_sesion)

    v_sql = """
        WITH ventas_productos AS (
            SELECT
                dv.id_plato,
                SUM(dv.cantidad) AS unidades_vendidas,
                SUM(
                    dv.cantidad * dv.precio_unitario
                ) AS ingresos_totales
            FROM detalle_venta AS dv
            JOIN venta AS v
                ON dv.id_venta = v.id_venta
            GROUP BY
                dv.id_plato
        )
        SELECT
            p.id_plato,
            p.nombre AS producto,
            vp.unidades_vendidas,
            vp.ingresos_totales
        FROM ventas_productos AS vp
        JOIN plato AS p
            ON vp.id_plato = p.id_plato
        ORDER BY
            vp.unidades_vendidas DESC,
            p.nombre ASC,
            p.id_plato ASC
        LIMIT 10;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(v_sql)
            return v_cursor.fetchall()


# =====================================================
# REPORTE 2: CADUCIDADES POR MES Y SUCURSAL
# =====================================================

def reporte_caducidades_mensual(
    p_sesion,
    p_anio,
    p_mes,
    p_id_sucursal
):
    """
    Consulta los lotes cuya fecha de caducidad
    corresponde al mes y anio seleccionados.

    Parametros:
        p_sesion: sesion autenticada.
        p_anio: anio del reporte.
        p_mes: mes del reporte.
        p_id_sucursal: identificador de sucursal.

    Devuelve:
        Sucursal, insumo, lote, fecha de caducidad,
        cantidad disponible y unidad de medida.

    Las cantidades son actuales, no historicas.
    """

    # 1. Validar permisos
    validar_permiso_reportes(p_sesion)

    # 2. Validar parametros
    try:
        v_anio = int(p_anio)
        v_mes = int(p_mes)
        v_id_sucursal = int(p_id_sucursal)
        date(v_anio, v_mes, 1)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            "El anio, mes o sucursal no son validos."
        )

    if v_id_sucursal <= 0:
        raise ValueError(
            "La sucursal debe ser valida."
        )

    # 3. Consulta SQL
    v_sql = """
        WITH periodo AS (
            SELECT
                MAKE_DATE(%s, %s, 1) AS inicio,
                (
                    MAKE_DATE(%s, %s, 1)
                    + INTERVAL '1 month'
                )::DATE AS fin
        )
        SELECT
            s.nombre AS sucursal,
            i.nombre AS insumo,
            l.id_lote,
            l.fecha_caducidad,
            l.cantidad_disponible,
            i.unidad_medida
        FROM lote AS l
        JOIN insumo AS i
            ON l.id_insumo = i.id_insumo
        JOIN sucursal AS s
            ON l.id_sucursal = s.id_sucursal
        CROSS JOIN periodo AS p
        WHERE l.id_sucursal = %s
          AND l.fecha_caducidad >= p.inicio
          AND l.fecha_caducidad < p.fin
        ORDER BY
            l.fecha_caducidad,
            i.nombre,
            l.id_lote;
    """

    # 4. Ejecutar consulta
    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(
                v_sql,
                (
                    v_anio,
                    v_mes,
                    v_anio,
                    v_mes,
                    v_id_sucursal
                )
            )

            return v_cursor.fetchall()
