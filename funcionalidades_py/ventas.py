# =====================================================
# MODULO DE VENTAS
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from decimal import Decimal, InvalidOperation
from funcionalidades_py.conexion import obtener_conexion


def entero_positivo(p_valor):
    if isinstance(p_valor, bool) or not str(p_valor).isdigit():
        raise ValueError("Debe ser un entero positivo.")

    v_numero = int(p_valor)

    if v_numero <= 0:
        raise ValueError("Debe ser un entero positivo.")

    return v_numero

def validar_productos(p_productos):
    """
    Valida los productos y cantidades de una venta.

    Recibe una lista de diccionarios:
    [
        {"id_plato": 1, "cantidad": 2},
        {"id_plato": 3, "cantidad": 1}
    ]

    Devuelve los productos normalizados.
    """

    if not isinstance(p_productos, list) or not p_productos:
        raise ValueError(
            "La venta debe contener al menos un producto."
        )

    v_productos = []
    v_identificadores = set()

    for v_producto in p_productos:

        if not isinstance(v_producto, dict):
            raise ValueError("El formato del producto no es valido.")

        try:
            v_id_plato = entero_positivo(v_producto["id_plato"])
            v_cantidad = entero_positivo(v_producto["cantidad"])
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ValueError(
                "El identificador y la cantidad deben ser enteros."
            )

        if v_id_plato <= 0 or v_cantidad <= 0:
            raise ValueError(
                "El producto y la cantidad deben ser positivos."
            )

        if v_id_plato in v_identificadores:
            raise ValueError(
                "Un producto no puede repetirse en la misma venta."
            )

        v_identificadores.add(v_id_plato)

        v_productos.append({
            "id_plato": v_id_plato,
            "cantidad": v_cantidad
        })

    return v_productos


def calcular_subtotal(p_cantidad, p_precio):
    """
    Calcula el subtotal conservando precision decimal.
    """

    try:
        v_cantidad = Decimal(str(p_cantidad))
        v_precio = Decimal(str(p_precio))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Cantidad o precio invalido.")

    if (
        not v_cantidad.is_finite()
        or not v_precio.is_finite()
        or v_cantidad <= 0
        or v_precio <= 0
    ):
        raise ValueError(
            "La cantidad y el precio deben ser positivos."
        )

    return v_cantidad * v_precio

def consultar_menu():
    """
    Consulta los productos y precios actuales
    del restaurante.
    """

    v_sql = """
        SELECT
            id_plato,
            nombre,
            precio
        FROM plato
        ORDER BY id_plato;
    """

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(v_sql)
            return v_cursor.fetchall()

# =====================================================
# REGISTRO TRANSACCIONAL DE VENTAS
# Responsable: Nathalie
# =====================================================



