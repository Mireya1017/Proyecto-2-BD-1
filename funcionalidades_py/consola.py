"""
Módulo de Presentación e Interfaz de Consola (CLI).
Separa estrictamente la interacción con el usuario de la lógica de negocio.
"""

import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Callable

from app.database import (
    ErrorBaseDatos,
    ErrorDisponibilidad,
    ErrorCapacidad,
    ErrorRestriccion,
    ErrorPermiso,
    ErrorAutenticacion,
    ErrorNoEncontrado
)
from app.auth import SesionUsuario
from app import usuarios, reservas, bitacora, reportes, proveedores, compras


def formatear_tabla(filas: List[Dict[str, Any]], encabezados: Optional[Dict[str, str]] = None) -> str:
    """Formatea una lista de diccionarios como una tabla legible."""
    if not filas:
        return "  (No se encontraron registros)"

    keys = list(filas[0].keys()) if not encabezados else list(encabezados.keys())
    titulos = [encabezados[k] if encabezados and k in encabezados else k for k in keys]

    filas_str = []
    for f in filas:
        filas_str.append([str(f.get(k, "")) for k in keys])

    anchos = [len(t) for t in titulos]
    for row in filas_str:
        for idx, val in enumerate(row):
            anchos[idx] = max(anchos[idx], len(val))

    separador = "+" + "+".join(["-" * (w + 2) for w in anchos]) + "+"
    cabecera = "| " + " | ".join([t.ljust(anchos[i]) for i, t in enumerate(titulos)]) + " |"

    lineas = [separador, cabecera, separador]
    for row in filas_str:
        fila_linea = "| " + " | ".join([row[i].ljust(anchos[i]) for i in range(len(row))]) + " |"
        lineas.append(fila_linea)
    lineas.append(separador)

    return "\n".join(lineas)


def pausar() -> None:
    input("\nPresione [Enter] para continuar...")


def menu_reservas(sesion: SesionUsuario) -> None:
    """Submenú para reservas."""
    while True:
        print("\n" + "=" * 60)
        print("          GESTIÓN DE RESERVAS DE MESAS")
        print("=" * 60)
        print("  1. Consultar disponibilidad de mesas")
        print("  2. Registrar nueva reserva")
        print("  3. Buscar y listar reservas")
        print("  4. Modificar reserva existente")
        print("  5. Cancelar reserva")
        print("  0. Regresar al menú anterior")
        print("-" * 60)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            _sub_consultar_disponibilidad(sesion)
        elif opcion == "2":
            _sub_registrar_reserva(sesion)
        elif opcion == "3":
            _sub_buscar_reservas(sesion)
        elif opcion == "4":
            _sub_modificar_reserva(sesion)
        elif opcion == "5":
            _sub_cancelar_reserva(sesion)
        elif opcion == "0":
            break
        else:
            print("[AVISO] Opción inválida.")


