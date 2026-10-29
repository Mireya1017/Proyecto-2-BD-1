def crear_sesion(p_id_usuario, p_rol, p_id_sucursal):
    if p_rol not in ("administrador", "gerente", "mesero"):
        raise ValueError("El rol del usuario no es válido.")

    v_sesion = {
        "id_usuario": p_id_usuario,
        "rol": p_rol,
        "id_sucursal": p_id_sucursal
    }

    return v_sesion