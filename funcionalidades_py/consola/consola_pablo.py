from getpass import getpass
from funcionalidades_py.usuarios import (
    iniciar_sesion,
    cerrar_sesion,
    registrar_primer_administrador,
    registrar_usuario,
    listar_usuarios,
    listar_sucursales,
)
from funcionalidades_py.reservas import (
    consultar_mesas_disponibles,
    registrar_reserva,
    modificar_reserva,
    cancelar_reserva,
    op_cambiar_estado_reserva,
    buscar_reservas,
)
from funcionalidades_py.administracion import (
    consultar_bitacora,
    generar_reporte_sucursales,
)
from funcionalidades_py.transacciones import ejecutar_transaccion

def menu_usuarios(p_sesion):
    if p_sesion["rol"] != "administrador":
        raise PermissionError("Solo el administrador gestiona usuarios.")

    while True:
        print("\n===== GESTIÓN DE USUARIOS =====")
        print("1. Registrar usuario")
        print("2. Listar usuarios")
        print("0. Volver")

        v_opcion = input("Seleccione una opción: ").strip()

        if v_opcion == "0":
            break

        try:
            if v_opcion == "1":
                print("\nSUCURSALES:")

                for v_sucursal in listar_sucursales():
                    print(
                        f"ID: {v_sucursal['id_sucursal']} | "
                        f"{v_sucursal['nombre']}"
                    )

                v_nombre = input("Nombre de usuario: ").strip()
                v_contrasena = getpass("Contraseña: ")
                v_confirmacion = getpass("Repita la contraseña: ")

                if v_contrasena != v_confirmacion:
                    raise ValueError("Las contraseñas no coinciden.")

                v_rol = input(
                    "Rol (administrador, gerente o mesero): "
                ).strip().lower()

                v_sucursal = int(input("ID de sucursal: "))

                v_id_usuario = registrar_usuario(
                    p_sesion,
                    {
                        "nombre_usuario": v_nombre,
                        "contrasena": v_contrasena,
                        "rol": v_rol,
                        "id_sucursal": v_sucursal
                    }
                )

                print(f"Usuario registrado con ID: {v_id_usuario}")

            elif v_opcion == "2":
                for v_usuario in listar_usuarios(p_sesion):
                    print(
                        f"ID: {v_usuario['id_usuario']} | "
                        f"Usuario: {v_usuario['nombre_usuario']} | "
                        f"Rol: {v_usuario['rol']} | "
                        f"Sucursal: {v_usuario['sucursal']}"
                    )

            else:
                print("Opción inválida.")

        except Exception as v_error:
            print(f"No se pudo realizar la operación: {v_error}")
def opcion_registrar_reserva(p_sesion):
    print("\n--- REGISTRAR RESERVA ---")

    v_id_cliente = int(input("ID del cliente: "))

    if p_sesion["rol"] == "administrador":
        for v_sucursal in listar_sucursales():
            print(
                f"ID: {v_sucursal['id_sucursal']} | "
                f"{v_sucursal['nombre']}"
            )

        v_id_sucursal = int(input("ID de sucursal: "))
    else:
        v_id_sucursal = p_sesion["id_sucursal"]

    print("Formato de fecha y hora: AAAA-MM-DD HH:MM")
    v_inicio = input("Inicio: ").strip()
    v_fin = input("Fin estimado: ").strip()
    v_personas = int(input("Cantidad de personas: "))
    v_zona = input("Zona (interior o exterior): ").strip().lower()

    if v_personas <= 0:
        raise ValueError("La cantidad de personas debe ser mayor que cero.")

    if v_zona not in ("interior", "exterior"):
        raise ValueError("La zona debe ser interior o exterior.")

    v_mesas = consultar_mesas_disponibles(
        v_id_sucursal,
        v_inicio,
        v_fin,
        v_zona
    )

    if not v_mesas:
        print("No hay mesas disponibles para ese horario y zona.")
        return

    print("\nMESAS DISPONIBLES PARA EL HORARIO:")

    for v_mesa in v_mesas:
        print(
            f"ID: {v_mesa['id_mesa']} | "
            f"Mesa: {v_mesa['numero']} | "
            f"Capacidad: {v_mesa['capacidad']} | "
            f"Zona: {v_mesa['zona']}"
        )

    v_texto = input("IDs de mesas separados por coma: ")
    v_ids_mesas = [int(v_id.strip()) for v_id in v_texto.split(",")]

    v_id_reserva = registrar_reserva(
        p_sesion,
        {
            "id_cliente": v_id_cliente,
            "id_sucursal": v_id_sucursal,
            "fecha_hora_inicio": v_inicio,
            "fecha_hora_fin_estimada": v_fin,
            "cantidad_personas": v_personas,
            "ids_mesas": v_ids_mesas
        }
    )

    print(f"Reserva registrada con ID: {v_id_reserva}")

def opcion_modificar_reserva(p_sesion):
    v_datos = {
        "id_reserva": int(input("ID de reserva: "))
    }

    print("Deje vacío lo que desea conservar.")

    v_inicio = input("Nuevo inicio (AAAA-MM-DD HH:MM): ").strip()
    v_fin = input("Nuevo fin (AAAA-MM-DD HH:MM): ").strip()
    v_personas = input("Nueva cantidad de personas: ").strip()
    v_mesas = input("Nuevos IDs de mesas separados por coma: ").strip()

    if v_inicio:
        v_datos["fecha_hora_inicio"] = v_inicio

    if v_fin:
        v_datos["fecha_hora_fin_estimada"] = v_fin

    if v_personas:
        v_datos["cantidad_personas"] = int(v_personas)

    if v_mesas:
        v_datos["ids_mesas"] = [
            int(v_id.strip()) for v_id in v_mesas.split(",")
        ]

    modificar_reserva(p_sesion, v_datos)
    print("Reserva modificada correctamente.")

