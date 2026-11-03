# funcionalidades_py/reservas.py
from datetime import datetime
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.transacciones import ejecutar_transaccion
from funcionalidades_py.usuarios import validar_permiso, validar_acceso_sucursal

ESTADOS_RESERVA = ("confirmada", "cancelada", "atendida", "no_asistio")
ZONAS_MESA = ("interior", "exterior")

def _validar_horario(p_inicio, p_fin):
    try:
        v_inicio = (
            datetime.fromisoformat(p_inicio)
            if isinstance(p_inicio, str)
            else p_inicio
        )

        v_fin = (
            datetime.fromisoformat(p_fin)
            if isinstance(p_fin, str)
            else p_fin
        )
    except ValueError:
        raise ValueError(
            "Ingrese fechas válidas con formato AAAA-MM-DD HH:MM."
        )

    if not isinstance(v_inicio, datetime) or not isinstance(v_fin, datetime):
        raise ValueError("Debe indicar fecha y hora de inicio y fin.")

    if v_fin <= v_inicio:
        raise ValueError(
            "La fecha y hora final debe ser posterior a la inicial."
        )


def consultar_mesas_disponibles(
    p_id_sucursal: int,
    p_fecha_hora_inicio: datetime | str,
    p_fecha_hora_fin_estimada: datetime | str,
    p_zona: str | None = None,
    p_id_reserva_excluir: int | None = None,
) -> list[dict]:
    """
    Devuelve las mesas disponibles de una sucursal para el horario indicado.
    Reutilizable tanto en reservas como en el módulo de visitas antes de ocupar una mesa.
    """
    _validar_horario(
        p_fecha_hora_inicio,
        p_fecha_hora_fin_estimada
    )

    if p_zona and p_zona not in ZONAS_MESA:
        raise ValueError(f"Zona inválida. Debe ser una de: {ZONAS_MESA}.")

    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                SELECT m.id_mesa, m.numero, m.capacidad, m.zona
                FROM mesa m
                WHERE m.id_sucursal = %s::integer
                  AND (%s::varchar IS NULL OR m.zona = %s::varchar)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM reserva_mesa rm
                      JOIN reserva r ON r.id_reserva = rm.id_reserva
                      WHERE rm.id_mesa = m.id_mesa
                        AND r.estado IN ('confirmada', 'atendida')
                        AND (%s::integer IS NULL OR r.id_reserva <> %s::integer)
                        AND r.fecha_hora_inicio < %s::timestamp
                        AND r.fecha_hora_fin_estimada > %s::timestamp
                  )
                ORDER BY m.zona ASC, m.numero ASC;
                """,
                (
                    int(p_id_sucursal),
                    p_zona,
                    p_zona,
                    p_id_reserva_excluir,
                    p_id_reserva_excluir,
                    p_fecha_hora_fin_estimada,
                    p_fecha_hora_inicio,
                ),
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()


def _validar_mesas_en_transaccion(
    p_cursor,
    p_id_sucursal: int,
    p_cantidad_personas: int,
    p_ids_mesas: list[int],
    p_inicio,
    p_fin,
    p_id_reserva_excluir: int | None = None,
) -> None:
    """Verifica sucursal, misma zona, capacidad suficiente y horario sin superposición."""
    _validar_horario(p_inicio, p_fin)
    if not p_ids_mesas:
        raise ValueError("Debe asignar al menos una mesa a la reserva.")

    v_ids_unicos = list(dict.fromkeys(int(x) for x in p_ids_mesas))
    if len(v_ids_unicos) != len(p_ids_mesas):
        raise ValueError("No se puede repetir una misma mesa dentro de la misma reserva.")

    p_cursor.execute(
        """
        SELECT id_mesa, id_sucursal, numero, capacidad, zona
        FROM mesa
        WHERE id_mesa = ANY(%s::integer[]);
        """,
        (v_ids_unicos,),
    )
    v_filas = p_cursor.fetchall()
    if len(v_filas) != len(v_ids_unicos):
        raise ValueError("Una o más mesas seleccionadas no existen.")

    v_zonas = set()
    v_capacidad_total = 0
    for v_id_mesa, v_id_suc_mesa, v_numero, v_capacidad, v_zona in v_filas:
        if v_id_suc_mesa != p_id_sucursal:
            raise ValueError(
                f"La mesa #{v_numero} (ID {v_id_mesa}) no pertenece a la sucursal {p_id_sucursal}."
            )
        v_zonas.add(v_zona)
        v_capacidad_total += v_capacidad

    if len(v_zonas) > 1:
        raise ValueError("Todas las mesas de una reserva deben pertenecer a una misma zona.")

    if v_capacidad_total < p_cantidad_personas:
        raise ValueError(
            f"Capacidad insuficiente: las mesas seleccionadas suman {v_capacidad_total} "
            f"lugares para {p_cantidad_personas} personas."
        )

    p_cursor.execute(
        """
        SELECT m.numero, r.id_reserva, r.fecha_hora_inicio, r.fecha_hora_fin_estimada
        FROM reserva_mesa rm
        JOIN reserva r ON r.id_reserva = rm.id_reserva
        JOIN mesa m ON m.id_mesa = rm.id_mesa
        WHERE rm.id_mesa = ANY(%s::integer[])
          AND r.estado IN ('confirmada', 'atendida')
          AND (%s::integer IS NULL OR r.id_reserva <> %s::integer)
          AND r.fecha_hora_inicio < %s::timestamp
          AND r.fecha_hora_fin_estimada > %s::timestamp
        LIMIT 1;
        """,
        (v_ids_unicos, p_id_reserva_excluir, p_id_reserva_excluir, p_fin, p_inicio),
    )
    v_conflicto = p_cursor.fetchone()
    if v_conflicto:
        v_num_mesa, v_id_res_conf, v_ini_conf, v_fin_conf = v_conflicto
        raise ValueError(
            f"La mesa #{v_num_mesa} ya tiene la reserva #{v_id_res_conf} "
            f"de {v_ini_conf} a {v_fin_conf}."
        )


def op_registrar_reserva(p_conexion, p_sesion: dict, p_datos: dict) -> int:
    """
    Operación transaccional que guarda la reserva y sus mesas en la misma transacción.
    """
    validar_permiso(p_sesion, ("administrador", "gerente", "mesero"))
    v_id_sucursal = validar_acceso_sucursal(p_sesion, p_datos.get("id_sucursal"))

    v_id_cliente = p_datos.get("id_cliente")
    v_inicio = p_datos.get("fecha_hora_inicio")
    v_fin = p_datos.get("fecha_hora_fin_estimada")
    v_personas = int(p_datos.get("cantidad_personas", 0))
    v_ids_mesas = p_datos.get("ids_mesas") or []

    if not v_id_cliente:
        raise ValueError("Debe indicar el cliente principal de la reserva.")
    if v_personas <= 0:
        raise ValueError("La cantidad de personas debe ser mayor que cero.")
    if not v_inicio or not v_fin:
        raise ValueError("Debe especificar fecha y hora de inicio y fin estimado.")

    with p_conexion.cursor() as v_cur:
        v_cur.execute("SELECT 1 FROM cliente WHERE id_cliente = %s::integer;", (int(v_id_cliente),))
        if not v_cur.fetchone():
            raise ValueError(f"El cliente con ID {v_id_cliente} no existe.")

        _validar_mesas_en_transaccion(
            v_cur, v_id_sucursal, v_personas, v_ids_mesas, v_inicio, v_fin
        )

        v_cur.execute(
            """
            INSERT INTO reserva (
                id_cliente, id_sucursal, fecha_hora_inicio,
                fecha_hora_fin_estimada, cantidad_personas, estado
            )
            VALUES (%s::integer, %s::integer, %s::timestamp, %s::timestamp, %s::integer, 'confirmada')
            RETURNING id_reserva;
            """,
            (int(v_id_cliente), v_id_sucursal, v_inicio, v_fin, v_personas),
        )
        v_id_reserva = v_cur.fetchone()[0]

        for v_id_mesa in v_ids_mesas:
            v_cur.execute(
                "INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (%s::integer, %s::integer);",
                (v_id_reserva, int(v_id_mesa)),
            )

        return v_id_reserva


def registrar_reserva(p_sesion: dict, p_datos: dict) -> int:
    """Registra una reserva y sus mesas usando ejecutar_transaccion."""
    return ejecutar_transaccion(p_sesion, op_registrar_reserva, p_datos)


def op_modificar_reserva(p_conexion, p_sesion: dict, p_datos: dict) -> bool:
    """
    Modifica una reserva confirmada. Si cambian las mesas, retira las anteriores
    e inserta las nuevas antes del mismo COMMIT.
    """
    validar_permiso(p_sesion, ("administrador", "gerente", "mesero"))
    v_id_reserva = p_datos.get("id_reserva")
    if not v_id_reserva:
        raise ValueError("Debe indicar el identificador de la reserva a modificar.")

    with p_conexion.cursor() as v_cur:
        v_cur.execute(
            """
            SELECT id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada,
                   cantidad_personas, estado
            FROM reserva
            WHERE id_reserva = %s::integer;
            """,
            (int(v_id_reserva),),
        )
        v_actual = v_cur.fetchone()
        if not v_actual:
            raise ValueError(f"La reserva #{v_id_reserva} no existe.")

        v_id_suc, v_ini_act, v_fin_act, v_cant_act, v_estado_act = v_actual
        validar_acceso_sucursal(p_sesion, v_id_suc)

        if v_estado_act != "confirmada":
            raise ValueError(
                f"Solo se pueden modificar reservas en estado 'confirmada' (actual: '{v_estado_act}')."
            )

        v_nuevo_ini = p_datos.get("fecha_hora_inicio") or v_ini_act
        v_nuevo_fin = p_datos.get("fecha_hora_fin_estimada") or v_fin_act

        v_nueva_cant = int(
            p_datos.get("cantidad_personas", v_cant_act)
        )

        if v_nueva_cant <= 0:
            raise ValueError(
                "La cantidad de personas debe ser mayor que cero."
            )

        v_nuevas_mesas = p_datos.get("ids_mesas")

        if v_nuevas_mesas is None:
            v_cur.execute(
                """
                SELECT id_mesa
                FROM reserva_mesa
                WHERE id_reserva = %s;
                """,
                (int(v_id_reserva),)
            )

            v_nuevas_mesas = [
                v_fila[0] for v_fila in v_cur.fetchall()
            ]

        _validar_mesas_en_transaccion(
            v_cur,
            v_id_suc,
            v_nueva_cant,
            v_nuevas_mesas,
            v_nuevo_ini,
            v_nuevo_fin,
            p_id_reserva_excluir=int(v_id_reserva),
        )

        v_cur.execute(
            """
            UPDATE reserva
            SET fecha_hora_inicio = %s::timestamp,
                fecha_hora_fin_estimada = %s::timestamp,
                cantidad_personas = %s::integer
            WHERE id_reserva = %s::integer;
            """,
            (v_nuevo_ini, v_nuevo_fin, v_nueva_cant, int(v_id_reserva)),
        )

        v_cur.execute("DELETE FROM reserva_mesa WHERE id_reserva = %s::integer;", (int(v_id_reserva),))
        for v_id_mesa in v_nuevas_mesas:
            v_cur.execute(
                "INSERT INTO reserva_mesa (id_reserva, id_mesa) VALUES (%s::integer, %s::integer);",
                (int(v_id_reserva), int(v_id_mesa)),
            )

        return True


def modificar_reserva(p_sesion: dict, p_datos: dict) -> bool:
    """Modifica una reserva mediante ejecutar_transaccion."""
    return ejecutar_transaccion(p_sesion, op_modificar_reserva, p_datos)


def op_cambiar_estado_reserva(p_conexion, p_sesion: dict, p_datos: dict) -> bool:
    """
    Cambia el estado de una reserva a 'cancelada' o 'no_asistio',
    conservando sus asignaciones históricas en reserva_mesa.
    """
    validar_permiso(p_sesion, ("administrador", "gerente", "mesero"))
    v_id_reserva = p_datos.get("id_reserva")
    v_nuevo_estado = p_datos.get("nuevo_estado", "cancelada")

    if v_nuevo_estado not in ("cancelada", "no_asistio"):
        raise ValueError("Estado no permitido en esta operación.")

    with p_conexion.cursor() as v_cur:
        v_cur.execute(
            "SELECT id_sucursal, estado FROM reserva WHERE id_reserva = %s::integer;",
            (int(v_id_reserva),),
        )
        v_fila = v_cur.fetchone()
        if not v_fila:
            raise ValueError(f"La reserva #{v_id_reserva} no existe.")

        v_id_sucursal, v_estado_actual = v_fila
        validar_acceso_sucursal(p_sesion, v_id_sucursal)

        if v_estado_actual == "atendida":
            raise ValueError("No se puede anular una reserva que ya fue atendida.")
        if v_estado_actual == v_nuevo_estado:
            raise ValueError(f"La reserva ya tiene el estado '{v_nuevo_estado}'.")

        v_cur.execute(
            "UPDATE reserva SET estado = %s::varchar WHERE id_reserva = %s::integer;",
            (v_nuevo_estado, int(v_id_reserva)),
        )
        return True


def cancelar_reserva(p_sesion: dict, p_id_reserva: int) -> bool:
    """Cancela una reserva manteniendo sus mesas históricas."""
    return ejecutar_transaccion(
        p_sesion,
        op_cambiar_estado_reserva,
        {"id_reserva": p_id_reserva, "nuevo_estado": "cancelada"},
    )


def buscar_reservas(p_sesion: dict, p_filtros: dict | None = None) -> list[dict]:
    """Busca reservas con filtros opcionales de sucursal, cliente, estado y fechas."""
    validar_permiso(p_sesion, ("administrador", "gerente", "mesero"))
    v_filtros = p_filtros or {}

    if p_sesion["rol"] == "administrador":
        v_id_sucursal = v_filtros.get("id_sucursal")
    else:
        v_id_sucursal = p_sesion["id_sucursal"]

    v_id_cliente = v_filtros.get("id_cliente")
    v_estado = v_filtros.get("estado")
    v_desde = v_filtros.get("fecha_desde")
    v_hasta = v_filtros.get("fecha_hasta")

    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                SELECT r.id_reserva,
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
                           STRING_AGG(
                               '#' || m.numero || ' (' || m.zona || ', cap:' || m.capacidad || ')',
                               ', ' ORDER BY m.numero
                           ),
                           'Sin mesas'
                       ) AS mesas_asignadas
                FROM reserva r
                JOIN cliente c ON c.id_cliente = r.id_cliente
                JOIN sucursal s ON s.id_sucursal = r.id_sucursal
                LEFT JOIN reserva_mesa rm ON rm.id_reserva = r.id_reserva
                LEFT JOIN mesa m ON m.id_mesa = rm.id_mesa
                WHERE (%s::integer IS NULL OR r.id_sucursal = %s::integer)
                  AND (%s::integer IS NULL OR r.id_cliente = %s::integer)
                  AND (%s::varchar IS NULL OR r.estado = %s::varchar)
                  AND (%s::timestamp IS NULL OR r.fecha_hora_inicio >= %s::timestamp)
                  AND (%s::timestamp IS NULL OR r.fecha_hora_inicio <= %s::timestamp)
                GROUP BY r.id_reserva, c.nombre, c.telefono, s.nombre
                ORDER BY r.fecha_hora_inicio DESC, r.id_reserva DESC;
                """,
                (
                    v_id_sucursal, v_id_sucursal,
                    v_id_cliente, v_id_cliente,
                    v_estado, v_estado,
                    v_desde, v_desde,
                    v_hasta, v_hasta,
                ),
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()


def obtener_reservas_por_cliente(
    p_sesion: dict,
    p_id_cliente: int
) -> list[dict]:
    """Consulta las reservas del cliente respetando la sucursal."""
    return buscar_reservas(
        p_sesion,
        {"id_cliente": p_id_cliente}
    )