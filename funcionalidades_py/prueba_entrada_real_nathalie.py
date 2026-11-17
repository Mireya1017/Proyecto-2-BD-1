
from datetime import date, timedelta
from getpass import getpass

from funcionalidades_py.usuarios import iniciar_sesion
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.inventario import registrar_entrada


def main():
    print("\n===== PRUEBA DE ENTRADA DE INVENTARIO =====")

    v_clave = getpass("Contrasena del administrador: ")
    v_sesion = iniciar_sesion("admin_nathalie", v_clave)

    v_hoy = date.today()

    v_datos = {
        "id_insumo": 1,
        "id_sucursal": 1,
        "fecha_recepcion": v_hoy.isoformat(),
        "fecha_caducidad": (
            v_hoy + timedelta(days=14)
        ).isoformat(),
        "cantidad": "1000.000"
    }

    v_conexion = obtener_conexion()

    try:
        v_id_lote = registrar_entrada(
            v_conexion,
            v_sesion,
            v_datos
        )

        print(f"Entrada procesada. ID temporal: {v_id_lote}")
        print("Cantidad: 1000 gramos de pollo")
        print("Sucursal: Oakland Mall")

    finally:
        v_conexion.rollback()
        v_conexion.close()

    print("ROLLBACK ejecutado. Entrada no guardada.")


if __name__ == "__main__":
    main()
