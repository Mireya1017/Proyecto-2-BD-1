"""Proyecto 3: genera visitas y asignaciones desde los CSV de fuentes.

Entradas: sucursales.csv, mesas.csv, reservas.csv.
Salidas: visitas.csv, visitas_mesas.csv.
Ejecutar desde la raiz: python proyecto3/python/generar_visitas.py
No modifica la base de datos del Proyecto 2 ni la base OLAP.
"""
import calendar
import csv
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    from proyecto3.python.parametros import (
        FECHA_INICIO, FECHA_CORTE_EXCLUSIVA, SEMILLA_VISITAS,
        TOTAL_VISITAS, PESOS_DIA_SEMANA, PESOS_HORA, distribuir_total, HORA_APERTURA,
        HORA_CIERRE, HORA_ULTIMA_LLEGADA_SIN_RESERVA,
        DURACION_VISITA_MINUTOS_MIN, DURACION_VISITA_MINUTOS_MAX,
        DESFASE_LLEGADA_MINUTOS_MIN, DESFASE_LLEGADA_MINUTOS_MAX,
        LIBERACION_MINUTOS_MIN, LIBERACION_MINUTOS_MAX,
        PERSONAS_POR_GRUPO, PROBABILIDADES_PERSONAS,
    )
except ModuleNotFoundError as v_error:
    # Permite ejecutar el archivo desde la raiz o importarlo como paquete.
    if v_error.name not in ('proyecto3', 'proyecto3.python'):
        raise
    from parametros import (
        FECHA_INICIO, FECHA_CORTE_EXCLUSIVA, SEMILLA_VISITAS,
        TOTAL_VISITAS, PESOS_DIA_SEMANA, PESOS_HORA, distribuir_total, HORA_APERTURA,
        HORA_CIERRE, HORA_ULTIMA_LLEGADA_SIN_RESERVA,
        DURACION_VISITA_MINUTOS_MIN, DURACION_VISITA_MINUTOS_MAX,
        DESFASE_LLEGADA_MINUTOS_MIN, DESFASE_LLEGADA_MINUTOS_MAX,
        LIBERACION_MINUTOS_MIN, LIBERACION_MINUTOS_MAX,
        PERSONAS_POR_GRUPO, PROBABILIDADES_PERSONAS,
    )

FORMATO_FECHA = '%Y-%m-%d %H:%M:%S'
CAMPOS_SUCURSALES = ('id_sucursal', 'nombre', 'direccion')
CAMPOS_MESAS = ('id_mesa', 'id_sucursal', 'numero', 'capacidad', 'zona')
CAMPOS_RESERVAS = ('id_reserva', 'id_sucursal', 'fecha_hora_inicio',
                   'fecha_hora_fin_estimada', 'cantidad_personas', 'estado')
CAMPOS_VISITAS = ('id_visita', 'id_sucursal', 'id_reserva',
                  'fecha_hora_llegada', 'fecha_hora_salida', 'cantidad_personas')
CAMPOS_ASIGNACIONES = ('id_visita', 'id_mesa', 'fecha_hora_liberacion')


class ErrorPlanificacion(Exception):
    """No se encontro una asignacion compatible con los horarios y las mesas."""


def leer_csv(p_ruta, p_campos):
    v_ruta = Path(p_ruta)
    with v_ruta.open('r', encoding='utf-8-sig', newline='') as v_archivo:
        v_lector = csv.DictReader(v_archivo)
        if tuple(v_lector.fieldnames or ()) != tuple(p_campos):
            raise ValueError(f'Encabezados incorrectos en {v_ruta.name}: {v_lector.fieldnames}')
        v_filas = list(v_lector)
    for v_numero, v_fila in enumerate(v_filas, start=2):
        if None in v_fila or any(v_fila[v_campo] is None for v_campo in p_campos):
            raise ValueError(f'{v_ruta.name}, fila {v_numero}: columnas incompletas')
    return v_filas


def convertir_entero_positivo(p_valor, p_campo):
    try:
        v_entero = int(p_valor)
    except (TypeError, ValueError) as v_error:
        raise ValueError(f'{p_campo} debe ser entero positivo: {p_valor}') from v_error
    if v_entero <= 0:
        raise ValueError(f'{p_campo} debe ser positivo: {p_valor}')
    return v_entero


