
# =====================================================
# CONSOLA DE INVENTARIO Y VENTAS
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from funcionalidades_py.inventario import (
    consultar_existencias,
    consultar_lotes,
    consultar_alertas_existencias,
    consultar_alertas_caducidad
)
from funcionalidades_py.inventario import registrar_entrada
from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.ventas import registrar_venta, consultar_menu
from funcionalidades_py.reportes_nathalie import (
    reporte_top_productos,
    reporte_caducidades_mensual
)


def validar_acceso_inventario(p_sesion):
    """
    Comprueba los permisos del modulo de inventario.
    """

    if not isinstance(p_sesion, dict):
        raise PermissionError("Se requiere una sesion valida.")

    if p_sesion.get("rol") not in ("administrador", "gerente"):
        raise PermissionError(
            "No tiene permisos para consultar inventario."
        )

    if p_sesion.get("id_usuario") is None:
        raise PermissionError("Se requiere una sesion autenticada.")

    if p_sesion.get("id_sucursal") is None:
        raise PermissionError("La sesion no tiene sucursal.")


def seleccionar_sucursal(p_sesion):
    """
    Obtiene la sucursal autorizada para el usuario.
    """

    validar_acceso_inventario(p_sesion)

    if p_sesion["rol"] == "administrador":
        return int(input("Ingrese ID de sucursal: "))

    return int(p_sesion["id_sucursal"])


def mostrar_existencias(p_sesion):
    v_sucursal = seleccionar_sucursal(p_sesion)
    v_resultados = consultar_existencias(v_sucursal, p_sesion)

    print("\n===== EXISTENCIAS DE INVENTARIO =====")

    if not v_resultados:
        print("No hay insumos registrados.")
        return

    for v_fila in v_resultados:
        print(
            f"{v_fila[1]} | "
            f"Disponible: {v_fila[4]} {v_fila[2]} | "
            f"Minimo: {v_fila[3]}"
        )


def mostrar_lotes(p_sesion):
    v_sucursal = seleccionar_sucursal(p_sesion)
    v_insumo = int(input("Ingrese ID del insumo: "))

    v_resultados = consultar_lotes(v_sucursal, v_insumo, p_sesion)

    print("\n===== LOTES DE INVENTARIO =====")

    if not v_resultados:
        print("No se encontraron lotes.")
        return

    for v_fila in v_resultados:
        print(
            f"Lote: {v_fila[0]} | "
            f"Caducidad: {v_fila[2]} | "
            f"Cantidad: {v_fila[3]} {v_fila[4]} | "
            f"Estado: {v_fila[5]}"
        )


def mostrar_alertas(p_sesion):
    v_sucursal = seleccionar_sucursal(p_sesion)

    print("\n===== ALERTAS DE EXISTENCIAS =====")

    v_alertas = consultar_alertas_existencias(v_sucursal, p_sesion)

    if not v_alertas:
        print("No hay insumos por debajo del minimo.")
    else:
        for v_fila in v_alertas:
            print(
                f"{v_fila[0]} | "
                f"Disponible: {v_fila[3]} {v_fila[1]} | "
                f"Minimo: {v_fila[2]}"
            )

    print("\n===== ALERTAS DE CADUCIDAD =====")

    # Ventana provisional de siete dias.
    v_caducidades = consultar_alertas_caducidad(
        v_sucursal, 7, p_sesion=p_sesion
    )

    if not v_caducidades:
        print("No hay lotes proximos a caducar.")
    else:
        for v_fila in v_caducidades:
            print(
                f"{v_fila[0]} | "
                f"Lote: {v_fila[1]} | "
                f"Caducidad: {v_fila[2]} | "
                f"Dias restantes: {v_fila[5]}"
            )

