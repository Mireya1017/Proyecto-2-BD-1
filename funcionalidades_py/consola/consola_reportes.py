from datetime import date, timedelta

from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.reportes_clientes import (
    top_clientes_frecuentes,
    top_clientes_reservas
)


def solicitar_periodo():
    print("\n--- SELECCIONAR PERÍODO ---")
    print("Formato: AAAA-MM-DD")

    inicio_texto = input("Fecha inicial: ").strip()
    fin_texto = input("Fecha final (inclusive): ").strip()

    try:
        fecha_inicio = date.fromisoformat(inicio_texto)
        fecha_fin = date.fromisoformat(fin_texto)

    except ValueError:
        raise ValueError(
            "Las fechas deben tener el formato AAAA-MM-DD "
            "y ser fechas válidas."
        )

    if fecha_inicio > fecha_fin:
        raise ValueError(
            "La fecha inicial no puede ser posterior a la final."
        )

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin + timedelta(days=1)
    }


def opcion_top_clientes_frecuentes(p_sesion):
    print("\n===== TOP 10 CLIENTES FRECUENTES =====")

    try:
        datos = solicitar_periodo()

        resultados = ejecutar_transaccion(
            p_sesion,
            top_clientes_frecuentes,
            datos
        )

        if not resultados:
            print("No hay visitas registradas en este período.")
            return

        print("\nPOSICIÓN | CLIENTE | TOTAL DE VISITAS")
        print("-" * 55)

        for posicion, cliente in enumerate(resultados, start=1):
            id_cliente = cliente[0]
            nombre = cliente[1]
            total = cliente[2]

            print(
                f"{posicion}. {nombre} "
                f"(ID: {id_cliente}) - {total} visitas"
            )

    except ValueError as error:
        print(f"Datos inválidos: {error}")

    except Exception as error:
        print(f"No se pudo generar el reporte: {error}")


def opcion_top_clientes_reservas(p_sesion):
    print("\n===== TOP 5 CLIENTES CON MÁS RESERVAS =====")

    try:
        datos = solicitar_periodo()

        resultados = ejecutar_transaccion(
            p_sesion,
            top_clientes_reservas,
            datos
        )

        if not resultados:
            print("No hay reservas para este período.")
            return

        for posicion, cliente in enumerate(resultados, start=1):
            print("\n" + "-" * 45)
            print(f"Posición: {posicion}")
            print(f"Cliente: {cliente['nombre']}")
            print(f"ID: {cliente['id_cliente']}")
            print(f"Total de reservas: {cliente['total_reservas']}")

            preferencias = cliente["preferencias"]

            if preferencias:
                print("Platos favoritos:")

                for plato in preferencias:
                    print(f"  - {plato}")
            else:
                print("Sin preferencias registradas.")

    except ValueError as error:
        print(f"Datos inválidos: {error}")

    except Exception as error:
        print(f"No se pudo generar el reporte: {error}")


def menu_reportes_clientes(p_sesion):
    if p_sesion["rol"] != "administrador":
        print("No tiene permiso para consultar reportes.")
        return

    while True:
        print("\n===== REPORTES DE CLIENTES =====")
        print("1. Top 10 de clientes frecuentes")
        print("2. Top 5 de clientes con más reservas")
        print("0. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            opcion_top_clientes_frecuentes(p_sesion)

        elif opcion == "2":
            opcion_top_clientes_reservas(p_sesion)

        elif opcion == "0":
            break

        else:
            print("Opción inválida. Intente nuevamente.")