def convertir_fecha_hora(p_texto):
    try:
        return datetime.strptime(p_texto, FORMATO_FECHA)
    except (TypeError, ValueError) as v_error:
        raise ValueError(f'Fecha y hora invalida: {p_texto}') from v_error


def validar_catalogos(p_sucursales, p_mesas):
    v_sucursales = set()
    for v_fila in p_sucursales:
        v_id = convertir_entero_positivo(v_fila['id_sucursal'], 'id_sucursal')
        if v_id in v_sucursales:
            raise ValueError(f'Sucursal duplicada: {v_id}')
        v_sucursales.add(v_id)
    if not v_sucursales:
        raise ValueError('No hay sucursales')
    v_mesas = []
    v_ids = set()
    v_numeros = set()
    for v_fila in p_mesas:
        v_id = convertir_entero_positivo(v_fila['id_mesa'], 'id_mesa')
        v_sucursal = convertir_entero_positivo(v_fila['id_sucursal'], 'id_sucursal')
        v_capacidad = convertir_entero_positivo(v_fila['capacidad'], 'capacidad')
        v_numero = convertir_entero_positivo(v_fila['numero'], 'numero')
        if v_id in v_ids or (v_sucursal, v_numero) in v_numeros:
            raise ValueError(f'Mesa duplicada: {v_id}')
        if v_sucursal not in v_sucursales:
            raise ValueError(f'Mesa {v_id}: sucursal inexistente')
        v_ids.add(v_id)
        v_numeros.add((v_sucursal, v_numero))
        v_mesas.append({'id_mesa': v_id, 'id_sucursal': v_sucursal,
                        'capacidad': v_capacidad})
    for v_sucursal in v_sucursales:
        if not any(v_mesa['id_sucursal'] == v_sucursal for v_mesa in v_mesas):
            raise ValueError(f'Sucursal {v_sucursal} sin mesas')
    return sorted(v_sucursales), sorted(v_mesas, key=lambda v_mesa: v_mesa['id_mesa'])


def validar_reservas(p_reservas, p_sucursales, p_fecha_inicio, p_fecha_corte_exclusiva):
    v_ids = set()
    v_horarios = set()
    v_resultado = []
    for v_fila in p_reservas:
        v_id = convertir_entero_positivo(v_fila['id_reserva'], 'id_reserva')
        v_sucursal = convertir_entero_positivo(v_fila['id_sucursal'], 'id_sucursal')
        v_personas = convertir_entero_positivo(v_fila['cantidad_personas'], 'cantidad_personas')
        v_inicio = convertir_fecha_hora(v_fila['fecha_hora_inicio'])
        v_fin = convertir_fecha_hora(v_fila['fecha_hora_fin_estimada'])
        v_estado = v_fila['estado']
        if v_id in v_ids:
            raise ValueError(f'Reserva duplicada: {v_id}')
        if v_sucursal not in p_sucursales:
            raise ValueError(f'Reserva {v_id}: sucursal inexistente')
        if not 1 <= v_personas <= 8:
            raise ValueError(f'Reserva {v_id}: personas fuera de 1..8')
        if not p_fecha_inicio <= v_inicio.date() < p_fecha_corte_exclusiva or v_fin <= v_inicio:
            raise ValueError(f'Reserva {v_id}: fechas invalidas')
        if v_estado not in ('atendida', 'cancelada', 'no_asistio'):
            raise ValueError(f'Reserva {v_id}: estado invalido')
        if (v_sucursal, v_inicio) in v_horarios:
            raise ValueError(f'Reserva {v_id}: horario duplicado')
        v_horarios.add((v_sucursal, v_inicio))
        v_ids.add(v_id)
        v_resultado.append({'id_reserva': v_id, 'id_sucursal': v_sucursal,
                            'cantidad_personas': v_personas,
                            'fecha_hora_inicio': v_inicio, 'fecha_hora_fin_estimada': v_fin,
                            'estado': v_estado})
    return sorted(v_resultado, key=lambda v_r: (v_r['fecha_hora_inicio'], v_r['id_reserva']))


