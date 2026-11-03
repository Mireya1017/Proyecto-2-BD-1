# =====================================================
# MODULO DE INVENTARIO
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from funcionalidades_py.conexion import obtener_conexion
from datetime import date
from decimal import Decimal



def validar_acceso_inventario(p_sesion, p_id_sucursal):
    """Exige sesion confiable y limita gerente a su sucursal."""
    if not isinstance(p_sesion, dict) or p_sesion.get("rol") not in ("administrador", "gerente"):
        raise PermissionError("No tiene permisos para acceder al inventario.")
    if p_sesion.get("id_usuario") is None:
        raise PermissionError("Se requiere una sesion autenticada.")
    if isinstance(p_id_sucursal, bool) or not str(p_id_sucursal).isdigit() or int(p_id_sucursal) <= 0:
        raise ValueError("Sucursal invalida.")
    if p_sesion["rol"] == "gerente" and int(p_sesion["id_sucursal"]) != int(p_id_sucursal):
        raise PermissionError("Solo puede consultar su sucursal.")
    return int(p_id_sucursal)


def consultar_existencias(p_id_sucursal, p_sesion):
    """
    Consulta las existencias utilizables de cada insumo
    en una sucursal determinada.

    No incluye cantidades de lotes vencidos.
    """

    p_id_sucursal = validar_acceso_inventario(p_sesion, p_id_sucursal)

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


def consultar_lotes(p_id_sucursal, p_id_insumo, p_sesion):
    """
    Consulta los lotes de un insumo en una sucursal,
    incluyendo cantidades y fechas de caducidad.
    """

    p_id_sucursal = validar_acceso_inventario(p_sesion, p_id_sucursal)

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

    # Validar rol y acceso a la sucursal.
    v_sucursal = validar_acceso_inventario(
        p_sesion,
        p_datos["id_sucursal"]
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

    if v_cantidad > Decimal("999999999.999") or v_cantidad.as_tuple().exponent < -3:
        raise ValueError("Cantidad fuera de precision NUMERIC(12,3).")

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

def consultar_alertas_existencias(p_id_sucursal, p_sesion):
    """Devuelve los insumos actualmente por debajo del mínimo."""
    v_existencias = consultar_existencias(
        p_id_sucursal,
        p_sesion
    )

    v_alertas = []

    for v_id, v_nombre, v_unidad, v_minimo, v_actual in v_existencias:
        if v_actual < v_minimo:
            v_alertas.append(
                (v_nombre, v_unidad, v_minimo, v_actual)
            )

    return v_alertas


def consultar_alertas_caducidad(p_id_sucursal, p_dias=7, *, p_sesion):
    """
    Devuelve lotes proximos a caducar.

    p_dias: ventana provisional de alerta.
    """

    if not isinstance(p_dias, int) or isinstance(p_dias, bool):
        raise ValueError("Los dias deben ser un numero entero.")

    if p_dias < 0:
        raise ValueError("Los dias no pueden ser negativos.")

    p_id_sucursal = validar_acceso_inventario(p_sesion, p_id_sucursal)

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


# =====================================================
# ALERTAS DE INVENTARIO AL 15 %
# Responsable: Nathalie
# Referencia: datos_iniciales.sql
# =====================================================




STOCK_REFERENCIA = {
    "Pollo": Decimal("5000"),
    "Carne de res": Decimal("5000"),
    "Arroz": Decimal("10000"),
    "Frijoles": Decimal("8000"),
    "Lechuga": Decimal("2000"),
    "Tortilla para wrap": Decimal("100"),
    "Sprite en lata": Decimal("48"),
    "Coca-Cola en lata": Decimal("48"),
    "Agua pura embotellada": Decimal("48")
}


def consultar_alertas_porcentaje(p_sesion, p_id_sucursal):
    """Calcula porcentajes usando el stock inicial como referencia."""
    v_existencias = consultar_existencias(
        p_id_sucursal,
        p_sesion
    )

    v_resultados = []

    for v_id, v_nombre, v_unidad, v_minimo, v_actual in v_existencias:
        v_referencia = STOCK_REFERENCIA.get(v_nombre)
        v_porcentaje = None

        if v_referencia is not None and v_referencia > 0:
            v_porcentaje = (
                v_actual * Decimal("100") / v_referencia
            ).quantize(Decimal("0.01"))

        if v_porcentaje is not None and v_porcentaje <= 15:
            v_estado = "ALERTA 15%"
        elif v_actual < v_minimo:
            v_estado = "BAJO MINIMO"
        elif v_porcentaje is None:
            v_estado = "SIN REFERENCIA"
        else:
            v_estado = "NORMAL"

        v_resultados.append({
            "insumo": v_nombre,
            "unidad": v_unidad,
            "existencia_actual": v_actual,
            "referencia": v_referencia,
            "porcentaje": v_porcentaje,
            "minimo": v_minimo,
            "estado": v_estado
        })

    return v_resultados