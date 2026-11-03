# =====================================================
# MODULO DE INVENTARIO
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from funcionalidades_py.conexion import obtener_conexion


def consultar_existencias(p_id_sucursal):
    """
    Consulta las existencias utilizables de cada insumo
    en una sucursal determinada.

    No incluye cantidades de lotes vencidos.
    """

    v_sql = """
        SELECT
            i.id_insumo,
            i.nombre,
            i.unidad_medida,
            i.existencia_minima,
            COALESCE(
                SUM(
                    CASE
                        WHEN l.fecha_caducidad >= CURRENT_DATE
                        THEN l.cantidad_disponible
                        ELSE 0
                    END
                ), 0
            ) AS existencia_utilizable
        FROM insumo AS i
        LEFT JOIN lote AS l
            ON i.id_insumo = l.id_insumo
            AND l.id_sucursal = %s
        GROUP BY
            i.id_insumo,
            i.nombre,
            i.unidad_medida,
            i.existencia_minima
        ORDER BY i.nombre;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(v_sql, (p_id_sucursal,))
            return v_cursor.fetchall()


def consultar_lotes(p_id_sucursal, p_id_insumo):
    """
    Consulta los lotes de un insumo en una sucursal,
    incluyendo cantidades y fechas de caducidad.
    """

    v_sql = """
        SELECT
            l.id_lote,
            l.fecha_recepcion,
            l.fecha_caducidad,
            l.cantidad_disponible,
            i.unidad_medida,
            CASE
                WHEN l.fecha_caducidad < CURRENT_DATE
                    THEN 'Vencido'
                WHEN l.cantidad_disponible = 0
                    THEN 'Agotado'
                ELSE 'Utilizable'
            END AS estado_lote
        FROM lote AS l
        JOIN insumo AS i
            ON l.id_insumo = i.id_insumo
        WHERE l.id_sucursal = %s
          AND l.id_insumo = %s
        ORDER BY
            l.fecha_caducidad,
            l.id_lote;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(
                v_sql,
                (p_id_sucursal, p_id_insumo)
            )
            return v_cursor.fetchall()
# =====================================================
# REGISTRO DE ENTRADAS DE INVENTARIO
# Responsable: Nathalie
# =====================================================

from datetime import date
from decimal import Decimal


def registrar_entrada(p_conexion, p_sesion, p_datos):
    """
    Registra un nuevo lote de inventario.

    Recibe:
        p_conexion: conexion compartida de PostgreSQL.
        p_sesion: usuario autenticado, rol y sucursal.
        p_datos: informacion del lote.

    Devuelve:
        Identificador del lote registrado.

    La confirmacion o reversion corresponde a
    ejecutar_transaccion().
    """

    # 1. Validar permisos
    v_rol = p_sesion["rol"]
    v_sucursal_usuario = p_sesion["id_sucursal"]
    v_sucursal = int(p_datos["id_sucursal"])

    if v_rol not in ("administrador", "gerente"):
        raise PermissionError(
            "No tiene permisos para registrar entradas."
        )

    if v_rol == "gerente" and v_sucursal != v_sucursal_usuario:
        raise PermissionError(
            "Solo puede registrar entradas en su sucursal."
        )

    # 2. Obtener y validar datos
    v_insumo = int(p_datos["id_insumo"])
    v_cantidad = Decimal(str(p_datos["cantidad"]))
    v_recepcion = date.fromisoformat(
        str(p_datos["fecha_recepcion"])
    )
    v_caducidad = date.fromisoformat(
        str(p_datos["fecha_caducidad"])
    )

    if not v_cantidad.is_finite() or v_cantidad <= 0:
        raise ValueError(
            "La cantidad debe ser un numero positivo y finito."
        )

    if v_caducidad < v_recepcion:
        raise ValueError(
            "La caducidad no puede ser anterior a la recepcion."
        )

    # 3. Registrar el lote
    v_sql = """
        INSERT INTO lote (
            id_insumo,
            id_sucursal,
            fecha_recepcion,
            fecha_caducidad,
            cantidad_disponible
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_lote;
    """

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(
            v_sql,
            (
                v_insumo,
                v_sucursal,
                v_recepcion,
                v_caducidad,
                v_cantidad
            )
        )

        v_resultado = v_cursor.fetchone()

    return v_resultado[0]

# =====================================================
# ALERTAS DE INVENTARIO
# Responsable: Nathalie
# =====================================================

def consultar_alertas_existencias(p_id_sucursal):
    """
    Devuelve los insumos cuya existencia utilizable
    es inferior al minimo establecido.
    """

    v_sql = """
        WITH existencias AS (
            SELECT
                i.id_insumo,
                i.nombre,
                i.unidad_medida,
                i.existencia_minima,
                COALESCE(
                    SUM(l.cantidad_disponible) FILTER (
                        WHERE l.fecha_caducidad >= CURRENT_DATE
                    ), 0
                ) AS existencia_utilizable
            FROM insumo AS i
            LEFT JOIN lote AS l
                ON l.id_insumo = i.id_insumo
               AND l.id_sucursal = %s
            GROUP BY
                i.id_insumo,
                i.nombre,
                i.unidad_medida,
                i.existencia_minima
        )
        SELECT
            nombre,
            unidad_medida,
            existencia_minima,
            existencia_utilizable
        FROM existencias
        WHERE existencia_utilizable < existencia_minima
        ORDER BY nombre;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(v_sql, (p_id_sucursal,))
            return v_cursor.fetchall()


def consultar_alertas_caducidad(p_id_sucursal, p_dias=7):
    """
    Devuelve lotes proximos a caducar.

    p_dias: ventana provisional de alerta.
    """

    if not isinstance(p_dias, int) or isinstance(p_dias, bool):
        raise ValueError("Los dias deben ser un numero entero.")

    if p_dias < 0:
        raise ValueError("Los dias no pueden ser negativos.")

    v_sql = """
        SELECT
            i.nombre,
            l.id_lote,
            l.fecha_caducidad,
            l.cantidad_disponible,
            i.unidad_medida,
            l.fecha_caducidad - CURRENT_DATE AS dias_restantes
        FROM lote AS l
        JOIN insumo AS i
            ON l.id_insumo = i.id_insumo
        WHERE l.id_sucursal = %s
          AND l.fecha_caducidad >= CURRENT_DATE
          AND l.fecha_caducidad <= CURRENT_DATE + %s
          AND l.cantidad_disponible > 0
        ORDER BY
            l.fecha_caducidad,
            i.nombre,
            l.id_lote;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(
                v_sql,
                (p_id_sucursal, p_dias)
            )
            return v_cursor.fetchall()