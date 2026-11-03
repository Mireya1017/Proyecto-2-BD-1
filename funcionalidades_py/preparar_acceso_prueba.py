from getpass import getpass

from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.usuarios import generar_hash_contrasena


if __name__ == "__main__":
    v_contrasena = getpass("Nueva contraseña del usuario de prueba: ")
    v_confirmacion = getpass("Repita la contraseña: ")

    if v_contrasena != v_confirmacion:
        raise ValueError("Las contraseñas no coinciden.")

    v_hash = generar_hash_contrasena(v_contrasena)

    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(
                """
                SELECT id_usuario
                FROM usuario
                WHERE nombre_usuario = %s
                  AND rol = 'administrador';
                """,
                ("prueba_revision_yu",)
            )

            v_usuario = v_cursor.fetchone()

            if v_usuario is None:
                raise ValueError(
                    "No existe el administrador de prueba."
                )

            v_cursor.execute(
                "SELECT set_config('app.id_usuario', %s, true);",
                (str(v_usuario[0]),)
            )

            v_cursor.execute(
                """
                UPDATE usuario
                SET contrasena_hash = %s
                WHERE id_usuario = %s;
                """,
                (v_hash, v_usuario[0])
            )

    print("Contraseña del usuario de prueba actualizada.")