def obtener_meses(p_fecha_inicio, p_fecha_corte_exclusiva):
    v_anio, v_mes = p_fecha_inicio.year, p_fecha_inicio.month
    while (v_anio, v_mes) <= (p_fecha_corte_exclusiva.year, p_fecha_corte_exclusiva.month):
        v_primero = datetime(v_anio, v_mes, 1).date()
        v_ultimo = datetime(v_anio, v_mes, calendar.monthrange(v_anio, v_mes)[1]).date()
        v_inicio = max(v_primero, p_fecha_inicio)
        v_fin = min(v_ultimo, p_fecha_corte_exclusiva - timedelta(days=1))
        if v_inicio <= v_fin:
            yield v_inicio, v_fin
        v_mes += 1
        if v_mes == 13:
            v_mes, v_anio = 1, v_anio + 1


def hay_superposicion(p_inicio_1, p_fin_1, p_inicio_2, p_fin_2):
    return p_inicio_1 < p_fin_2 and p_inicio_2 < p_fin_1


def seleccionar_mesas(p_mesas_disponibles, p_personas):
    """Menor capacidad suficiente; luego menos mesas; luego IDs menores.

    Programacion dinamica por capacidad, para evitar 2**N combinaciones.
    """
    v_opciones = {0: ()}
    for v_mesa in sorted(p_mesas_disponibles, key=lambda v_m: v_m['id_mesa']):
        v_nuevas = dict(v_opciones)
        for v_capacidad, v_ids in v_opciones.items():
            v_total = v_capacidad + v_mesa['capacidad']
            v_candidata = v_ids + (v_mesa['id_mesa'],)
            v_anterior = v_nuevas.get(v_total)
            if v_anterior is None or (len(v_candidata), v_candidata) < (len(v_anterior), v_anterior):
                v_nuevas[v_total] = v_candidata
        v_opciones = v_nuevas
    v_validas = [(v_cap, len(v_ids), v_ids) for v_cap, v_ids in v_opciones.items()
                 if v_cap >= p_personas]
    return min(v_validas)[2] if v_validas else None


def asignar_mesas_visitas(p_visitas, p_mesas, p_aleatorio, p_fecha_corte_exclusiva):
    v_ocupaciones = defaultdict(list)
    v_asignaciones = []
    v_corte = datetime.combine(p_fecha_corte_exclusiva, datetime.min.time())
    for v_visita in sorted(p_visitas, key=lambda v_v: (v_v['fecha_hora_llegada'], v_v['id_visita'])):
        v_llegada = v_visita['fecha_hora_llegada']
        v_salida = v_visita['fecha_hora_salida']
        v_liberacion_max = v_salida + timedelta(minutes=LIBERACION_MINUTOS_MAX)
        if v_liberacion_max >= v_corte or v_liberacion_max.time() > HORA_CIERRE:
            raise ErrorPlanificacion(f'Visita {v_visita["id_visita"]}: fuera de horario/corte')
        v_disponibles = [v_mesa for v_mesa in p_mesas
                         if v_mesa['id_sucursal'] == v_visita['id_sucursal']
                         and all(not hay_superposicion(v_llegada, v_liberacion_max, v_a, v_b)
                                 for v_a, v_b in v_ocupaciones[v_mesa['id_mesa']])]
        v_ids = seleccionar_mesas(v_disponibles, v_visita['cantidad_personas'])
        if v_ids is None:
            raise ErrorPlanificacion(f'Visita {v_visita["id_visita"]}: sin mesas disponibles')
        for v_id in v_ids:
            v_liberacion = v_salida + timedelta(minutes=p_aleatorio.randint(
                LIBERACION_MINUTOS_MIN, LIBERACION_MINUTOS_MAX))
            v_ocupaciones[v_id].append((v_llegada, v_liberacion))
            v_asignaciones.append({'id_visita': v_visita['id_visita'],
                                  'id_mesa': v_id, 'fecha_hora_liberacion': v_liberacion})
    return v_asignaciones


