# funcionalidades_py/prueba_pablo.py
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.usuarios import (
    registrar_primer_administrador,
    iniciar_sesion,
    listar_usuarios,
)
from funcionalidades_py.reservas import (
    consultar_mesas_disponibles,
    registrar_reserva,
    modificar_reserva,
    cancelar_reserva,
    buscar_reservas,
    obtener_reservas_por_cliente,
)
from funcionalidades_py.administracion import (
    consultar_bitacora,
    generar_reporte_sucursales,
)


def ejecutar_pruebas_pablo():
    print("=== 1. PRUEBA DE PRIMER ADMINISTRADOR Y SESIÓN ===")
    try:
        v_id_admin = registrar_primer_administrador("admin_pablo", "Admin1234", 1)
        print(f"Primer admin creado con ID: {v_id_admin}")
    except Exception as v_e:
        print(f"Validación primer admin: {v_e}")

    v_sesion = iniciar_sesion("admin_pablo", "Admin1234")
    print("Sesión autenticada:", v_sesion)
    print("Usuarios registrados:", listar_usuarios(v_sesion))

    print("\n=== 2. ASEGURAR CLIENTE DE PRUEBA ===")
    with obtener_conexion() as v_con:
        with v_con.cursor() as v_cur:
            v_cur.execute("SELECT id_cliente FROM cliente ORDER BY id_cliente LIMIT 1;")
            v_fila = v_cur.fetchone()
            if not v_fila:
                v_cur.execute(
                    """
                    INSERT INTO cliente (nombre, telefono)
                    VALUES (%s, %s)
                    RETURNING id_cliente;
                    """,
                    ("Cliente Prueba Pablo", "5555-1234"),
                )
                v_id_cliente = v_cur.fetchone()[0]
                v_con.commit()
            else:
                v_id_cliente = v_fila[0]
    print(f"Usando id_cliente = {v_id_cliente}")

    print("\n=== 3. DISPONIBILIDAD Y REGISTRO DE RESERVA EN TRANSACCIÓN ===")
    v_inicio = "2026-11-15 13:00:00"
    v_fin = "2026-11-15 15:00:00"
    v_mesas = consultar_mesas_disponibles(1, v_inicio, v_fin, "interior")
    print(f"Mesas disponibles antes de reservar: {len(v_mesas)}")

    v_id_mesa = v_mesas[0]["id_mesa"]
    v_id_reserva = registrar_reserva(
        v_sesion,
        {
            "id_cliente": v_id_cliente,
            "id_sucursal": 1,
            "fecha_hora_inicio": v_inicio,
            "fecha_hora_fin_estimada": v_fin,
            "cantidad_personas": 2,
            "ids_mesas": [v_id_mesa],
        },
    )
    print(f"Reserva creada con ID: #{v_id_reserva} en mesa ID {v_id_mesa}")

    v_mesas_despues = consultar_mesas_disponibles(1, v_inicio, v_fin, "interior")
    print(f"Mesas disponibles en el mismo horario tras reservar: {len(v_mesas_despues)}")

    print("\n=== 4. REPORTE DE SUCURSALES (CON RESERVA ACTIVA) ===")
    print(generar_reporte_sucursales(v_sesion, p_id_sucursal=1))

    print("\n=== 5. MODIFICACIÓN Y CANCELACIÓN DE RESERVA ===")
    # 5.1 Prueba de rechazo por capacidad insuficiente (regla de negocio)
    try:
        modificar_reserva(
            v_sesion,
            {
                "id_reserva": v_id_reserva,
                "cantidad_personas": 3,
            },
        )
    except ValueError as v_err:
        print(f"[OK - Rechazo esperado]: {v_err}")

    # 5.2 Modificación válida: subir a 3 personas asignando una segunda mesa disponible de la misma zona
    v_segunda_mesa = v_mesas[1]["id_mesa"]
    modificar_reserva(
        v_sesion,
        {
            "id_reserva": v_id_reserva,
            "cantidad_personas": 3,
            "ids_mesas": [v_id_mesa, v_segunda_mesa],
        },
    )
    print(
        f"Reserva #{v_id_reserva} modificada exitosamente a 3 personas "
        f"con las mesas ID {[v_id_mesa, v_segunda_mesa]}."
    )

    cancelar_reserva(v_sesion, v_id_reserva)
    print(f"Reserva #{v_id_reserva} cancelada (conservando mesas históricas).")
    print("Historial del cliente:", obtener_reservas_por_cliente(v_id_cliente)[:1])

    print("\n=== 6. CONSULTA DE BITÁCORA (AUDITORÍA CON ID_USUARIO REAL) ===")
    for v_b in consultar_bitacora(v_sesion, {"limite": 8}):
        print(
            f"  [{v_b['id_bitacora']}] {v_b['fecha_hora']} | "
            f"usuario={v_b['nombre_usuario']} (ID:{v_b['id_usuario']}) | "
            f"{v_b['tabla']} | {v_b['operacion']} | {v_b['registro']}"
        )


if __name__ == "__main__":
    ejecutar_pruebas_pablo()