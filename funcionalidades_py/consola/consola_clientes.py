# -----------------------------------------------------------
# Consola para hacer inputs y prints (ingresar
# datos y mostrarlos) sobre los clientes
# -----------------------------------------------------------

from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.clientes import (
    registrar_cliente,
    buscar_clientes,
    obtener_cliente
)


def opcion_registrar_cliente(p_sesion):
    print("\n--- REGISTRAR CLIENTE ---")

    nombre = input("Nombre: ").strip()
    telefono = input("Teléfono (opcional): ").strip()

    datos = {
        "nombre": nombre,
        "telefono": telefono
    }

    try:
        id_cliente = ejecutar_transaccion(
            p_sesion,
            registrar_cliente,
            datos
        )

        print(f"Cliente registrado con ID: {id_cliente}")

    except Exception as error:
        print(f"No se pudo registrar el cliente: {error}")



def opcion_buscar_clientes(p_sesion):
    print("\n--- BUSCAR CLIENTES ---")

    nombre = input("Nombre a buscar: ").strip()

    try:
        clientes = ejecutar_transaccion(
            p_sesion,
            buscar_clientes,
            {"nombre": nombre}
        )

        if not clientes:
            print("No se encontraron clientes.")
            return

        print("\nRESULTADOS:")

        for cliente in clientes:
            print(
                f"ID: {cliente[0]} | "
                f"Nombre: {cliente[1]} | "
                f"Teléfono: {cliente[2] or 'Sin teléfono'}"
            )

    except Exception as error:
        print(f"Error al buscar clientes: {error}")


def opcion_consultar_cliente(p_sesion):
    print("\n--- CONSULTAR CLIENTE ---")

    try:
        id_cliente = int(input("ID del cliente: "))

        cliente = ejecutar_transaccion(
            p_sesion,
            obtener_cliente,
            {"id_cliente": id_cliente}
        )

        if cliente is None:
            print("El cliente no existe.")
            return

        print(f"\nID: {cliente[0]}")
        print(f"Nombre: {cliente[1]}")
        print(f"Teléfono: {cliente[2] or 'Sin teléfono'}")

    except ValueError:
        print("Debes ingresar un ID numérico.")

    except Exception as error:
        print(f"Error al consultar cliente: {error}")


def menu_clientes(p_sesion):
    while True:
        print("\n===== MENÚ DE CLIENTES =====")
        print("1. Registrar cliente")
        print("2. Buscar clientes")
        print("3. Consultar cliente por ID")
        print("0. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            opcion_registrar_cliente(p_sesion)

        elif opcion == "2":
            opcion_buscar_clientes(p_sesion)

        elif opcion == "3":
            opcion_consultar_cliente(p_sesion)

        elif opcion == "0":
            break

        else:
            print("Opción inválida. Intente nuevamente.")

# FIN DEL CÓDIGO :)