def construir_ocupaciones(p_visitas, p_asignaciones):
    v_visitas_por_id = {
        v_visita["id_visita"]: v_visita
        for v_visita in p_visitas
    }

    v_ocupaciones = defaultdict(list)

    for v_asignacion in p_asignaciones:
        v_id_visita = v_asignacion["id_visita"]
        v_id_mesa = v_asignacion["id_mesa"]

        v_visita = v_visitas_por_id[v_id_visita]

        v_ocupaciones[v_id_mesa].append((
            v_visita["fecha_hora_llegada"],
            v_asignacion["fecha_hora_liberacion"]
        ))

    return v_ocupaciones


def buscar_mesas_para_visita(
    p_visita,
    p_mesas,
    p_ocupaciones
):
    v_llegada = p_visita["fecha_hora_llegada"]

    v_liberacion_maxima = (
        p_visita["fecha_hora_salida"]
        + timedelta(minutes=LIBERACION_MINUTOS_MAX)
    )

    v_disponibles = []

    for v_mesa in p_mesas:
        if v_mesa["id_sucursal"] != p_visita["id_sucursal"]:
            continue

        v_id_mesa = v_mesa["id_mesa"]

        v_ocupada = any(
            hay_superposicion(
                v_llegada,
                v_liberacion_maxima,
                v_inicio,
                v_fin
            )
            for v_inicio, v_fin
            in p_ocupaciones[v_id_mesa]
        )

        if not v_ocupada:
            v_disponibles.append(v_mesa)

    return seleccionar_mesas(
        v_disponibles,
        p_visita["cantidad_personas"]
    )


def obtener_cantidades_sin_reserva(
    p_sucursales, p_reservas, p_fecha_inicio, p_fecha_corte_exclusiva
):
    """Completa el total global de visitas sin imponer 100 por sucursal/mes.

    Cada reserva atendida origina una visita. Las restantes son sin reserva
    y se distribuyen segun el volumen de reservas de cada sucursal/mes.
    """
    v_atendidas = sum(v_r['estado'] == 'atendida' for v_r in p_reservas)
    v_total_sin = TOTAL_VISITAS - v_atendidas
    if v_total_sin < 0:
        raise ValueError('Las reservas atendidas superan TOTAL_VISITAS.')
    v_conteos = Counter(
        (v_r['id_sucursal'], v_r['fecha_hora_inicio'].year,
         v_r['fecha_hora_inicio'].month) for v_r in p_reservas
    )
    v_claves = [
        (v_sucursal, v_inicio.year, v_inicio.month)
        for v_sucursal in sorted(p_sucursales)
        for v_inicio, _ in obtener_meses(p_fecha_inicio, p_fecha_corte_exclusiva)
    ]
    v_pesos = [max(1, v_conteos[v_clave]) for v_clave in v_claves]
    return distribuir_total(v_total_sin, v_claves, v_pesos)


