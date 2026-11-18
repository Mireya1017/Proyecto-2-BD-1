#!/usr/bin/env python3
"""Script CLI para inicializar al primer administrador del restaurante."""

import sys
import getpass
from app.config import DB_CONFIG
from app.database import inicializar_pool, cerrar_pool, transaccion
from app.usuarios import contar_usuarios, registrar_primer_administrador


def main():
    print("=" * 65)
    print("  RESTAURANTE - CONFIGURACIÓN INICIAL DEL PRIMER ADMINISTRADOR")
    print("=" * 65)
    print(f"Base de datos: {DB_CONFIG.get_dsn_safe()}\n")

    try:
        inicializar_pool()
        total = contar_usuarios()
        if total > 0:
            print(f"[AVISO] Ya existen {total} usuario(s) en la base de datos.")
            print("El primer administrador solo puede crearse cuando la base está vacía.")
            sys.exit(0)

        with transaccion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_sucursal, nombre FROM sucursal ORDER BY id_sucursal;")
                sucursales = cur.fetchall()

        if not sucursales:
            print("[ERROR] No hay sucursales registradas. Ejecute primero bd/datos_iniciales.sql.")
            sys.exit(1)

        print("Sucursales disponibles:")
        for sid, sname in sucursales:
            print(f"  [{sid}] {sname}")
        print()

        nombre_usuario = input("Nombre de usuario para el administrador: ").strip()
        if not nombre_usuario:
            print("[ERROR] El usuario no puede estar vacío.")
            sys.exit(1)

        contrasena = getpass.getpass("Contraseña: ")
        if len(contrasena) < 6:
            print("[ERROR] La contraseña debe tener al menos 6 caracteres.")
            sys.exit(1)

        confirmacion = getpass.getpass("Confirme la contraseña: ")
        if contrasena != confirmacion:
            print("[ERROR] Las contraseñas no coinciden.")
            sys.exit(1)

        sucursal_input = input(f"ID de sucursal habitual [{sucursales[0][0]}]: ").strip()
        id_sucursal = int(sucursal_input) if sucursal_input else sucursales[0][0]

        id_creado = registrar_primer_administrador(nombre_usuario, contrasena, id_sucursal)
        print(f"\n[ÉXITO] Administrador registrado correctamente con ID #{id_creado}.")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    finally:
        cerrar_pool()


if __name__ == "__main__":
    main()
