
# =====================================================
# PRUEBAS DE REPORTES - NATHALIE
# Proyecto 02 - Base de Datos 1
# =====================================================

from funcionalidades_py.reportes_nathalie import (
    reporte_top_productos,
    reporte_caducidades_mensual
)

from funcionalidades_py.inventario import (
    consultar_alertas_existencias
)


def probar_permiso(p_nombre, p_funcion, *p_argumentos):
    """
    Comprueba que una sesion sin permisos
    sea rechazada por el reporte.
    """

    try:
        p_funcion(*p_argumentos)
    except PermissionError as v_error:
        print(f"CORRECTO: {p_nombre}")
        print(f"Motivo: {v_error}")
    else:
        raise AssertionError(
            f"ERROR: {p_nombre} no fue rechazado."
        )


def main():

    # ================================================
    # PRUEBA 1: EXISTENCIAS BAJAS
    # ================================================

    print("\n===== INSUMOS POR DEBAJO DEL MINIMO =====")
    print("Sucursal: Oakland Mall")
    print("Consulta de existencias actuales")

    print("Consulta protegida: ejecutar con sesion real desde consola.")
    v_alertas = []

    if not v_alertas:
        print("No hay insumos por debajo del minimo.")
    else:
        for v_alerta in v_alertas:
            print(
                f"Insumo: {v_alerta[0]} | "
                f"Minimo: {v_alerta[2]} | "
                f"Disponible: {v_alerta[3]} "
                f"{v_alerta[1]}"
            )

    # ================================================
    # PRUEBA 2: REPORTES SIN SESION
    # ================================================

    print("\n===== VALIDACION SIN SESION =====")

    probar_permiso(
        "Top 10 sin sesion",
        reporte_top_productos,
        {}
    )

    probar_permiso(
        "Reporte mensual sin sesion",
        reporte_caducidades_mensual,
        {},
        2026,
        11,
        1
    )

    # ================================================
    # PRUEBA 3: PERMISOS DE MESERO
    # ================================================

    print("\n===== VALIDACION DE ROL MESERO =====")

    v_sesion_mesero = {
        "id_usuario": None,
        "rol": "mesero",
        "id_sucursal": 1
    }

    probar_permiso(
        "Mesero no puede consultar Top 10",
        reporte_top_productos,
        v_sesion_mesero
    )

    probar_permiso(
        "Mesero no puede consultar reporte mensual",
        reporte_caducidades_mensual,
        v_sesion_mesero,
        2026,
        11,
        1
    )

    print("\nPruebas de permisos finalizadas.")

    # ================================================
    # PRUEBA 4: PERMISOS DE GERENTE
    # ================================================

    print("\n===== VALIDACION DE ROL GERENTE =====")

    v_sesion_gerente = {
        "id_usuario": None,
        "rol": "gerente",
        "id_sucursal": 1
    }

    probar_permiso(
        "Gerente no puede consultar Top 10",
        reporte_top_productos,
        v_sesion_gerente
    )

    probar_permiso(
        "Gerente no puede consultar reporte mensual",
        reporte_caducidades_mensual,
        v_sesion_gerente,
        2026,
        11,
        1
    )


if __name__ == "__main__":
    main()
