from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.historial import obtener_historial_cliente


def opcion_consultar_historial(p_sesion):
    print("\n===== HISTORIAL DEL CLIENTE =====")

    try:
        id_cliente = int(input("Ingrese el ID del cliente: "))

        if id_cliente <= 0:
            print("El ID debe ser mayor que cero.")
            return

        historial = ejecutar_transaccion(
            p_sesion,
            obtener_historial_cliente,
            {"id_cliente": id_cliente}
        )

        print(f"\nHistorial del cliente ID: {id_cliente}")

        # VISITAS
        print("\n--- VISITAS ---")

        visitas = historial["visitas"]

        if not visitas:
            print("No tiene visitas registradas.")
        else:
            for visita in visitas:
                print(f"\nVisita ID: {visita[0]}")
                print(f"Llegada: {visita[1]}")
                print(f"Salida: {visita[2] or 'Sin registrar'}")
                print(f"Personas: {visita[3]}")
                print(f"Observaciones: {visita[4] or 'Ninguna'}")
                print(f"Reserva asociada: {visita[5] or 'Sin reserva'}")
                print(f"Sucursal ID: {visita[6]}")

        # RESERVAS
        print("\n--- RESERVAS ---")

        reservas = historial["reservas"]

        if not reservas:
            print("No tiene reservas registradas.")
        else:
            for reserva in reservas:
                print(f"\nReserva ID: {reserva[0]}")
                print(f"Inicio: {reserva[1]}")
                print(f"Fin estimado: {reserva[2]}")
                print(f"Personas: {reserva[3]}")
                print(f"Estado: {reserva[4]}")
                print(f"Sucursal ID: {reserva[5]}")

        # PREFERENCIAS
        print("\n--- PLATOS FAVORITOS ---")

        preferencias = historial["preferencias"]

        if not preferencias:
            print("No tiene platos favoritos registrados.")
        else:
            for plato in preferencias:
                print(f"{plato[1]} - Q{plato[2]:.2f}")

    except ValueError as v_error:
        print(f"No se pudo consultar el historial: {v_error}")

    except Exception as error:
        print(f"No se pudo consultar el historial: {error}")


def menu_historial(p_sesion):
    while True:
        print("\n===== MENÚ DE HISTORIAL =====")
        print("1. Consultar historial de un cliente")
        print("0. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            opcion_consultar_historial(p_sesion)

        elif opcion == "0":
            break

        else:
            print("Opción inválida. Intente nuevamente.")
