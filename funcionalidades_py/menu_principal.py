# Punto central de navegación

from funcionalidades_py.consola.consola_clientes import menu_clientes
from funcionalidades_py.consola.consola_preferencias import menu_preferencias
from funcionalidades_py.consola.consola_historial import menu_historial
from funcionalidades_py.consola.consola_reportes import menu_reportes_clientes
from funcionalidades_py.consola.consola_visitas import menu_visitas

from funcionalidades_py.consola.consola_pablo import (
    menu_usuarios,
    menu_reservas,
    menu_administracion
)

from funcionalidades_py.consola.consola_nathalie import (
    menu_inventario,
    menu_ventas,
    menu_reportes_nathalie
)


def menu_principal(p_sesion):
    v_rol = p_sesion["rol"]

    if v_rol not in ("administrador", "gerente", "mesero"):
        raise PermissionError("Rol de usuario no válido.")

    while True:
        print("\n" + "=" * 45)
        print("       SISTEMA DE RESTAURANTE")
        print("=" * 45)

        print(f"Usuario ID: {p_sesion['id_usuario']}")
        print(f"Rol: {v_rol}")
        print(f"Sucursal ID: {p_sesion['id_sucursal']}")

        print("\n===== MENÚ PRINCIPAL =====")
        print("1. Gestión de clientes")
        print("2. Preferencias de clientes")
        print("3. Historial de clientes")

        if v_rol == "administrador":
            print("4. Reportes de clientes")

        print("5. Gestión de visitas")

        if v_rol == "administrador":
            print("6. Gestión de usuarios")

        print("7. Gestión de reservas")

        if v_rol == "administrador":
            print("8. Administración")

        print("9. Ventas")

        if v_rol in ("administrador", "gerente"):
            print("10. Inventario")

        if v_rol == "administrador":
            print("11. Reportes de inventario y ventas")

        print("0. Cerrar sesión")

        v_opcion = input("\nSeleccione una opción: ").strip()

        if v_opcion == "1":
            menu_clientes(p_sesion)

        elif v_opcion == "2":
            menu_preferencias(p_sesion)

        elif v_opcion == "3":
            menu_historial(p_sesion)

        elif v_opcion == "4" and v_rol == "administrador":
            menu_reportes_clientes(p_sesion)

        elif v_opcion == "5":
            menu_visitas(p_sesion)

        elif v_opcion == "6" and v_rol == "administrador":
            menu_usuarios(p_sesion)

        elif v_opcion == "7":
            menu_reservas(p_sesion)

        elif v_opcion == "8" and v_rol == "administrador":
            menu_administracion(p_sesion)

        elif v_opcion == "9":
            menu_ventas(p_sesion)

        elif v_opcion == "10" and v_rol in ("administrador", "gerente"):
            menu_inventario(p_sesion)

        elif v_opcion == "11" and v_rol == "administrador":
            menu_reportes_nathalie(p_sesion)

        elif v_opcion == "0":
            print("\nRegresando al inicio de sesión...")
            break

        else:
            print("Opción inválida o sin permiso.")