def _sub_consultar_disponibilidad(sesion: SesionUsuario) -> None:
    print("\n--- Consultar Disponibilidad de Mesas ---")
    try:
        sucursal_id = sesion.id_sucursal
        if sesion.es_administrador:
            s_input = input(f"Ingrese ID de sucursal [{sucursal_id}]: ").strip()
            if s_input:
                sucursal_id = int(s_input)

        fecha_str = input("Fecha de inicio (YYYY-MM-DD HH:MM): ").strip()
        f_inicio = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")

        duracion_mins = input("Duración estimada en minutos [120]: ").strip()
        mins = int(duracion_mins) if duracion_mins else 120
        f_fin = datetime.fromtimestamp(f_inicio.timestamp() + (mins * 60))

        zona_input = input("Zona deseada (interior/exterior o Enter para todas): ").strip().lower()
        zona = zona_input if zona_input in ('interior', 'exterior') else None

        personas_str = input("Cantidad de personas (opcional): ").strip()
        personas = int(personas_str) if personas_str else 0

        mesas = reservas.consultar_disponibilidad_mesas(
            id_sucursal=sucursal_id,
            fecha_hora_inicio=f_inicio,
            fecha_hora_fin=f_fin,
            zona=zona
        )

        print(f"\nMesas disponibles en sucursal {sucursal_id}:")
        encabezados = {"id_mesa": "ID", "numero": "Número", "capacidad": "Capacidad", "zona": "Zona"}
        print(formatear_tabla(mesas, encabezados))

        if personas > 0 and mesas:
            sugerencias = reservas.sugerir_mesas_adecuadas(mesas, personas, zona)
            if sugerencias:
                print(f"\nSugerencias para {personas} personas (misma zona):")
                for idx, combo in enumerate(sugerencias, 1):
                    nums = ", ".join([f"Mesa {m['numero']} (cap. {m['capacidad']})" for m in combo])
                    cap_total = sum(m['capacidad'] for m in combo)
                    print(f"  Opción {idx}: {nums} | Capacidad total: {cap_total} | Zona: {combo[0]['zona']}")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        pausar()