def mostrar_registro_entrada(p_sesion):
    """
    Solicita los datos de una entrada de inventario
    y ejecuta su registro en PostgreSQL.
    """

    validar_acceso_inventario(p_sesion)

    print("\n===== REGISTRAR ENTRADA DE INVENTARIO =====")

    v_sucursal = seleccionar_sucursal(p_sesion)

    v_datos = {
        "id_insumo": int(input("ID del insumo: ")),
        "id_sucursal": v_sucursal,
        "fecha_recepcion": input(
            "Fecha de recepcion (AAAA-MM-DD): "
        ).strip(),
        "fecha_caducidad": input(
            "Fecha de caducidad (AAAA-MM-DD): "
        ).strip(),
        "cantidad": input(
            "Cantidad recibida: "
        ).strip()
    }

    v_id_lote = ejecutar_transaccion(
        p_sesion,
        registrar_entrada,
        v_datos
    )

    print(f"\nEntrada registrada. ID del lote: {v_id_lote}")


# =====================================================
# REGISTRO DE VENTAS DESDE CONSOLA
# Responsable: Nathalie
# =====================================================

def mostrar_registro_venta(p_sesion):
    """
    Permite registrar una venta desde consola.

    Utiliza la operacion transaccional registrar_venta
    y la conexion compartida del proyecto.
    """

    if p_sesion.get("rol") not in (
        "administrador", "gerente", "mesero"
    ):
        raise PermissionError(
            "No tiene permisos para registrar ventas."
        )

    print("\n===== REGISTRAR VENTA =====")

    # Mostrar productos disponibles
    v_menu = consultar_menu()

    if not v_menu:
        print("No hay productos disponibles.")
        return

    print("\nMENU DEL RESTAURANTE")

    for v_plato in v_menu:
        print(
            f"ID: {v_plato[0]} | "
            f"{v_plato[1]} | "
            f"Q{v_plato[2]:.2f}"
        )

    # Solicitar visita
    v_id_visita = int(input("\nID de la visita: "))

    # Solicitar productos
    v_cantidad_productos = int(
        input("Cantidad de productos diferentes: ")
    )

    if v_cantidad_productos <= 0:
        raise ValueError(
            "Debe seleccionar al menos un producto."
        )

    v_productos = []

    for v_numero in range(v_cantidad_productos):
        print(f"\nProducto {v_numero + 1}")

        v_id_plato = int(input("ID del plato: "))
        v_cantidad = int(input("Cantidad: "))

        v_productos.append({
            "id_plato": v_id_plato,
            "cantidad": v_cantidad
        })

    v_datos = {
        "id_visita": v_id_visita,
        "productos": v_productos
    }

    # Ejecutar toda la venta en una transaccion
    v_resultado = ejecutar_transaccion(
        p_sesion,
        registrar_venta,
        v_datos
    )

    print("\n===== VENTA REGISTRADA =====")
    print(f"ID de venta: {v_resultado['id_venta']}")
    print(f"ID de visita: {v_resultado['id_visita']}")
    print(f"Total: Q{v_resultado['total']:.2f}")

def menu_inventario(p_sesion):
    """
    Menu independiente para integracion con Yu-fong.
    """

    validar_acceso_inventario(p_sesion)

    while True:
        print("\n" + "=" * 45)
        print("       MODULO DE INVENTARIO")
        print("=" * 45)

        print("1. Consultar existencias")
        print("2. Consultar lotes")
        print("3. Consultar alertas")
        print("4. Registrar entrada de inventario")
        print("0. Regresar al menu principal")

        v_opcion = input("\nSeleccione una opcion: ").strip()

        try:
            if v_opcion == "1":
                mostrar_existencias(p_sesion)

            elif v_opcion == "2":
                mostrar_lotes(p_sesion)

            elif v_opcion == "3":
                mostrar_alertas(p_sesion)

            elif v_opcion == "4":
                mostrar_registro_entrada(p_sesion)

            elif v_opcion == "0":
                print("Regresando al menu principal...")
                break

            else:
                print("Opcion no valida.")

        except (ValueError, PermissionError) as v_error:
            print(f"Error: {v_error}")

        except Exception as v_error:
            print(f"Error al consultar inventario: {v_error}")

# =====================================================
# MENU DE VENTAS
# =====================================================

