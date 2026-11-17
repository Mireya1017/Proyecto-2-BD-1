# =====================================================
# PRUEBAS DEL MODULO DE VENTAS
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from decimal import Decimal

from funcionalidades_py.ventas import (
    validar_productos,
    calcular_subtotal
)


def probar_error(p_nombre, p_productos):
    try:
        validar_productos(p_productos)
        print(f"ERROR: {p_nombre} no fue rechazado")

    except ValueError as v_error:
        print(f"CORRECTO: {p_nombre}")
        print(f"Motivo: {v_error}\n")


def main():

    print("\n===== PRUEBA DE VENTA VALIDA =====")

    v_productos = [
        {"id_plato": 1, "cantidad": 2},
        {"id_plato": 3, "cantidad": 1}
    ]

    v_productos_validados = validar_productos(v_productos)

    print("Productos validados:", v_productos_validados)

    # Precios obtenidos anteriormente del menu oficial
    v_subtotal_bowl = calcular_subtotal(
        2, Decimal("35.00")
    )

    v_subtotal_wrap = calcular_subtotal(
        1, Decimal("30.00")
    )

    v_total = v_subtotal_bowl + v_subtotal_wrap

    print(f"Subtotal bowls: Q{v_subtotal_bowl:.2f}")
    print(f"Subtotal wrap: Q{v_subtotal_wrap:.2f}")
    print(f"Total venta: Q{v_total:.2f}")

    assert v_total == Decimal("100.00")

    print("\n===== PRUEBAS DE VALIDACION =====")

    probar_error(
        "Venta sin productos",
        []
    )

    probar_error(
        "Cantidad negativa",
        [{"id_plato": 1, "cantidad": -2}]
    )

    probar_error(
        "Producto duplicado",
        [
            {"id_plato": 1, "cantidad": 2},
            {"id_plato": 1, "cantidad": 1}
        ]
    )

    probar_error(
        "Identificador invalido",
        [{"id_plato": 0, "cantidad": 1}]
    )

def probar_visita_inexistente():
    from funcionalidades_py.conexion import obtener_conexion
    from funcionalidades_py.ventas import registrar_venta

    # Sesión simulada únicamente para esta prueba local.
    # No se utiliza ejecutar_transaccion ni se confirma nada.
    v_sesion_prueba = {
        "id_usuario": None,
        "rol": "administrador",
        "id_sucursal": 1
    }

    v_datos = {
        "id_visita": 999999999,
        "productos": [
            {"id_plato": 1, "cantidad": 2},
            {"id_plato": 3, "cantidad": 1}
        ]
    }

    v_conexion = obtener_conexion()

    try:
        registrar_venta(
            v_conexion,
            v_sesion_prueba,
            v_datos
        )
    except ValueError as v_error:
        print("CORRECTO: Venta con visita inexistente rechazada.")
        print(f"Motivo: {v_error}")
    finally:
        v_conexion.rollback()
        v_conexion.close()
def probar_inventario_insuficiente():
    from funcionalidades_py.conexion import obtener_conexion
    from funcionalidades_py.ventas import registrar_venta

    v_sesion_prueba = {
        "id_usuario": None,
        "rol": "administrador",
        "id_sucursal": 1
    }

    v_datos = {
        "id_visita": 1,
        "productos": [
            {"id_plato": 1, "cantidad": 100}
        ]
    }

    v_conexion = obtener_conexion()

    try:
        registrar_venta(
            v_conexion,
            v_sesion_prueba,
            v_datos
        )
        print("ERROR: La venta debio rechazarse.")

    except ValueError as v_error:
        if "Inventario insuficiente" in str(v_error):
            print("CORRECTO: Venta rechazada por inventario insuficiente.")
            print(f"Motivo: {v_error}")
        else:
            raise

    finally:
        v_conexion.rollback()
        v_conexion.close()

if __name__ == "__main__":
    main()
    print("\n===== PRUEBA DE VISITA INEXISTENTE =====")
    probar_visita_inexistente()
    print("\n===== PRUEBA DE INVENTARIO INSUFICIENTE =====")
    probar_inventario_insuficiente()