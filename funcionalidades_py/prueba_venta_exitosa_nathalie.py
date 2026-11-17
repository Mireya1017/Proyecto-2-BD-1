
# PRUEBA DE VENTA EXITOSA SIN GUARDAR CAMBIOS
# Responsable: Nathalie

from getpass import getpass

from funcionalidades_py.usuarios import iniciar_sesion
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.ventas import registrar_venta


def main():
    print("\n===== PRUEBA CONTROLADA DE VENTA =====")

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

    v_conexion = obtener_conexion()

    try:
        v_resultado = registrar_venta(
            v_conexion,
            v_sesion,
            v_datos
        )

        print("\nVenta procesada correctamente.")
        print("ID temporal:", v_resultado["id_venta"])
        print(f"Total: Q{v_resultado['total']:.2f}")

        assert v_resultado["total"] == 100

        print("\nPRUEBA EXITOSA: se ejecutara ROLLBACK.")

    finally:
        v_conexion.rollback()
        v_conexion.close()

    print("Cambios revertidos. Inventario sin modificar.")


if __name__ == "__main__":
    main()
