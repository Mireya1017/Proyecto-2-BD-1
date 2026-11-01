import hashlib
import secrets

from funcionalidades_py.conexion import obtener_conexion


with obtener_conexion() as v_conexion:
    with v_conexion.cursor() as v_cursor:
        v_cursor.execute(
            """
            SELECT id_sucursal
            FROM sucursal
            WHERE nombre = %s;
            """,
            ("Oakland Mall",)
        )

        v_sucursal = v_cursor.fetchone()

        if v_sucursal is None:
            raise ValueError("No existe la sucursal Oakland Mall.")

        # Contraseña aleatoria: este usuario se utilizará
        # mediante una sesión de prueba, sin iniciar sesión.
        v_sal = secrets.token_bytes(16)
        v_clave = secrets.token_bytes(32)

        v_hash = hashlib.pbkdf2_hmac(
            "sha256", v_clave, v_sal, 600000
        )

        v_hash_guardado = (
            f"pbkdf2_sha256$600000${v_sal.hex()}${v_hash.hex()}"
        )

        v_cursor.execute(
            """
            INSERT INTO usuario (
                nombre_usuario,
                contrasena_hash,
                rol,
                id_sucursal
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (nombre_usuario) DO NOTHING;
            """,
            (
                "prueba_revision_yu",
                v_hash_guardado,
                "administrador",
                v_sucursal[0]
            )
        )

        v_cursor.execute(
            """
            SELECT id_usuario, nombre_usuario, rol, id_sucursal
            FROM usuario
            WHERE nombre_usuario = %s;
            """,
            ("prueba_revision_yu",)
        )

        print("Usuario para pruebas:", v_cursor.fetchone())