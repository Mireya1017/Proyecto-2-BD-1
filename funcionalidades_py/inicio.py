from getpass import getpass

from funcionalidades_py.usuarios import (
    iniciar_sesion,
    cerrar_sesion,
    registrar_primer_administrador,
    listar_sucursales
)
from funcionalidades_py.menu_principal import menu_principal

def preparar_primer_administrador():
    print("\n--- CREAR PRIMER ADMINISTRADOR ---")

    for v_sucursal in listar_sucursales():
        print(
            f"ID: {v_sucursal['id_sucursal']} | "
            f"{v_sucursal['nombre']}"
        )

    v_nombre = input("Nombre de usuario: ").strip()
    v_contrasena = getpass("Contraseña: ")
    v_confirmacion = getpass("Repita la contraseña: ")

    if v_contrasena != v_confirmacion:
        raise ValueError("Las contraseñas no coinciden.")

    v_sucursal = int(input("ID de sucursal habitual: "))

    v_id = registrar_primer_administrador(
        v_nombre,
        v_contrasena,
        v_sucursal
    )

    print(f"Administrador creado con ID: {v_id}")
    print("Ahora puede iniciar sesión.")

def iniciar_programa():
    while True:
        print("\n===== ACCESO AL RESTAURANTE =====")
        print("1. Iniciar sesión")
        print("2. Crear primer administrador")
        print("0. Salir")

        v_opcion = input("Seleccione una opción: ").strip()

        if v_opcion == "0":
            break
        
        if v_opcion == "2":
            try:
                preparar_primer_administrador()
            except Exception as v_error:
                print(f"No se pudo crear el administrador: {v_error}")
            continue

        if v_opcion != "1":
            print("Opción inválida.")
            continue

        v_nombre = input("Nombre de usuario: ").strip()
        v_contrasena = getpass("Contraseña: ")

        try:
            v_sesion = iniciar_sesion(v_nombre, v_contrasena)
        except Exception as v_error:
            print(f"No se pudo iniciar sesión: {v_error}")
            continue

        print(f"\nBienvenido: {v_sesion['nombre_usuario']}")

        try:
            menu_principal(v_sesion)
        finally:
            cerrar_sesion(v_sesion)


if __name__ == "__main__":
    iniciar_programa()