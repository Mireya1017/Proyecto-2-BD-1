from funcionalidades_py.conexion import obtener_conexion
def establecer_usuario_bitacora(p_conexion, p_sesion):
    v_id_usuario = str(p_sesion["id_usuario"])

    with p_conexion.cursor() as v_cursor:
        v_cursor.execute(
            "SELECT set_config('app.id_usuario', %s, true);",
            (v_id_usuario,)
        )
def ejecutar_transaccion(p_sesion, p_operacion, p_datos):
    v_conexion = obtener_conexion()

    try:
        establecer_usuario_bitacora(v_conexion, p_sesion)

        v_resultado = p_operacion(
            v_conexion,
            p_sesion,
            p_datos
        )

        v_conexion.commit()

        return v_resultado

    except Exception:
        v_conexion.rollback()
        raise

    finally:
        v_conexion.close()