def _sub_registrar_reserva(sesion: SesionUsuario) -> None:
    print("\n--- Registrar Nueva Reserva ---")
    try:
        cliente_id = int(input("ID del Cliente principal: ").strip())
        sucursal_id = sesion.id_sucursal
        if sesion.es_administrador:
            s_input = input(f"ID de Sucursal [{sucursal_id}]: ").strip()
            if s_input:
                sucursal_id = int(s_input)

        fecha_str = input("Fecha y hora de inicio (YYYY-MM-DD HH:MM): ").strip()
        f_inicio = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")

        fecha_fin_str = input("Fecha y hora de fin estimada (YYYY-MM-DD HH:MM): ").strip()
        f_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d %H:%M")

        personas = int(input("Cantidad de personas: ").strip())

        mesas_str = input("IDs de mesas asignadas (ej. 1, 2): ").strip()
        ids_mesas = [int(m.strip()) for m in mesas_str.split(",") if m.strip()]

        id_reserva = reservas.crear_reserva(
            id_cliente=cliente_id,
            id_sucursal=sucursal_id,
            fecha_hora_inicio=f_inicio,
            fecha_hora_fin_estimada=f_fin,
            cantidad_personas=personas,
            ids_mesas=ids_mesas,
            sesion=sesion
        )
        print(f"\n[ÉXITO] ¡Reserva creada con ID #{id_reserva}!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        pausar()


def _sub_buscar_reservas(sesion: SesionUsuario) -> None:
    print("\n--- Buscar Reservas ---")
    try:
        id_r_in = input("ID de Reserva (o Enter): ").strip()
        id_reserva = int(id_r_in) if id_r_in else None

        id_c_in = input("ID de Cliente (o Enter): ").strip()
        id_cliente = int(id_c_in) if id_c_in else None

        estado_in = input("Estado (confirmada/cancelada/atendida/no_asistio o Enter): ").strip().lower()
        estado = estado_in if estado_in else None

        fecha_in = input("Fecha (YYYY-MM-DD o Enter): ").strip()
        fecha = datetime.strptime(fecha_in, "%Y-%m-%d").date() if fecha_in else None

        resultados = reservas.buscar_reservas(
            id_reserva=id_reserva,
            id_cliente=id_cliente,
            fecha=fecha,
            estado=estado,
            sesion=sesion
        )
        encabezados = {
            "id_reserva": "ID", "nombre_cliente": "Cliente", "nombre_sucursal": "Sucursal",
            "fecha_hora_inicio": "Inicio", "fecha_hora_fin_estimada": "Fin Estimado",
            "cantidad_personas": "Pers.", "estado": "Estado", "numeros_mesas": "Mesas", "zona_mesas": "Zona"
        }
        print("\n" + formatear_tabla(resultados, encabezados))
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        pausar()


def _sub_modificar_reserva(sesion: SesionUsuario) -> None:
    print("\n--- Modificar Reserva ---")
    try:
        id_reserva = int(input("ID de la reserva a modificar: ").strip())
        print("Deje en blanco los campos que NO desea cambiar:")
        f_ini_in = input("Nueva fecha y hora de inicio (YYYY-MM-DD HH:MM): ").strip()
        f_ini = datetime.strptime(f_ini_in, "%Y-%m-%d %H:%M") if f_ini_in else None

        f_fin_in = input("Nueva fecha y hora de fin estimada (YYYY-MM-DD HH:MM): ").strip()
        f_fin = datetime.strptime(f_fin_in, "%Y-%m-%d %H:%M") if f_fin_in else None

        pers_in = input("Nueva cantidad de personas: ").strip()
        pers = int(pers_in) if pers_in else None

        mesas_in = input("Nuevos IDs de mesas (ej. 3, 4): ").strip()
        nuevas_mesas = [int(m.strip()) for m in mesas_in.split(",") if m.strip()] if mesas_in else None

        reservas.modificar_reserva(
            id_reserva=id_reserva,
            nueva_fecha_inicio=f_ini,
            nueva_fecha_fin=f_fin,
            nueva_cantidad_personas=pers,
            nuevos_ids_mesas=nuevas_mesas,
            sesion=sesion
        )
        print(f"\n[ÉXITO] ¡Reserva #{id_reserva} modificada correctamente!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        pausar()


def _sub_cancelar_reserva(sesion: SesionUsuario) -> None:
    print("\n--- Cancelar Reserva ---")
    try:
        id_reserva = int(input("ID de la reserva a cancelar: ").strip())
        confirm = input(f"¿Confirmar cancelación de reserva #{id_reserva}? (s/N): ").strip().lower()
        if confirm == 's':
            reservas.cancelar_reserva(id_reserva=id_reserva, sesion=sesion)
            print(f"\n[ÉXITO] Reserva #{id_reserva} cancelada. Asignaciones históricas conservadas.")
        else:
            print("Operación cancelada.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        pausar()


def menu_usuarios(sesion: SesionUsuario) -> None:
    """Submenú usuarios."""
    while True:
        print("\n" + "=" * 60)
        print("          ADMINISTRACIÓN DE USUARIOS")
        print("=" * 60)
        print("  1. Listar usuarios del sistema")
        print("  2. Registrar nuevo usuario")
        print("  0. Regresar al menú anterior")
        print("-" * 60)

        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            try:
                lista = usuarios.listar_usuarios(sesion=sesion)
                encabezados = {
                    "id_usuario": "ID", "nombre_usuario": "Usuario",
                    "rol": "Rol", "id_sucursal": "ID Sucursal", "nombre_sucursal": "Sucursal Habitual"
                }
                print("\n" + formatear_tabla(lista, encabezados))
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "2":
            try:
                nombre = input("Nombre de usuario: ").strip()
                contrasena = input("Contraseña: ").strip()
                rol = input("Rol (administrador, gerente, mesero): ").strip().lower()
                sucursal_id = int(input("ID de Sucursal habitual: ").strip())

                nuevo_id = usuarios.registrar_usuario(
                    nombre_usuario=nombre, contrasena=contrasena, rol=rol, id_sucursal=sucursal_id, sesion=sesion
                )
                print(f"\n[ÉXITO] Usuario '{nombre}' registrado con ID #{nuevo_id}.")
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "0":
            break


def menu_bitacora(sesion: SesionUsuario) -> None:
    """Submenú bitácora."""
    while True:
        print("\n" + "=" * 60)
        print("          CONSULTA DE BITÁCORA DE AUDITORÍA")
        print("=" * 60)
        print("  1. Ver últimos registros")
        print("  2. Filtrar por rango de fechas")
        print("  3. Filtrar por tabla")
        print("  4. Filtrar por operación (INSERT/UPDATE/DELETE)")
        print("  0. Regresar al menú anterior")
        print("-" * 60)

        opcion = input("Seleccione una opción: ").strip()
        if opcion in ("1", "2", "3", "4"):
            f_desde = None
            f_hasta = None
            tabla = None
            operacion = None
            try:
                if opcion == "2":
                    d_str = input("Fecha desde (YYYY-MM-DD): ").strip()
                    f_desde = datetime.strptime(d_str, "%Y-%m-%d") if d_str else None
                    h_str = input("Fecha hasta (YYYY-MM-DD): ").strip()
                    f_hasta = datetime.strptime(h_str, "%Y-%m-%d") if h_str else None
                elif opcion == "3":
                    tabla = input("Tabla (ej. reserva, usuario, lote): ").strip()
                elif opcion == "4":
                    operacion = input("Operación (INSERT, UPDATE, DELETE): ").strip().upper()

                limite_str = input("Límite [50]: ").strip()
                limite = int(limite_str) if limite_str else 50

                registros = bitacora.consultar_bitacora(
                    fecha_desde=f_desde, fecha_hasta=f_hasta, tabla=tabla, operacion=operacion, limite=limite, sesion=sesion
                )
                encabezados = {
                    "id_bitacora": "ID", "fecha_hora": "Fecha/Hora", "nombre_usuario": "Usuario",
                    "tabla": "Tabla", "operacion": "Operación", "registro": "Registro Afectado"
                }
                print("\n" + formatear_tabla(registros, encabezados))
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "0":
            break


def menu_reporte_sucursales(sesion: SesionUsuario) -> None:
    """Submenú reporte."""
    while True:
        print("\n" + "=" * 60)
        print("     REPORTE DE SUCURSALES (RESERVAS, VENTAS E IMPORTES)")
        print("=" * 60)
        print("  1. Reporte consolidado global")
        print("  2. Filtrar por rango de fechas")
        print("  3. Filtrar por sucursal específica")
        print("  0. Regresar al menú anterior")
        print("-" * 60)

        opcion = input("Seleccione una opción: ").strip()
        if opcion in ("1", "2", "3"):
            f_desde = None
            f_hasta = None
            id_sucursal = None
            try:
                if opcion == "2":
                    d_str = input("Fecha inicial (YYYY-MM-DD): ").strip()
                    f_desde = datetime.strptime(d_str, "%Y-%m-%d") if d_str else None
                    h_str = input("Fecha final (YYYY-MM-DD): ").strip()
                    f_hasta = datetime.strptime(h_str, "%Y-%m-%d") if h_str else None
                elif opcion == "3":
                    id_sucursal = int(input("ID de la sucursal: ").strip())

                rep = reportes.reporte_rendimiento_sucursales(
                    fecha_desde=f_desde, fecha_hasta=f_hasta, id_sucursal=id_sucursal, sesion=sesion
                )
                print("\n" + "=" * 70)
                print("           REPORTE OFICIAL DE RENDIMIENTO POR SUCURSAL")
                print("=" * 70)
                print(f"Período evaluado : {rep['filtros']['fecha_desde']} hasta {rep['filtros']['fecha_hasta']}")
                print(f"Sede filtrada    : {rep['filtros']['sucursal']}")
                print("-" * 70)

                encabezados = {
                    "id_sucursal": "ID", "nombre_sucursal": "Sucursal",
                    "cantidad_reservas": "Reservas", "cantidad_ventas": "Ventas", "importe_vendido": "Total Vendido (Q)"
                }
                print(formatear_tabla(rep["filas"], encabezados))
                tot = rep["totales"]
                print("-" * 70)
                print(f"TOTALES CONSOLIDADOS: Reservas: {tot['total_reservas']} | Ventas: {tot['total_ventas']} | Vendido: Q{tot['total_importe_vendido']:,.2f}")
                print("=" * 70)
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "0":
            break


def menu_proveedores_compras(sesion: SesionUsuario) -> None:
    """Submenú compras y proveedores."""
    while True:
        print("\n" + "=" * 60)
        print("          GESTIÓN DE PROVEEDORES Y COMPRAS")
        print("=" * 60)
        print("  1. Consultar proveedores")
        print("  2. Registrar proveedor")
        print("  3. Registrar compra coordinada con inventario")
        print("  4. Consultar compras registradas")
        print("  0. Regresar al menú anterior")
        print("-" * 60)

        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            try:
                filtro = input("Filtrar por nombre (o Enter): ").strip()
                provs = proveedores.consultar_proveedores(filtro_nombre=filtro)
                encabezados = {"id_proveedor": "ID", "nombre": "Nombre", "telefono": "Teléfono", "email": "Email"}
                print("\n" + formatear_tabla(provs, encabezados))
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "2":
            try:
                nombre = input("Nombre: ").strip()
                tel = input("Teléfono: ").strip()
                email = input("Email: ").strip()
                dir_p = input("Dirección: ").strip()
                pid = proveedores.registrar_proveedor(nombre=nombre, telefono=tel, email=email, direccion=dir_p, sesion=sesion)
                print(f"\n[ÉXITO] Proveedor #{pid} registrado.")
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "3":
            try:
                pid = int(input("ID Proveedor: ").strip())
                sid = sesion.id_sucursal
                if sesion.es_administrador:
                    s_in = input(f"ID Sucursal [{sid}]: ").strip()
                    if s_in: sid = int(s_in)

                detalles = []
                while True:
                    ins_in = input("ID de insumo (o 'fin'): ").strip()
                    if ins_in.lower() == 'fin' or not ins_in: break
                    id_ins = int(ins_in)
                    cant = float(input(f"Cantidad insumo {id_ins}: ").strip())
                    precio = float(input(f"Precio unitario Q: ").strip())
                    cad = input(f"Fecha caducidad (YYYY-MM-DD): ").strip()
                    detalles.append({
                        "id_insumo": id_ins, "cantidad": cant, "precio_unitario": precio,
                        "fecha_caducidad": datetime.strptime(cad, "%Y-%m-%d").date()
                    })
                if detalles:
                    cid = compras.registrar_compra(id_proveedor=pid, id_sucursal=sid, detalles_insumos=detalles, sesion=sesion)
                    print(f"\n[ÉXITO] Compra #{cid} registrada exitosamente.")
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "4":
            try:
                cps = compras.consultar_compras(sesion=sesion)
                encabezados = {"id_compra": "ID", "nombre_proveedor": "Proveedor", "nombre_sucursal": "Sucursal", "fecha_hora": "Fecha/Hora", "total": "Total (Q)"}
                print("\n" + formatear_tabla(cps, encabezados))
            except Exception as e:
                print(f"[ERROR] {e}")
            pausar()
        elif opcion == "0":
            break


def obtener_opciones_menu_pablo(sesion: SesionUsuario) -> Dict[str, Tuple[str, Callable[[SesionUsuario], None]]]:
    """Retorna las opciones de menú que Yu-fong integrará en la consola principal."""
    opciones: Dict[str, Tuple[str, Callable[[SesionUsuario], None]]] = {}
    opciones["reservas"] = ("Gestión de Reservas de Mesas", menu_reservas)

    if sesion.rol in ("administrador", "gerente"):
        opciones["compras"] = ("Gestión de Proveedores y Compras de Insumos", menu_proveedores_compras)

    if sesion.es_administrador:
        opciones["usuarios"] = ("Administración de Usuarios y Permisos", menu_usuarios)
        opciones["bitacora"] = ("Consulta de Bitácora de Auditoría", menu_bitacora)
        opciones["reporte_sucursales"] = ("Reporte de Rendimiento de Sucursales", menu_reporte_sucursales)

    return opciones
