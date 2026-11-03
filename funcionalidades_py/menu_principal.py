# -----------------------------------------------------------
# El punto central de la navegación
# -----------------------------------------------------------

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

def menu_principal(p_sesion):
    rol = p_sesion["rol"]

    if rol not in ("administrador", "gerente", "mesero"):
        raise PermissionError("Rol de usuario no válido.")

    while True:
        print("\n" + "=" * 45)
        print("       SISTEMA DE RESTAURANTE")
        print("=" * 45)

        print(f"Usuario ID: {p_sesion['id_usuario']}")
        print(f"Rol: {rol}")
        print(f"Sucursal ID: {p_sesion['id_sucursal']}")

        print("\n===== MENÚ PRINCIPAL =====")
        print("1. Gestión de clientes")
        print("2. Preferencias de clientes")
        print("3. Historial de clientes")
        print("5. Gestión de visitas")
        print("7. Gestión de reservas")

        if rol == "administrador":
            print("4. Reportes de clientes")
            print("6. Gestión de usuarios")
            print("8. Administración")

        print("0. Cerrar sesión")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            menu_clientes(p_sesion)

        elif opcion == "2":
            menu_preferencias(p_sesion)

        elif opcion == "3":
            menu_historial(p_sesion)

        elif opcion == "4" and rol == "administrador":
            menu_reportes_clientes(p_sesion)
        
        elif opcion == "5":
            menu_visitas(p_sesion)
        
        elif opcion == "6" and rol == "administrador":
            menu_usuarios(p_sesion)
        
        elif opcion == "7":
            menu_reservas(p_sesion)
        
        elif opcion == "8" and rol == "administrador":
            menu_administracion(p_sesion)

        elif opcion == "0":
            print("\nRegresando al inicio de sesión...")
            break

        else:
            print("Opción inválida o sin permiso.")

# Fin del código