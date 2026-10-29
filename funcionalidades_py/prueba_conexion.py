from funcionalidades_py.conexion import obtener_conexion


with obtener_conexion() as v_conexion:
    with v_conexion.cursor() as v_cursor:
        v_cursor.execute(
            "SELECT current_database(), current_user;"
        )

        v_resultado = v_cursor.fetchone()

        print("Conexión exitosa")
        print("Base de datos:", v_resultado[0])
        print("Usuario de PostgreSQL:", v_resultado[1])