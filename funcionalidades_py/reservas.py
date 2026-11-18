"""
Módulo de Gestión de Reservas y Disponibilidad de Mesas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.database import (
    transaccion,
    ErrorBaseDatos,
    ErrorDisponibilidad,
    ErrorCapacidad,
    ErrorRestriccion,
    ErrorNoEncontrado,
    ErrorPermiso
)
from app.auth import SesionUsuario, validar_permisos_operacion

ADVISORY_LOCK_RESERVAS = 308802


def consultar_disponibilidad_mesas(
    id_sucursal: int,
    fecha_hora_inicio: datetime,
    fecha_hora_fin: datetime,
    zona: Optional[str] = None,
    excluir_id_reserva: Optional[int] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Consulta mesas libres de una sucursal en un rango horario."""
    if fecha_hora_fin <= fecha_hora_inicio:
        raise ValueError("La fecha y hora de fin estimada debe ser posterior al inicio.")

    if zona and zona not in ('interior', 'exterior'):
        raise ValueError("La zona debe ser 'interior' o 'exterior'.")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            query = """
                SELECT 
                    m.id_mesa,
                    m.id_sucursal,
                    m.numero,
                    m.capacidad,
                    m.zona
                FROM mesa m
                WHERE m.id_sucursal = %s
                  AND (%s IS NULL OR m.zona = %s)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM reserva_mesa rm
                      JOIN reserva r ON r.id_reserva = rm.id_reserva
                      WHERE rm.id_mesa = m.id_mesa
                        AND r.estado IN ('confirmada', 'atendida')
                        AND r.fecha_hora_inicio < %s
                        AND r.fecha_hora_fin_estimada > %s
                        AND (%s::INTEGER IS NULL OR r.id_reserva <> %s)
                  )
                ORDER BY m.zona ASC, m.numero ASC;
            """
            cur.execute(
                query,
                (
                    id_sucursal,
                    zona,
                    zona,
                    fecha_hora_fin,
                    fecha_hora_inicio,
                    excluir_id_reserva,
                    excluir_id_reserva
                )
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def sugerir_mesas_adecuadas(
    mesas_disponibles: List[Dict[str, Any]],
    cantidad_personas: int,
    zona_preferida: Optional[str] = None
) -> List[List[Dict[str, Any]]]:
    """Sugerencia de mesas en la misma zona con capacidad suficiente."""
    if cantidad_personas <= 0:
        return []

    zonas_a_evaluar = [zona_preferida] if zona_preferida else ['interior', 'exterior']
    sugerencias = []

    for z in zonas_a_evaluar:
        mesas_zona = [m for m in mesas_disponibles if m['zona'] == z]
        individuales = [m for m in mesas_zona if m['capacidad'] >= cantidad_personas]
        individuales.sort(key=lambda x: x['capacidad'])
        for ind in individuales:
            sugerencias.append([ind])

        if not sugerencias:
            mesas_zona.sort(key=lambda x: x['capacidad'], reverse=True)
            combo = []
            acumulado = 0
            for m in mesas_zona:
                combo.append(m)
                acumulado += m['capacidad']
                if acumulado >= cantidad_personas:
                    sugerencias.append(list(combo))
                    break

    return sugerencias


def crear_reserva(
    id_cliente: int,
    id_sucursal: int,
    fecha_hora_inicio: datetime,
    fecha_hora_fin_estimada: datetime,
    cantidad_personas: int,
    ids_mesas: List[int],
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> int:
    """Registra una reserva con sus mesas asignadas de forma atómica."""
    validar_permisos_operacion(
        sesion,
        roles_permitidos=["administrador", "gerente", "mesero"],
        id_sucursal_operacion=id_sucursal
    )

    if cantidad_personas <= 0:
        raise ValueError("La cantidad de personas debe ser mayor que cero.")

    if fecha_hora_fin_estimada <= fecha_hora_inicio:
        raise ValueError("La fecha/hora de fin estimada debe ser posterior a la de inicio.")

    if not ids_mesas:
        raise ValueError("Debe asignar al menos una mesa a la reserva.")

    ids_mesas_unicos = list(dict.fromkeys(ids_mesas))
    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s);", (ADVISORY_LOCK_RESERVAS,))

            cur.execute("SELECT id_cliente FROM cliente WHERE id_cliente = %s;", (id_cliente,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"El cliente con ID {id_cliente} no existe.")

            cur.execute("SELECT id_sucursal FROM sucursal WHERE id_sucursal = %s;", (id_sucursal,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"La sucursal con ID {id_sucursal} no existe.")

            placeholders = ",".join(["%s"] * len(ids_mesas_unicos))
            cur.execute(
                f"""
                SELECT id_mesa, id_sucursal, capacidad, zona
                FROM mesa
                WHERE id_mesa IN ({placeholders});
                """,
                ids_mesas_unicos
            )
            mesas = cur.fetchall()

            if len(mesas) != len(ids_mesas_unicos):
                raise ErrorNoEncontrado("Una o más de las mesas indicadas no existen.")

            zonas = set()
            capacidad_total = 0
            for mid, msucursal, mcapacidad, mzona in mesas:
                if msucursal != id_sucursal:
                    raise ErrorRestriccion(f"La mesa con ID {mid} no pertenece a la sucursal {id_sucursal}.")
                zonas.add(mzona)
                capacidad_total += mcapacidad

            if len(zonas) > 1:
                raise ErrorRestriccion(
                    f"Mesas incompatibles: Se asignaron mesas de diferentes zonas ({', '.join(zonas)}). "
                    "Todas las mesas deben ser de una misma zona."
                )

            if capacidad_total < cantidad_personas:
                raise ErrorCapacidad(
                    f"Capacidad insuficiente: Las mesas seleccionadas admiten {capacidad_total} personas "
                    f"y la reserva requiere {cantidad_personas}."
                )

            cur.execute(
                f"""
                SELECT rm.id_mesa
                FROM reserva_mesa rm
                JOIN reserva r ON r.id_reserva = rm.id_reserva
                WHERE rm.id_mesa IN ({placeholders})
                  AND r.estado IN ('confirmada', 'atendida')
                  AND r.fecha_hora_inicio < %s
                  AND r.fecha_hora_fin_estimada > %s
                LIMIT 1;
                """,
                ids_mesas_unicos + [fecha_hora_fin_estimada, fecha_hora_inicio]
            )
            conflicto = cur.fetchone()
            if conflicto:
                raise ErrorDisponibilidad(
                    f"Conflicto de horario: La mesa ID {conflicto[0]} ya está reservada en el rango solicitado."
                )

            cur.execute(
                """
                INSERT INTO reserva (
                    id_cliente,
                    id_sucursal,
                    fecha_hora_inicio,
                    fecha_hora_fin_estimada,
                    cantidad_personas,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, 'confirmada')
                RETURNING id_reserva;
                """,
                (
                    id_cliente,
                    id_sucursal,
                    fecha_hora_inicio,
                    fecha_hora_fin_estimada,
                    cantidad_personas
                )
            )
            id_reserva = cur.fetchone()[0]

            for mid in ids_mesas_unicos:
                cur.execute(
                    """
                    INSERT INTO reserva_mesa (id_reserva, id_mesa)
                    VALUES (%s, %s);
                    """,
                    (id_reserva, mid)
                )

            return id_reserva


def buscar_reservas(
    id_reserva: Optional[int] = None,
    id_cliente: Optional[int] = None,
    id_sucursal: Optional[int] = None,
    fecha: Optional[datetime] = None,
    estado: Optional[str] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Busca reservas aplicando filtros opcionales."""
    if sesion:
        validar_permisos_operacion(
            sesion,
            roles_permitidos=["administrador", "gerente", "mesero"]
        )
        if not sesion.es_administrador:
            id_sucursal = sesion.id_sucursal

    with transaccion(conn) as c:
        with c.cursor() as cur:
            query = """
                SELECT 
                    r.id_reserva,
                    r.id_cliente,
                    c.nombre AS nombre_cliente,
                    c.telefono AS telefono_cliente,
                    r.id_sucursal,
                    s.nombre AS nombre_sucursal,
                    r.fecha_hora_inicio,
                    r.fecha_hora_fin_estimada,
                    r.cantidad_personas,
                    r.estado,
                    COALESCE(
                        STRING_AGG(m.numero::TEXT, ', ' ORDER BY m.numero), 
                        ''
                    ) AS numeros_mesas,
                    MAX(m.zona) AS zona_mesas
                FROM reserva r
                JOIN cliente c ON c.id_cliente = r.id_cliente
                JOIN sucursal s ON s.id_sucursal = r.id_sucursal
                LEFT JOIN reserva_mesa rm ON rm.id_reserva = r.id_reserva
                LEFT JOIN mesa m ON m.id_mesa = rm.id_mesa
                WHERE (%s::INTEGER IS NULL OR r.id_reserva = %s)
                  AND (%s::INTEGER IS NULL OR r.id_cliente = %s)
                  AND (%s::INTEGER IS NULL OR r.id_sucursal = %s)
                  AND (%s::DATE IS NULL OR r.fecha_hora_inicio::DATE = %s::DATE)
                  AND (%s::VARCHAR IS NULL OR r.estado = %s)
                GROUP BY 
                    r.id_reserva,
                    r.id_cliente,
                    c.nombre,
                    c.telefono,
                    r.id_sucursal,
                    s.nombre,
                    r.fecha_hora_inicio,
                    r.fecha_hora_fin_estimada,
                    r.cantidad_personas,
                    r.estado
                ORDER BY r.fecha_hora_inicio DESC, r.id_reserva DESC;
            """
            cur.execute(
                query,
                (
                    id_reserva, id_reserva,
                    id_cliente, id_cliente,
                    id_sucursal, id_sucursal,
                    fecha, fecha,
                    estado, estado
                )
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def modificar_reserva(
    id_reserva: int,
    nueva_fecha_inicio: Optional[datetime] = None,
    nueva_fecha_fin: Optional[datetime] = None,
    nueva_cantidad_personas: Optional[int] = None,
    nuevos_ids_mesas: Optional[List[int]] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> None:
    """Modifica una reserva retirando asignaciones previas y creando las nuevas atómicamente."""
    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s);", (ADVISORY_LOCK_RESERVAS,))

            cur.execute(
                """
                SELECT id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, estado
                FROM reserva
                WHERE id_reserva = %s
                FOR UPDATE;
                """,
                (id_reserva,)
            )
            reserva_actual = cur.fetchone()
            if not reserva_actual:
                raise ErrorNoEncontrado(f"No existe la reserva con ID {id_reserva}.")

            id_sucursal_res, f_inicio_act, f_fin_act, personas_act, estado_act = reserva_actual

            validar_permisos_operacion(
                sesion,
                roles_permitidos=["administrador", "gerente", "mesero"],
                id_sucursal_operacion=id_sucursal_res
            )

            if estado_act in ('cancelada', 'atendida'):
                raise ErrorRestriccion(f"No se puede modificar una reserva en estado '{estado_act}'.")

            f_inicio = nueva_fecha_inicio or f_inicio_act
            f_fin = nueva_fecha_fin or f_fin_act
            personas = nueva_cantidad_personas or personas_act

            if f_fin <= f_inicio:
                raise ValueError("La fecha/hora de fin estimada debe ser posterior al inicio.")

            if personas <= 0:
                raise ValueError("La cantidad de personas debe ser mayor que cero.")

            if nuevos_ids_mesas is not None:
                if not nuevos_ids_mesas:
                    raise ValueError("La reserva no puede quedar sin mesas asignadas.")

                ids_unicos = list(dict.fromkeys(nuevos_ids_mesas))
                placeholders = ",".join(["%s"] * len(ids_unicos))

                cur.execute(
                    f"SELECT id_mesa, id_sucursal, capacidad, zona FROM mesa WHERE id_mesa IN ({placeholders});",
                    ids_unicos
                )
                mesas_db = cur.fetchall()

                if len(mesas_db) != len(ids_unicos):
                    raise ErrorNoEncontrado("Una o más mesas especificadas no existen.")

                zonas = set()
                capacidad_total = 0
                for mid, msuc, mcap, mzona in mesas_db:
                    if msuc != id_sucursal_res:
                        raise ErrorRestriccion(f"La mesa {mid} no pertenece a la sucursal {id_sucursal_res}.")
                    zonas.add(mzona)
                    capacidad_total += mcap

                if len(zonas) > 1:
                    raise ErrorRestriccion("Todas las mesas asignadas deben pertenecer a la misma zona.")

                if capacidad_total < personas:
                    raise ErrorCapacidad(
                        f"Capacidad insuficiente: Las mesas admiten {capacidad_total} personas y se requieren {personas}."
                    )

                cur.execute(
                    f"""
                    SELECT rm.id_mesa
                    FROM reserva_mesa rm
                    JOIN reserva r ON r.id_reserva = rm.id_reserva
                    WHERE rm.id_mesa IN ({placeholders})
                      AND r.id_reserva <> %s
                      AND r.estado IN ('confirmada', 'atendida')
                      AND r.fecha_hora_inicio < %s
                      AND r.fecha_hora_fin_estimada > %s
                    LIMIT 1;
                    """,
                    ids_unicos + [id_reserva, f_fin, f_inicio]
                )
                conflicto = cur.fetchone()
                if conflicto:
                    raise ErrorDisponibilidad(
                        f"Conflicto de horario: La mesa ID {conflicto[0]} está ocupada por otra reserva en ese intervalo."
                    )

                cur.execute("DELETE FROM reserva_mesa WHERE id_reserva = %s;", (id_reserva,))
                for mid in ids_unicos:
                    cur.execute(
                        "INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (%s, %s);",
                        (id_reserva, mid)
                    )

            cur.execute(
                """
                UPDATE reserva
                SET fecha_hora_inicio = %s,
                    fecha_hora_fin_estimada = %s,
                    cantidad_personas = %s
                WHERE id_reserva = %s;
                """,
                (f_inicio, f_fin, personas, id_reserva)
            )


def cancelar_reserva(
    id_reserva: int,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> None:
    """Cancela una reserva activa, conservando su registro y asignaciones históricas."""
    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s);", (ADVISORY_LOCK_RESERVAS,))

            cur.execute(
                "SELECT id_sucursal, estado FROM reserva WHERE id_reserva = %s FOR UPDATE;",
                (id_reserva,)
            )
            fila = cur.fetchone()
            if not fila:
                raise ErrorNoEncontrado(f"No existe la reserva con ID {id_reserva}.")

            id_sucursal, estado_actual = fila

            validar_permisos_operacion(
                sesion,
                roles_permitidos=["administrador", "gerente", "mesero"],
                id_sucursal_operacion=id_sucursal
            )

            if estado_actual == 'cancelada':
                raise ErrorRestriccion("La reserva ya se encuentra cancelada.")
            if estado_actual == 'atendida':
                raise ErrorRestriccion("No se puede cancelar una reserva que ya fue atendida.")

            cur.execute(
                "UPDATE reserva SET estado = 'cancelada' WHERE id_reserva = %s;",
                (id_reserva,)
            )


def obtener_reservas_cliente(
    id_cliente: int,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Función compartida para el módulo de Clientes e Historial (Yu-fong)."""
    with transaccion(conn) as c:
        with c.cursor() as cur:
            query = """
                SELECT 
                    r.id_reserva,
                    r.id_sucursal,
                    s.nombre AS nombre_sucursal,
                    r.fecha_hora_inicio,
                    r.fecha_hora_fin_estimada,
                    r.cantidad_personas,
                    r.estado,
                    COALESCE(
                        STRING_AGG(m.numero::TEXT, ', ' ORDER BY m.numero), 
                        ''
                    ) AS mesas
                FROM reserva r
                JOIN sucursal s ON s.id_sucursal = r.id_sucursal
                LEFT JOIN reserva_mesa rm ON rm.id_reserva = r.id_reserva
                LEFT JOIN mesa m ON m.id_mesa = rm.id_mesa
                WHERE r.id_cliente = %s
                GROUP BY 
                    r.id_reserva,
                    r.id_sucursal,
                    s.nombre,
                    r.fecha_hora_inicio,
                    r.fecha_hora_fin_estimada,
                    r.cantidad_personas,
                    r.estado
                ORDER BY r.fecha_hora_inicio DESC;
            """
            cur.execute(query, (id_cliente,))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
