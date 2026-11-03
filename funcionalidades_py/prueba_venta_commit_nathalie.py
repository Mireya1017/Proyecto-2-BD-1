
# =====================================================
# PRUEBA DE VENTA CON COMMIT
# Responsable: Nathalie
# =====================================================

from getpass import getpass

from funcionalidades_py.usuarios import iniciar_sesion
from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.ventas import registrar_venta


def main():
    print("\n===== REGISTRO REAL DE VENTA =====")

    v_clave = getpass("Contrasena del administrador: ")

    v_sesion = iniciar_sesion(
        "admin_nathalie",
        v_clave
    )

    v_datos = {
        "id_visita": 1,
        "productos": [
            {"id_plato": 1, "cantidad": 2},
            {"id_plato": 3, "cantidad": 1}
        ]
    }

    print("\n===== CONFIRMACION DE VENTA =====")
    print("Visita: 1")
    print("Productos: 2 bowls de pollo y 1 wrap de pollo")
    print("Total esperado: Q100.00")

    v_confirmacion = input(
        "\nConfirmar venta real (SI/NO): "
    ).strip().upper()

    if v_confirmacion != "SI":
        print("Operacion cancelada. No se registraron cambios.")
        return
    v_resultado = ejecutar_transaccion(
        v_sesion,
        registrar_venta,
        v_datos
    )

    print("\nVENTA REGISTRADA CORRECTAMENTE")
    print(f"ID de venta: {v_resultado['id_venta']}")
    print(f"ID de visita: {v_resultado['id_visita']}")
    print(f"Total: Q{v_resultado['total']:.2f}")


if __name__ == "__main__":
    main()
