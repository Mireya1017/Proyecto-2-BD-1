from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.sesion import crear_sesion
from funcionalidades_py.transacciones import establecer_usuario_bitacora


v_sesion = crear_sesion(
    p_id_usuario=1,
    p_rol="gerente",
    p_id_sucursal=2
)

with obtener_conexion() as v_conexion:
    establecer_usuario_bitacora(v_conexion, v_sesion)

    with v_conexion.cursor() as v_cursor:
        v_cursor.execute(
            "SELECT current_setting('app.id_usuario', true);"
        )
        v_usuario = v_cursor.fetchone()[0]

        print("Usuario dentro de la transacción:", v_usuario)

    v_conexion.rollback()

    # Esta consulta inicia otra transacción.
    with v_conexion.cursor() as v_cursor:
        v_cursor.execute(
            "SELECT NULLIF(current_setting('app.id_usuario', true), '');"
        )
        v_usuario = v_cursor.fetchone()[0]

        print("Usuario después del rollback:", v_usuario)