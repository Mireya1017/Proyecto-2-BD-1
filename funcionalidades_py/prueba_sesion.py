from funcionalidades_py.sesion import crear_sesion


v_sesion = crear_sesion(
    p_id_usuario=1,
    p_rol="gerente",
    p_id_sucursal=2
)

print("Usuario:", v_sesion["id_usuario"])
print("Rol:", v_sesion["rol"])
print("Sucursal:", v_sesion["id_sucursal"])