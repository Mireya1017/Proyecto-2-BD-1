
from datetime import date, timedelta
from getpass import getpass

from funcionalidades_py.usuarios import iniciar_sesion
from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.inventario import registrar_entrada


def main():
    print("\n===== ENTRADA REAL DE INVENTARIO =====")

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

    print("\nEntrada a registrar:")
    print("Insumo: Pollo")
    print("Sucursal: Oakland Mall")
    print("Cantidad: 1000 gramos")

    v_confirmacion = input(
        "\nConfirmar registro (SI/NO): "
    ).strip().upper()

    if v_confirmacion != "SI":
        print("Operacion cancelada.")
        return

    v_id_lote = ejecutar_transaccion(
        v_sesion,
        registrar_entrada,
        v_datos
    )

    print("\nENTRADA REGISTRADA CORRECTAMENTE")
    print(f"ID del nuevo lote: {v_id_lote}")


if __name__ == "__main__":
    main()