def planificar_visitas_sin_reserva(
    p_sucursales,
    p_mesas,
    p_visitas_reserva,
    p_asignaciones_reserva,
    p_reservas,
    p_fecha_inicio,
    p_fecha_corte_exclusiva,
    p_aleatorio
):
    v_ocupaciones = construir_ocupaciones(
        p_visitas_reserva,
        p_asignaciones_reserva
    )

    v_visitas = []
    v_asignaciones = []

    v_id_siguiente = len(p_visitas_reserva) + 1

    v_hora_min = (
        HORA_APERTURA.hour * 60
        + HORA_APERTURA.minute
    )

    v_hora_max = (
        HORA_ULTIMA_LLEGADA_SIN_RESERVA.hour * 60
        + HORA_ULTIMA_LLEGADA_SIN_RESERVA.minute
    )

    v_corte = datetime.combine(
        p_fecha_corte_exclusiva,
        datetime.min.time()
    )

    v_cantidades = obtener_cantidades_sin_reserva(
        p_sucursales, p_reservas, p_fecha_inicio, p_fecha_corte_exclusiva
    )
    v_minutos = list(range(v_hora_min, v_hora_max + 1))
    v_pesos_minutos = [PESOS_HORA[v_minuto // 60] for v_minuto in v_minutos]

    for v_sucursal in sorted(p_sucursales):
        for v_inicio_mes, v_fin_mes in obtener_meses(
            p_fecha_inicio,
            p_fecha_corte_exclusiva
        ):
            v_fechas = [
                v_inicio_mes + timedelta(days=v_dia)
                for v_dia in range((v_fin_mes - v_inicio_mes).days + 1)
            ]
            v_pesos_fechas = [PESOS_DIA_SEMANA[v_fecha.weekday()]
                               for v_fecha in v_fechas]
            v_cantidad = v_cantidades[(v_sucursal, v_inicio_mes.year, v_inicio_mes.month)]
            for _ in range(v_cantidad):
                v_personas = p_aleatorio.choices(
                    PERSONAS_POR_GRUPO,
                    weights=PROBABILIDADES_PERSONAS,
                    k=1
                )[0]

                v_encontrada = False
                v_dias = (v_fin_mes - v_inicio_mes).days + 1

                for v_intento in range(500):
                    v_fecha = p_aleatorio.choices(
                        v_fechas, weights=v_pesos_fechas, k=1
                    )[0]
                    v_minuto = p_aleatorio.choices(
                        v_minutos, weights=v_pesos_minutos, k=1
                    )[0]

                    v_llegada = datetime.combine(
                        v_fecha,
                        datetime.min.time()
                    ) + timedelta(minutes=v_minuto)

                    v_duracion = p_aleatorio.randint(
                        DURACION_VISITA_MINUTOS_MIN,
                        DURACION_VISITA_MINUTOS_MAX
                    )

                    v_salida = v_llegada + timedelta(
                        minutes=v_duracion
                    )

                    v_liberacion_maxima = v_salida + timedelta(
                        minutes=LIBERACION_MINUTOS_MAX
                    )

                    if v_liberacion_maxima >= v_corte:
                        continue

                    if v_liberacion_maxima.time() > HORA_CIERRE:
                        continue

                    v_visita = {
                        "id_visita": v_id_siguiente,
                        "id_sucursal": v_sucursal,
                        "id_reserva": None,
                        "fecha_hora_llegada": v_llegada,
                        "fecha_hora_salida": v_salida,
                        "cantidad_personas": v_personas
                    }

                    v_ids_mesas = buscar_mesas_para_visita(
                        v_visita,
                        p_mesas,
                        v_ocupaciones
                    )

                    if v_ids_mesas is None:
                        continue

                    for v_id_mesa in v_ids_mesas:
                        v_minutos_liberacion = p_aleatorio.randint(
                            LIBERACION_MINUTOS_MIN,
                            LIBERACION_MINUTOS_MAX
                        )

                        v_liberacion = v_salida + timedelta(
                            minutes=v_minutos_liberacion
                        )

                        v_asignaciones.append({
                            "id_visita": v_id_siguiente,
                            "id_mesa": v_id_mesa,
                            "fecha_hora_liberacion": v_liberacion
                        })

                        v_ocupaciones[v_id_mesa].append(
                            (v_llegada, v_liberacion)
                        )

                    v_visitas.append(v_visita)
                    v_id_siguiente += 1
                    v_encontrada = True
                    break

                if not v_encontrada:
                    raise ErrorPlanificacion(
                        f"No se encontró horario para una visita "
                        f"sin reserva en sucursal {v_sucursal}, "
                        f"mes {v_inicio_mes.month}."
                    )

    return v_visitas, v_asignaciones


def planificar_reservas(
    p_reservas,
    p_mesas,
    p_aleatorio,
    p_fecha_corte_exclusiva
):
    v_visitas = generar_visitas_con_reserva(
        p_reservas,
        p_aleatorio,
        p_fecha_corte_exclusiva
    )

    v_asignaciones = asignar_mesas_visitas(
        v_visitas,
        p_mesas,
        p_aleatorio,
        p_fecha_corte_exclusiva
    )

    return v_visitas, v_asignaciones
 

def generar_visitas_con_reserva(
    p_reservas,
    p_aleatorio,
    p_fecha_corte_exclusiva
):
    v_visitas = []

    v_corte = datetime.combine(
        p_fecha_corte_exclusiva,
        datetime.min.time()
    )

    for v_reserva in p_reservas:
        if v_reserva["estado"] != "atendida":
            continue

        v_inicio = v_reserva["fecha_hora_inicio"]

        v_desfase = p_aleatorio.randint(
            DESFASE_LLEGADA_MINUTOS_MIN,
            DESFASE_LLEGADA_MINUTOS_MAX
        )

        v_llegada = v_inicio + timedelta(
            minutes=v_desfase
        )

        v_apertura = datetime.combine(
            v_inicio.date(),
            HORA_APERTURA
        )

        if v_llegada < v_apertura:
            v_llegada = v_apertura

        v_desfase_real = (
            v_llegada - v_inicio
        ).total_seconds() / 60

        if not (
            DESFASE_LLEGADA_MINUTOS_MIN
            <= v_desfase_real
            <= DESFASE_LLEGADA_MINUTOS_MAX
        ):
            raise ErrorPlanificacion(
                f"Reserva {v_reserva['id_reserva']}: "
                "llegada fuera del rango permitido."
        )

        v_duracion = p_aleatorio.randint(
            DURACION_VISITA_MINUTOS_MIN,
            DURACION_VISITA_MINUTOS_MAX
        )

        v_salida = v_llegada + timedelta(
            minutes=v_duracion
        )

        v_liberacion_maxima = v_salida + timedelta(
            minutes=LIBERACION_MINUTOS_MAX
        )

        if v_liberacion_maxima >= v_corte:
            raise ValueError(
                f"La reserva {v_reserva['id_reserva']} "
                "genera una visita fuera del período."
            )

        v_visitas.append({
            "id_visita": len(v_visitas) + 1,
            "id_sucursal": v_reserva["id_sucursal"],
            "id_reserva": v_reserva["id_reserva"],
            "fecha_hora_llegada": v_llegada,
            "fecha_hora_salida": v_salida,
            "cantidad_personas": v_reserva["cantidad_personas"]
        })

    return v_visitas


def validar_resultados(p_visitas, p_asignaciones, p_reservas, p_mesas,
                        p_fecha_inicio, p_fecha_corte_exclusiva):
    v_corte = datetime.combine(p_fecha_corte_exclusiva, datetime.min.time())
    v_mesas = {v_m['id_mesa']: v_m for v_m in p_mesas}
    v_asig_por_visita = defaultdict(list)
    v_ocupaciones = defaultdict(list)
    v_ids = set()
    v_reservas_atendidas = {v_r['id_reserva']: v_r for v_r in p_reservas if v_r['estado'] == 'atendida'}
    v_usadas = set()
    for v_visita in p_visitas:
        v_id = v_visita['id_visita']
        if v_id in v_ids:
            raise ValueError(f'Visita duplicada: {v_id}')
        v_ids.add(v_id)
        v_llegada, v_salida = v_visita['fecha_hora_llegada'], v_visita['fecha_hora_salida']
        if not (p_fecha_inicio <= v_llegada.date() < p_fecha_corte_exclusiva
                and v_llegada < v_salida < v_corte):
            raise ValueError(f'Visita {v_id}: fechas invalidas')
        if not (DURACION_VISITA_MINUTOS_MIN <= (v_salida - v_llegada).total_seconds()/60
                <= DURACION_VISITA_MINUTOS_MAX):
            raise ValueError(f'Visita {v_id}: duracion invalida')
        if v_visita['id_reserva'] is not None:
            v_reserva = v_reservas_atendidas.get(v_visita['id_reserva'])
            if v_reserva is None or v_visita['id_reserva'] in v_usadas:
                raise ValueError(f'Visita {v_id}: reserva inexistente o repetida')
            v_usadas.add(v_visita['id_reserva'])
            if (v_reserva['id_sucursal'], v_reserva['cantidad_personas']) != (v_visita['id_sucursal'], v_visita['cantidad_personas']):
                raise ValueError(f'Visita {v_id}: sucursal/personas no coinciden con reserva')
            v_desfase = (v_llegada - v_reserva['fecha_hora_inicio']).total_seconds()/60
            if not (DESFASE_LLEGADA_MINUTOS_MIN <= v_desfase <= DESFASE_LLEGADA_MINUTOS_MAX):
                raise ValueError(f'Visita {v_id}: desfase invalido')
        elif v_llegada.time() > HORA_ULTIMA_LLEGADA_SIN_RESERVA:
            raise ValueError(f'Visita {v_id}: llegada sin reserva demasiado tarde')
    if v_usadas != set(v_reservas_atendidas):
        raise ValueError('No hay exactamente una visita por reserva atendida')
    for v_asig in p_asignaciones:
        v_id, v_mesa_id = v_asig['id_visita'], v_asig['id_mesa']
        if v_id not in v_ids or v_mesa_id not in v_mesas:
            raise ValueError('Asignacion con visita o mesa inexistente')
        if any(v_a['id_mesa'] == v_mesa_id for v_a in v_asig_por_visita[v_id]):
            raise ValueError(f'Asignacion duplicada visita {v_id}, mesa {v_mesa_id}')
        v_asig_por_visita[v_id].append(v_asig)
    for v_visita in p_visitas:
        v_id = v_visita['id_visita']
        v_asigs = v_asig_por_visita[v_id]
        if not v_asigs:
            raise ValueError(f'Visita {v_id} sin mesas')
        if sum(v_mesas[v_a['id_mesa']]['capacidad'] for v_a in v_asigs) < v_visita['cantidad_personas']:
            raise ValueError(f'Visita {v_id}: capacidad insuficiente')
        for v_a in v_asigs:
            v_mesa = v_mesas[v_a['id_mesa']]
            if v_mesa['id_sucursal'] != v_visita['id_sucursal']:
                raise ValueError(f'Visita {v_id}: mesa de otra sucursal')
            v_lib = v_a['fecha_hora_liberacion']
            v_minutos = (v_lib - v_visita['fecha_hora_salida']).total_seconds()/60
            if not LIBERACION_MINUTOS_MIN <= v_minutos <= LIBERACION_MINUTOS_MAX or v_lib >= v_corte or v_lib.time() > HORA_CIERRE:
                raise ValueError(f'Visita {v_id}: liberacion invalida')
            v_ocupaciones[v_a['id_mesa']].append((v_visita['fecha_hora_llegada'], v_lib, v_id))
    for v_mesa_id, v_intervalos in v_ocupaciones.items():
        v_intervalos.sort()
        for v_anterior, v_siguiente in zip(v_intervalos, v_intervalos[1:]):
            if v_anterior[1] > v_siguiente[0]:
                raise ValueError(f'Mesa {v_mesa_id}: visitas {v_anterior[2]} y {v_siguiente[2]} superpuestas')
    v_esperadas = obtener_cantidades_sin_reserva(
        {v_m['id_sucursal'] for v_m in p_mesas}, p_reservas,
        p_fecha_inicio, p_fecha_corte_exclusiva
    )
    if len(p_visitas) != TOTAL_VISITAS:
        raise ValueError('Cantidad total de visitas incorrecta')
    v_conteos = Counter((v_v['id_sucursal'], v_v['fecha_hora_llegada'].year,
                         v_v['fecha_hora_llegada'].month) for v_v in p_visitas if v_v['id_reserva'] is None)
    for v_sucursal in {v_m['id_sucursal'] for v_m in p_mesas}:
        for v_mes_inicio, _ in obtener_meses(p_fecha_inicio, p_fecha_corte_exclusiva):
            v_clave = (v_sucursal, v_mes_inicio.year, v_mes_inicio.month)
            if v_conteos[v_clave] != v_esperadas[v_clave]:
                raise ValueError('Cantidad incorrecta de visitas sin reserva por mes y sucursal')



def planificar_con_reintentos(
    p_reservas,
    p_sucursales,
    p_mesas,
    p_fecha_inicio,
    p_fecha_corte_exclusiva,
    p_semilla,
    p_max_intentos=100
):
    v_ultimo_error = None

    for v_intento in range(p_max_intentos):
        v_aleatorio = random.Random(
            p_semilla + v_intento
        )

        try:
            # Primero planificar las reservas atendidas.
            v_visitas_reserva, v_asignaciones_reserva = (
                planificar_reservas(
                    p_reservas,
                    p_mesas,
                    v_aleatorio,
                    p_fecha_corte_exclusiva
                )
            )

            # Después agregar visitas sin reserva.
            v_visitas_sin, v_asignaciones_sin = (
                planificar_visitas_sin_reserva(
                    p_sucursales,
                    p_mesas,
                    v_visitas_reserva,
                    v_asignaciones_reserva,
                    p_reservas,
                    p_fecha_inicio,
                    p_fecha_corte_exclusiva,
                    v_aleatorio
                )
            )

            v_visitas = (
                v_visitas_reserva + v_visitas_sin
            )

            v_asignaciones = (
                v_asignaciones_reserva + v_asignaciones_sin
            )

            validar_resultados(
                v_visitas,
                v_asignaciones,
                p_reservas,
                p_mesas,
                p_fecha_inicio,
                p_fecha_corte_exclusiva
            )

            return v_visitas, v_asignaciones

        except ErrorPlanificacion as v_error:
            v_ultimo_error = v_error

    raise ErrorPlanificacion(
        f"No fue posible completar la planificación "
        f"después de {p_max_intentos} intentos. "
        f"Último conflicto: {v_ultimo_error}"
    )


def escribir_csv(p_ruta, p_campos, p_filas):
    v_ruta = Path(p_ruta)
    with v_ruta.open('w', encoding='utf-8', newline='') as v_archivo:
        v_escritor = csv.DictWriter(v_archivo, fieldnames=p_campos)
        v_escritor.writeheader()
        for v_fila in p_filas:
            v_escritor.writerow({v_campo: (v_fila[v_campo].strftime(FORMATO_FECHA)
                                            if isinstance(v_fila[v_campo], datetime)
                                            else '' if v_fila[v_campo] is None
                                            else v_fila[v_campo]) for v_campo in p_campos})


def generar_visitas(p_directorio_fuentes, p_fecha_inicio, p_fecha_corte_exclusiva, p_semilla):
    """Genera y valida las visitas; devuelve conteos de visitas y asignaciones."""
    if p_fecha_inicio >= p_fecha_corte_exclusiva:
        raise ValueError('Periodo invalido')
    v_directorio = Path(p_directorio_fuentes)
    v_sucursales_crudas = leer_csv(v_directorio / 'sucursales.csv', CAMPOS_SUCURSALES)
    v_mesas_crudas = leer_csv(v_directorio / 'mesas.csv', CAMPOS_MESAS)
    v_reservas_crudas = leer_csv(v_directorio / 'reservas.csv', CAMPOS_RESERVAS)
    v_sucursales, v_mesas = validar_catalogos(v_sucursales_crudas, v_mesas_crudas)
    v_reservas = validar_reservas(v_reservas_crudas, v_sucursales,
                                 p_fecha_inicio, p_fecha_corte_exclusiva)
    v_capacidades = defaultdict(int)
    for v_mesa in v_mesas:
        v_capacidades[v_mesa['id_sucursal']] += v_mesa['capacidad']
    if any(v_reserva['cantidad_personas'] > v_capacidades[v_reserva['id_sucursal']]
           for v_reserva in v_reservas):
        raise ValueError('Reserva con grupo mayor que la capacidad de su sucursal')
    if max(PERSONAS_POR_GRUPO) > min(v_capacidades.values()):
        raise ValueError('Capacidad insuficiente para tamanos de grupo acordados')
    v_visitas, v_asignaciones = planificar_con_reintentos(
        v_reservas, v_sucursales, v_mesas,
        p_fecha_inicio, p_fecha_corte_exclusiva, p_semilla)
    # Los dos archivos se escriben solo despues de validar todos los datos.
    escribir_csv(v_directorio / 'visitas.csv', CAMPOS_VISITAS,
                 sorted(v_visitas, key=lambda v_v: v_v['id_visita']))
    escribir_csv(v_directorio / 'visitas_mesas.csv', CAMPOS_ASIGNACIONES,
                 sorted(v_asignaciones, key=lambda v_a: (v_a['id_visita'], v_a['id_mesa'])))
    return {'visitas_generadas': len(v_visitas),
            'asignaciones_generadas': len(v_asignaciones)}


if __name__ == '__main__':
    v_fuentes = Path(__file__).resolve().parent.parent / 'fuentes'
    print(generar_visitas(v_fuentes, FECHA_INICIO, FECHA_CORTE_EXCLUSIVA, SEMILLA_VISITAS))