def menu_ventas(p_sesion):
    """
    Menu de ventas para integrar con el menu principal.
    """

    if p_sesion.get("rol") not in (
        "administrador", "gerente", "mesero"
    ):
        raise PermissionError(
            "No tiene permisos para acceder a ventas."
        )

    while True:
        print("\n" + "=" * 45)
        print("          MODULO DE VENTAS")
        print("=" * 45)

        print("1. Consultar menu")
        print("2. Registrar venta")
        print("0. Regresar al menu principal")

        v_opcion = input("\nSeleccione una opcion: ").strip()

        try:
            if v_opcion == "1":
                v_productos = consultar_menu()

                for v_producto in v_productos:
                    print(
                        f"{v_producto[1]} | "
                        f"Q{v_producto[2]:.2f}"
                    )

            elif v_opcion == "2":
                mostrar_registro_venta(p_sesion)

            elif v_opcion == "0":
                break

            else:
                print("Opcion no valida.")

        except (ValueError, PermissionError) as v_error:
            print(f"Error: {v_error}")

        except Exception as v_error:
            print(f"No se pudo completar la operacion: {v_error}")

# =====================================================
# MENU DE REPORTES DE NATHALIE
# Proyecto 02 - Base de Datos 1
# =====================================================

def menu_reportes_nathalie(p_sesion):
    """
    Presenta los reportes de ventas y caducidades.
    Acceso exclusivo para administradores.
    """

    if not isinstance(p_sesion, dict) or (
        p_sesion.get("rol") != "administrador"
    ):
        raise PermissionError(
            "Solo los administradores pueden consultar reportes."
        )

    while True:
        print("\n===== REPORTES DE INVENTARIO Y VENTAS =====")
        print("1. Top 10 de productos mas vendidos")
        print("2. Caducidades por mes y sucursal")
        print("3. Insumos bajo minimo (existencias actuales)")
        print("0. Regresar al menu principal")

        v_opcion = input("\nSeleccione una opcion: ").strip()

        try:
            if v_opcion == "1":
                v_resultados = reporte_top_productos(p_sesion)

                print("\n===== TOP 10 PRODUCTOS =====")

                if not v_resultados:
                    print("No hay ventas registradas.")

                for v_fila in v_resultados:
                    print(
                        f"{v_fila[1]} | "
                        f"Unidades: {v_fila[2]} | "
                        f"Ingresos: Q{v_fila[3]:.2f}"
                    )

            elif v_opcion == "2":
                v_anio = int(input("Anio (AAAA): "))
                v_mes = int(input("Mes (1-12): "))
                v_sucursal = int(
                    input("ID de sucursal: ")
                )

                v_resultados = reporte_caducidades_mensual(
                    p_sesion,
                    v_anio,
                    v_mes,
                    v_sucursal
                )

                print("\n===== CADUCIDADES MENSUALES =====")
                print(f"Periodo: {v_mes:02d}/{v_anio}")
                print(f"Sucursal ID: {v_sucursal}")

                if not v_resultados:
                    print("No hay lotes para este periodo.")

                for v_fila in v_resultados:
                    print(
                        f"{v_fila[1]} | "
                        f"Lote: {v_fila[2]} | "
                        f"Caducidad: {v_fila[3]} | "
                        f"Disponible actual: "
                        f"{v_fila[4]} {v_fila[5]}"
                    )

            elif v_opcion == "3":
                v_sucursal = int(input("ID de sucursal: "))
                v_filas = consultar_alertas_existencias(v_sucursal, p_sesion)
                print("Existencias actuales por debajo del minimo:")
                if not v_filas:
                    print("No hay alertas de existencias bajas.")
                for v_fila in v_filas:
                    print(f"{v_fila[0]}: {v_fila[3]} {v_fila[1]} (minimo {v_fila[2]})")

            elif v_opcion == "0":
                break

            else:
                print("Opcion no valida.")

        except (ValueError, PermissionError) as v_error:
            print(f"Error: {v_error}")

        except Exception as v_error:
            print(f"No se pudo generar el reporte: {v_error}")
            