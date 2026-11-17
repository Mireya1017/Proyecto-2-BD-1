from funcionalidades_py.sesion import crear_sesion
from funcionalidades_py.transacciones import ejecutar_transaccion


def buscar_sucursal(p_conexion, p_sesion, p_datos):
    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(
            """
            SELECT id_sucursal, nombre, direccion
            FROM sucursal
            WHERE nombre = %s;
            """,
            (p_datos["nombre"],)
        )

        return v_cursor.fetchone()


# Sesión de ejemplo para una prueba de solo lectura.
v_sesion = crear_sesion(
    p_id_usuario=1,
    p_rol="administrador",
    p_id_sucursal=1
)

v_datos = {
    "nombre": "Oakland Mall"
}

v_resultado = ejecutar_transaccion(
    v_sesion,
    buscar_sucursal,
    v_datos
)

print("Sucursal encontrada:", v_resultado)

def provocar_error(p_conexion, p_sesion, p_datos):
    with p_conexion.cursor() as v_cursor:
        v_cursor.execute("SELECT 1 / 0;")


try:
    ejecutar_transaccion(
        v_sesion,
        provocar_error,
        {}
    )

except Exception as v_error:
    print("Error de prueba capturado:", v_error)


v_resultado = ejecutar_transaccion(
    v_sesion,
    buscar_sucursal,
    v_datos
)

print("Consulta posterior al error:", v_resultado)