from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.visitas import (
    registrar_visita,
    registrar_salida,
    liberar_mesa,
    consultar_mesas_disponibles
)

def opcion_registrar_visita(p_sesion):
    print("\n--- REGISTRAR LLEGADA ---")

    try:
        v_id_cliente = int(input("ID del cliente: "))

        if p_sesion["rol"] == "administrador":
            v_id_sucursal = int(input("ID de la sucursal: "))
        else:
            v_id_sucursal = p_sesion["id_sucursal"]

        v_personas = int(input("Cantidad de personas: "))

        v_reserva = input(
            "ID de reserva (dejar vacío si no tiene): "
        ).strip()

        v_id_reserva = int(v_reserva) if v_reserva else None

        v_disponibles = ejecutar_transaccion(
            p_sesion,
            consultar_mesas_disponibles,
            {
                "id_sucursal": v_id_sucursal,
                "id_reserva": v_id_reserva
            }
        )

        if not v_disponibles:
            print("No hay mesas disponibles en este momento.")
            return

        print("\n--- MESAS DISPONIBLES AHORA ---")

        for v_mesa in v_disponibles:
            print(
                f"ID: {v_mesa[0]} | "
                f"Mesa: {v_mesa[1]} | "
                f"Capacidad: {v_mesa[2]} | "
                f"Zona: {v_mesa[3]}"
            )

        print("Seleccione los IDs de las mesas que puede juntar.")

        v_texto_mesas = input(
            "IDs de mesas separados por coma (ejemplo: 1,2): "
        )

        v_mesas = [
            int(v_id.strip())
            for v_id in v_texto_mesas.split(",")
        ]

        v_observaciones = input(
            "Observaciones (opcional): "
        ).strip()

        v_datos = {
            "id_cliente": v_id_cliente,
            "id_sucursal": v_id_sucursal,
            "cantidad_personas": v_personas,
            "id_reserva": v_id_reserva,
            "mesas": v_mesas,
            "observaciones": v_observaciones or None
        }

        v_resultado = ejecutar_transaccion(
            p_sesion,
            registrar_visita,
            v_datos
        )

        print(f"Visita registrada con ID: {v_resultado}")

    except Exception as v_error:
        print(f"No se pudo registrar la visita: {v_error}")


def opcion_registrar_salida(p_sesion):
    print("\n--- REGISTRAR SALIDA ---")

    try:
        v_id_visita = int(input("ID de la visita: "))

        v_resultado = ejecutar_transaccion(
            p_sesion,
            registrar_salida,
            {"id_visita": v_id_visita}
        )

        print("Salida registrada:", v_resultado["fecha_hora_salida"])
        print("Las mesas deben liberarse después de limpiarlas.")

    except Exception as v_error:
        print(f"No se pudo registrar la salida: {v_error}")


def opcion_liberar_mesa(p_sesion):
    print("\n--- LIBERAR MESA ---")

    try:
        v_id_visita = int(input("ID de la visita: "))
        v_id_mesa = int(input("ID de la mesa: "))

        v_resultado = ejecutar_transaccion(
            p_sesion,
            liberar_mesa,
            {
                "id_visita": v_id_visita,
                "id_mesa": v_id_mesa
            }
        )

        print("Mesa liberada:", v_resultado["fecha_hora_liberacion"])

    except Exception as v_error:
        print(f"No se pudo liberar la mesa: {v_error}")


def menu_visitas(p_sesion):
    while True:
        print("\n===== MENÚ DE VISITAS =====")
        print("1. Registrar llegada")
        print("2. Registrar salida")
        print("3. Liberar mesa después de limpieza")
        print("0. Volver al menú principal")

        v_opcion = input("\nSeleccione una opción: ").strip()

        if v_opcion == "1":
            opcion_registrar_visita(p_sesion)
        elif v_opcion == "2":
            opcion_registrar_salida(p_sesion)
        elif v_opcion == "3":
            opcion_liberar_mesa(p_sesion)
        elif v_opcion == "0":
            break
        else:
            print("Opción inválida.")