def registrar_venta(p_conexion, p_sesion, p_datos):
    """
    Registra una venta, sus detalles y el consumo FEFO.

    Debe ejecutarse mediante ejecutar_transaccion().
    No realiza commit, rollback ni abre conexiones.
    """

    # 1. Validar permisos y datos de entrada
    if not isinstance(p_sesion, dict) or p_sesion.get("rol") not in (
        "administrador", "gerente", "mesero"
    ):
        raise PermissionError(
            "No tiene permisos para registrar ventas."
        )
    
    if p_sesion.get("id_usuario") is None:
        raise PermissionError("Se requiere una sesión autenticada.")

    if not isinstance(p_datos, dict):
        raise ValueError("Datos de venta invalidos.")
    if isinstance(p_datos.get("id_visita"), bool) or not str(p_datos.get("id_visita", "")).isdigit():
        raise ValueError("La visita debe ser valida.")
    v_id_visita = int(p_datos["id_visita"])

    if v_id_visita <= 0:
        raise ValueError("La visita debe ser valida.")

    v_productos = validar_productos(p_datos["productos"])

    with p_conexion.cursor() as v_cursor:

        # 2. Consultar la visita y su sucursal
        v_cursor.execute(
            """
            SELECT id_sucursal, fecha_hora_salida
            FROM visita
            WHERE id_visita = %s
            FOR UPDATE;
            """,
            (v_id_visita,)
        )

        v_visita = v_cursor.fetchone()

        if v_visita is None:
            raise ValueError("La visita no existe.")

        v_id_sucursal, v_salida = v_visita

        if (
            p_sesion["rol"] != "administrador"
            and int(p_sesion["id_sucursal"]) != v_id_sucursal
        ):
            raise PermissionError(
                "No puede registrar ventas en otra sucursal."
            )

        if v_salida is not None:
            raise ValueError(
                "No se pueden registrar ventas en una visita finalizada."
            )

        # 3. Obtener precios reales y calcular detalles
        v_detalles = []
        v_total = Decimal("0.00")

        for v_producto in v_productos:
            v_cursor.execute(
                """
                SELECT precio
                FROM plato
                WHERE id_plato = %s;
                """,
                (v_producto["id_plato"],)
            )

            v_fila = v_cursor.fetchone()

            if v_fila is None:
                raise ValueError(
                    f"El plato {v_producto['id_plato']} no existe."
                )

            v_precio = v_fila[0]
            v_cantidad = v_producto["cantidad"]

            v_subtotal = calcular_subtotal(
                v_cantidad, v_precio
            )

            v_total += v_subtotal

            v_detalles.append({
                "id_plato": v_producto["id_plato"],
                "cantidad": v_cantidad,
                "precio": v_precio
            })

        # 4. Calcular consumo conjunto por ingrediente
        v_consumo = {}

        for v_detalle in v_detalles:
            v_cursor.execute(
                """
                SELECT id_insumo, cantidad
                FROM receta
                WHERE id_plato = %s;
                """,
                (v_detalle["id_plato"],)
            )

            v_receta = v_cursor.fetchall()

            if not v_receta:
                raise ValueError(
                    f"El plato {v_detalle['id_plato']} "
                    "no tiene receta registrada."
                )

            for v_id_insumo, v_cantidad_receta in v_receta:
                v_necesario = (
                    v_cantidad_receta * v_detalle["cantidad"]
                )

                v_consumo[v_id_insumo] = (
                    v_consumo.get(
                        v_id_insumo, Decimal("0")
                    ) + v_necesario
                )

        # 5. Bloquear lotes y planificar consumo FEFO
        v_descuentos = []

        for v_id_insumo in sorted(v_consumo):
            v_pendiente = v_consumo[v_id_insumo]

            v_cursor.execute(
                """
                SELECT
                    id_lote,
                    cantidad_disponible
                FROM lote
                WHERE id_sucursal = %s
                  AND id_insumo = %s
                  AND fecha_caducidad >= CURRENT_DATE
                  AND cantidad_disponible > 0
                ORDER BY fecha_caducidad, id_lote
                FOR UPDATE;
                """,
                (v_id_sucursal, v_id_insumo)
            )

            v_lotes = v_cursor.fetchall()

            for v_id_lote, v_disponible in v_lotes:
                v_descontar = min(
                    v_pendiente, v_disponible
                )

                v_descuentos.append(
                    (v_id_lote, v_descontar)
                )

                v_pendiente -= v_descontar

                if v_pendiente == 0:
                    break

            if v_pendiente > 0:
                raise ValueError(
                    f"Inventario insuficiente "
                    f"para el insumo {v_id_insumo}."
                )

        # 6. Registrar cabecera de venta
        v_cursor.execute(
            """
            INSERT INTO venta (id_visita, fecha_hora)
            VALUES (%s, CURRENT_TIMESTAMP)
            RETURNING id_venta;
            """,
            (v_id_visita,)
        )

        v_id_venta = v_cursor.fetchone()[0]

        # 7. Registrar detalles con precio aplicado
        for v_detalle in v_detalles:
            v_cursor.execute(
                """
                INSERT INTO detalle_venta (
                    id_venta,
                    id_plato,
                    cantidad,
                    precio_unitario
                )
                VALUES (%s, %s, %s, %s);
                """,
                (
                    v_id_venta,
                    v_detalle["id_plato"],
                    v_detalle["cantidad"],
                    v_detalle["precio"]
                )
            )

        # 8. Descontar ingredientes de los lotes
        for v_id_lote, v_descontar in v_descuentos:
            v_cursor.execute(
                """
                UPDATE lote
                SET cantidad_disponible =
                    cantidad_disponible - %s
                WHERE id_lote = %s
                  AND cantidad_disponible >= %s;
                """,
                (
                    v_descontar,
                    v_id_lote,
                    v_descontar
                )
            )

            if v_cursor.rowcount != 1:
                raise ValueError(
                    "No fue posible descontar el lote."
                )

    return {
        "id_venta": v_id_venta,
        "id_visita": v_id_visita,
        "total": v_total,
        "detalles": v_detalles
    }