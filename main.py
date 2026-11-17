#!/usr/bin/env python3
"""
Punto de Entrada Principal - Consola de Operaciones de Pablo (Integrante 2).
"""

import sys
import getpass
from app.config import DB_CONFIG
from app.database import inicializar_pool, cerrar_pool, ErrorAutenticacion
from app.usuarios import contar_usuarios, iniciar_sesion
from app.auth import SesionUsuario
from app.consola import obtener_opciones_menu_pablo


def mostrar_encabezado_sesion(sesion: SesionUsuario) -> None:
    print("=" * 65)
    print("      SISTEMA DE GESTIÓN DE RESTAURANTE - CONSOLA PRINCIPAL")
    print("=" * 65)
    print(f" Usuario : {sesion.nombre_usuario}")
    print(f" Rol     : {sesion.rol.upper()}")
    print(f" Sucursal: ID #{sesion.id_sucursal}")
    print("=" * 65)


def autenticar_usuario() -> SesionUsuario:
    while True:
        print("\n" + "=" * 50)
        print("            INICIO DE SESIÓN")
        print("=" * 50)
        try:
            total = contar_usuarios()
            if total == 0:
                print("\n[AVISO] No hay usuarios registrados en el sistema.")
                print("Por favor ejecute primero: python setup_admin.py")
                sys.exit(0)
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
            print(f"Revise su configuración en el archivo .env ({DB_CONFIG.get_dsn_safe()})")
            sys.exit(1)

        usuario = input("Nombre de usuario: ").strip()
        if not usuario:
            continue

        contrasena = getpass.getpass("Contraseña: ")

        try:
            sesion = iniciar_sesion(usuario, contrasena)
            print(f"\n[ÉXITO] ¡Bienvenido/a {sesion.nombre_usuario}!")
            return sesion
        except ErrorAutenticacion as ea:
            print(f"\n[ERROR] {ea}")
            reintentar = input("¿Desea reintentar? (S/n): ").strip().lower()
            if reintentar == 'n':
                print("Saliendo del sistema...")
                sys.exit(0)


def main():
    try:
        inicializar_pool()
        sesion = autenticar_usuario()

        while True:
            mostrar_encabezado_sesion(sesion)
            opciones_dict = obtener_opciones_menu_pablo(sesion)

            lista_claves = list(opciones_dict.keys())
            for idx, key in enumerate(lista_claves, 1):
                titulo, _ = opciones_dict[key]
                print(f"  {idx}. {titulo}")

            print("  9. Cerrar sesión")
            print("  0. Salir de la aplicación")
            print("-" * 65)

            opcion = input("Seleccione una opción: ").strip()

            if opcion == "0":
                print("\nSaliendo del sistema. ¡Hasta pronto!")
                break
            elif opcion == "9":
                print("\nCerrando sesión...")
                sesion = autenticar_usuario()
            elif opcion.isdigit():
                indice = int(opcion) - 1
                if 0 <= indice < len(lista_claves):
                    clave_sel = lista_claves[indice]
                    _, funcion = opciones_dict[clave_sel]
                    funcion(sesion)
                else:
                    print("[AVISO] Opción no válida.")
            else:
                print("[AVISO] Entrada no reconocida.")

    except KeyboardInterrupt:
        print("\n\nEjecución interrumpida por el usuario.")
    except Exception as e:
        print(f"\n[FATAL] Error inesperado en la aplicación: {e}")
    finally:
        cerrar_pool()


if __name__ == "__main__":
    main()