def menu_reservas(p_sesion):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para gestionar reservas.")

    while True:
        print("\n===== GESTIÓN DE RESERVAS =====")
        print("1. Registrar reserva")
        print("2. Consultar reservas")
        print("3. Modificar reserva")
        print("4. Cancelar reserva")
        print("5. Marcar inasistencia")
        print("0. Volver")

        v_opcion = input("Seleccione una opción: ").strip()

        if v_opcion == "0":
            break

        try:
            if v_opcion == "1":
                opcion_registrar_reserva(p_sesion)

            elif v_opcion == "2":
                v_reservas = buscar_reservas(p_sesion)

                if not v_reservas:
                    print("No hay reservas para mostrar.")

                for v_reserva in v_reservas:
                    print(
                        f"\nReserva ID: {v_reserva['id_reserva']}\n"
                        f"Cliente: {v_reserva['nombre_cliente']}\n"
                        f"Sucursal: {v_reserva['nombre_sucursal']}\n"
                        f"Inicio: {v_reserva['fecha_hora_inicio']}\n"
                        f"Fin: {v_reserva['fecha_hora_fin_estimada']}\n"
                        f"Personas: {v_reserva['cantidad_personas']}\n"
                        f"Estado: {v_reserva['estado']}\n"
                        f"Mesas: {v_reserva['mesas_asignadas']}"
                    )
            elif v_opcion == "3":
                opcion_modificar_reserva(p_sesion)

            elif v_opcion == "4":
                v_id_reserva = int(input("ID de reserva: "))
                cancelar_reserva(p_sesion, v_id_reserva)
                print("Reserva cancelada correctamente.")

            elif v_opcion == "5":
                v_id_reserva = int(input("ID de reserva: "))

                ejecutar_transaccion(
                    p_sesion,
                    op_cambiar_estado_reserva,
                    {
                        "id_reserva": v_id_reserva,
                        "nuevo_estado": "no_asistio"
                    }
                )

                print("Reserva marcada como no asistida.")

            else:
                print("Opción inválida.")

        except Exception as v_error:
            print(f"No se pudo realizar la operación: {v_error}")

def menu_administracion(p_sesion):
    if p_sesion["rol"] != "administrador":
        raise PermissionError("Solo el administrador tiene acceso.")

    while True:
        print("\n===== ADMINISTRACIÓN =====")
        print("1. Consultar bitácora")
        print("2. Reporte de sucursales")
        print("0. Volver")

        v_opcion = input("Seleccione una opción: ").strip()

        if v_opcion == "0":
            break

        if v_opcion not in ("1", "2"):
            print("Opción inválida.")
            continue

        try:
            print("Fechas: AAAA-MM-DD. Deje vacío para no filtrar.")
            v_inicio = input("Fecha inicial: ").strip() or None
            v_fin = input("Fecha final (inclusive): ").strip() or None

            if v_opcion == "1":
                v_usuario = input(
                    "ID de usuario (vacío para todos): "
                ).strip()

                v_tabla = input(
                    "Tabla (vacío para todas): "
                ).strip()

                v_operacion = input(
                    "Operación INSERT, UPDATE o DELETE "
                    "(vacío para todas): "
                ).strip()

                v_resultados = consultar_bitacora(
                    p_sesion,
                    {
                        "fecha_desde": v_inicio,
                        "fecha_hasta": v_fin,
                        "id_usuario": int(v_usuario) if v_usuario else None,
                        "tabla": v_tabla,
                        "operacion": v_operacion,
                        "limite": 100
                    }
                )

                if not v_resultados:
                    print("No hay registros para esos filtros.")

                for v_registro in v_resultados:
                    print(
                        f"\nFecha: {v_registro['fecha_hora']}\n"
                        f"Usuario: {v_registro['nombre_usuario']}\n"
                        f"Tabla: {v_registro['tabla']}\n"
                        f"Operación: {v_registro['operacion']}\n"
                        f"Registro: {v_registro['registro']}"
                    )

            elif v_opcion == "2":
                for v_sucursal in listar_sucursales():
                    print(
                        f"ID: {v_sucursal['id_sucursal']} | "
                        f"{v_sucursal['nombre']}"
                    )

                v_sucursal = input(
                    "ID de sucursal (vacío para todas): "
                ).strip()

                v_resultados = generar_reporte_sucursales(
                    p_sesion,
                    p_fecha_inicio=v_inicio,
                    p_fecha_fin=v_fin,
                    p_id_sucursal=(
                        int(v_sucursal) if v_sucursal else None
                    )
                )

                if not v_resultados:
                    print("No hay sucursales para mostrar.")

                for v_fila in v_resultados:
                    print(
                        f"\nSucursal: {v_fila['sucursal']}\n"
                        f"Reservas no canceladas: "
                        f"{v_fila['cantidad_reservas']}\n"
                        f"Cantidad de ventas: {v_fila['cantidad_ventas']}\n"
                        f"Importe vendido: Q{v_fila['importe_vendido']:.2f}"
                    )

        except Exception as v_error:
            print(f"No se pudo realizar la consulta: {v_error}")