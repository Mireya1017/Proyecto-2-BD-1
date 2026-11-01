from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.sesion import crear_sesion
from funcionalidades_py.menu_principal import menu_principal


if __name__ == "__main__":
    with obtener_conexion() as v_conexion:
        with v_conexion.cursor() as v_cursor:
            v_cursor.execute(
                """
                SELECT id_usuario, rol, id_sucursal
                FROM usuario
                WHERE nombre_usuario = %s;
                """,
                ("prueba_revision_yu",)
            )

            v_usuario = v_cursor.fetchone()

    if v_usuario is None:
        raise ValueError("Primero debe crear el usuario de prueba.")

    v_sesion = crear_sesion(
        v_usuario[0],
        v_usuario[1],
        v_usuario[2]
    )

    print("MODO DE PRUEBA: sesión sin autenticación.")
    menu_principal(v_sesion)