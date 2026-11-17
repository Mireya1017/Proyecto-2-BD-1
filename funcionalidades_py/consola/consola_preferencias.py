# -----------------------------------------------------------
# Consola de las preferencias
# -----------------------------------------------------------

from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.preferencias import (
    agregar_preferencia,
    consultar_preferencias
)


def opcion_agregar_preferencia(p_sesion):
    print("\n--- AGREGAR PREFERENCIA ---")

    try:
        id_cliente = int(input("ID del cliente: "))
        id_plato = int(input("ID del plato favorito: "))

        datos = {
            "id_cliente": id_cliente,
            "id_plato": id_plato
        }

        resultado = ejecutar_transaccion(
            p_sesion,
            agregar_preferencia,
            datos
        )

        print(resultado)

    except ValueError as v_error:
        print(f"No se pudo agregar la preferencia: {v_error}")

    except Exception as error:
        print(f"No se pudo agregar la preferencia: {error}")


def opcion_consultar_preferencias(p_sesion):
    print("\n--- CONSULTAR PREFERENCIAS ---")

    try:
        id_cliente = int(input("ID del cliente: "))

        preferencias = ejecutar_transaccion(
            p_sesion,
            consultar_preferencias,
            {"id_cliente": id_cliente}
        )

        if not preferencias:
            print("El cliente no tiene preferencias registradas.")
            return

        print("\nPLATOS FAVORITOS:")

        for plato in preferencias:
            print(
                f"ID: {plato[0]} | "
                f"Plato: {plato[1]} | "
                f"Precio: Q{plato[2]:.2f}"
            )

    except ValueError as v_error:
        print(f"No se pudo agregar la preferencia: {v_error}")

    except Exception as error:
        print(f"Error al consultar preferencias: {error}")


def menu_preferencias(p_sesion):
    while True:
        print("\n===== MENÚ DE PREFERENCIAS =====")
        print("1. Agregar plato favorito")
        print("2. Consultar platos favoritos")
        print("0. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            opcion_agregar_preferencia(p_sesion)

        elif opcion == "2":
            opcion_consultar_preferencias(p_sesion)

        elif opcion == "0":
            break

        else:
            print("Opción inválida. Intente nuevamente.")

# FIN DEL CÓDIGO :)