"""Proyecto 3 - ETL del DataMart de reservas y visitas.

Entradas: los cinco CSV en proyecto3/fuentes (o fuentes/ejemplo).
Salida: dimensiones y hechos en restaurante_olap, conteos por archivo/tabla.
Ejecucion: python proyecto3/python/cargar_datamart.py
Requiere el SQL oficial 01_modelo_estrella.sql ejecutado previamente.
Nunca escribe en la base operativa del Proyecto 2.
"""
import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from proyecto3.python.conexion import obtener_conexion
    from proyecto3.python.parametros import (
        FECHA_INICIO, FECHA_CORTE_EXCLUSIVA, HORA_APERTURA, HORA_CIERRE,
        HORA_PRIMERA_RESERVA, HORA_ULTIMA_RESERVA,
        HORA_ULTIMA_LLEGADA_SIN_RESERVA,
        DURACION_ESTIMADA_RESERVA_MINUTOS,
        DESFASE_LLEGADA_MINUTOS_MIN, DESFASE_LLEGADA_MINUTOS_MAX,
        DURACION_VISITA_MINUTOS_MIN, DURACION_VISITA_MINUTOS_MAX,
        LIBERACION_MINUTOS_MIN, LIBERACION_MINUTOS_MAX,
    )
except ModuleNotFoundError as v_error:
    if v_error.name not in ('proyecto3', 'proyecto3.python'):
        raise
    from conexion import obtener_conexion
    from parametros import (
        FECHA_INICIO, FECHA_CORTE_EXCLUSIVA, HORA_APERTURA, HORA_CIERRE,
        HORA_PRIMERA_RESERVA, HORA_ULTIMA_RESERVA,
        HORA_ULTIMA_LLEGADA_SIN_RESERVA,
        DURACION_ESTIMADA_RESERVA_MINUTOS,
        DESFASE_LLEGADA_MINUTOS_MIN, DESFASE_LLEGADA_MINUTOS_MAX,
        DURACION_VISITA_MINUTOS_MIN, DURACION_VISITA_MINUTOS_MAX,
        LIBERACION_MINUTOS_MIN, LIBERACION_MINUTOS_MAX,
    )

FORMATO_FECHA_HORA = '%Y-%m-%d %H:%M:%S'
CAMPOS = {
    'sucursales.csv': ('id_sucursal', 'nombre', 'direccion'),
    'mesas.csv': ('id_mesa', 'id_sucursal', 'numero', 'capacidad', 'zona'),
    'reservas.csv': ('id_reserva', 'id_sucursal', 'fecha_hora_inicio',
                     'fecha_hora_fin_estimada', 'cantidad_personas', 'estado'),
    'visitas.csv': ('id_visita', 'id_sucursal', 'id_reserva',
                    'fecha_hora_llegada', 'fecha_hora_salida', 'cantidad_personas'),
    'visitas_mesas.csv': ('id_visita', 'id_mesa', 'fecha_hora_liberacion'),
}
COLUMNAS_TABLAS = {
    'dim_sucursal': ('id_sucursal', 'nombre', 'direccion'),
    'dim_mesa': ('id_mesa', 'id_sucursal', 'numero', 'capacidad', 'zona'),
    'dim_fecha': ('id_fecha', 'fecha', 'anio', 'mes', 'nombre_mes', 'dia_mes', 'dia_semana', 'nombre_dia'),
    'dim_hora': ('id_hora', 'etiqueta'),
    'fact_reserva': ('id_reserva', 'id_sucursal', 'id_fecha', 'id_hora',
                     'fecha_hora_inicio', 'fecha_hora_fin_estimada', 'cantidad_personas', 'estado'),
    'fact_visita': ('id_visita', 'id_sucursal', 'id_fecha', 'id_hora', 'id_reserva_origen',
                    'fecha_hora_llegada', 'fecha_hora_salida', 'cantidad_personas', 'capacidad_asignada'),
    'fact_uso_mesa': ('id_visita_origen', 'id_mesa', 'id_sucursal', 'id_fecha',
                      'fecha_hora_llegada', 'fecha_hora_salida', 'fecha_hora_liberacion'),
}
MESES = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre')
DIAS = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')


class ErrorFuente(ValueError):
    def __init__(self, p_archivo, p_fila, p_campo, p_motivo):
        self.archivo, self.fila, self.campo, self.motivo = p_archivo, p_fila, p_campo, p_motivo
        super().__init__(f'{p_archivo}, fila {p_fila}, {p_campo}: {p_motivo}')


def error(p_archivo, p_fila, p_campo, p_motivo):
    raise ErrorFuente(p_archivo, p_fila, p_campo, p_motivo)


def leer_fuente(p_ruta, p_campos):
    v_ruta = Path(p_ruta)
    if not v_ruta.is_file():
        error(v_ruta.name, 1, 'archivo', 'No existe el archivo')
    with v_ruta.open('r', encoding='utf-8-sig', newline='') as v_archivo:
        v_lector = csv.DictReader(v_archivo)
        if tuple(v_lector.fieldnames or ()) != tuple(p_campos):
            error(v_ruta.name, 1, 'encabezado', f'Se esperaban {list(p_campos)}; se encontraron {v_lector.fieldnames}')
        v_filas = []
        for v_numero, v_fila in enumerate(v_lector, start=2):
            if None in v_fila or any(v_fila.get(v_campo) is None for v_campo in p_campos):
                error(v_ruta.name, v_numero, 'columnas', 'Cantidad de columnas incorrecta')
            for v_campo in p_campos:
                if v_fila[v_campo] == '' and not (v_ruta.name == 'visitas.csv' and v_campo == 'id_reserva'):
                    error(v_ruta.name, v_numero, v_campo, 'Campo obligatorio vacío')
            v_filas.append(v_fila)
    return v_filas


def entero(p_fila, p_campo, p_archivo, p_numero, p_opcional=False):
    v_texto = p_fila[p_campo]
    if p_opcional and v_texto == '':
        return None
    try:
        v_valor = int(v_texto)
    except (ValueError, TypeError):
        error(p_archivo, p_numero, p_campo, f'Entero inválido: {v_texto}')
    if v_valor <= 0:
        error(p_archivo, p_numero, p_campo, 'Debe ser positivo')
    return v_valor


def fecha_hora(p_fila, p_campo, p_archivo, p_numero):
    try:
        return datetime.strptime(p_fila[p_campo], FORMATO_FECHA_HORA)
    except (TypeError, ValueError):
        error(p_archivo, p_numero, p_campo, f'Fecha inválida: {p_fila[p_campo]}')


def transformar(p_fuentes):
    v_convertidos = {}
    v_numericos = {
        'sucursales.csv': ('id_sucursal',),
        'mesas.csv': ('id_mesa', 'id_sucursal', 'numero', 'capacidad'),
        'reservas.csv': ('id_reserva', 'id_sucursal', 'cantidad_personas'),
        'visitas.csv': ('id_visita', 'id_sucursal', 'id_reserva', 'cantidad_personas'),
        'visitas_mesas.csv': ('id_visita', 'id_mesa'),
    }
    v_fechas = {
        'reservas.csv': ('fecha_hora_inicio', 'fecha_hora_fin_estimada'),
        'visitas.csv': ('fecha_hora_llegada', 'fecha_hora_salida'),
        'visitas_mesas.csv': ('fecha_hora_liberacion',),
    }
    for v_archivo, v_filas in p_fuentes.items():
        v_convertidos[v_archivo] = []
        for v_numero, v_fila in enumerate(v_filas, start=2):
            v_registro = dict(v_fila)
            for v_campo in v_numericos[v_archivo]:
                v_registro[v_campo] = entero(v_fila, v_campo, v_archivo, v_numero,
                                             v_archivo == 'visitas.csv' and v_campo == 'id_reserva')
            for v_campo in v_fechas.get(v_archivo, ()):
                v_registro[v_campo] = fecha_hora(v_fila, v_campo, v_archivo, v_numero)
            for v_campo in v_registro:
                if isinstance(v_registro[v_campo], str):
                    v_registro[v_campo] = v_registro[v_campo].strip()
            v_registro['_fila'] = v_numero
            v_convertidos[v_archivo].append(v_registro)
    return v_convertidos


def comprobar_unicos(p_filas, p_campos, p_archivo):
    v_vistos = set()
    for v_fila in p_filas:
        v_clave = tuple(v_fila[v_campo] for v_campo in p_campos)
        if v_clave in v_vistos:
            error(p_archivo, v_fila['_fila'], ','.join(p_campos), f'Duplicado: {v_clave}')
        v_vistos.add(v_clave)


def validar_datos(p_datos, p_inicio, p_corte):
    v_suc = p_datos['sucursales.csv']
    v_mesas = p_datos['mesas.csv']
    v_res = p_datos['reservas.csv']
    v_vis = p_datos['visitas.csv']
    v_asig = p_datos['visitas_mesas.csv']
    for v_filas, v_campos, v_archivo in (
        (v_suc, ('id_sucursal',), 'sucursales.csv'),
        (v_mesas, ('id_mesa',), 'mesas.csv'),
        (v_mesas, ('id_sucursal', 'numero'), 'mesas.csv'),
        (v_res, ('id_reserva',), 'reservas.csv'),
        (v_res, ('id_sucursal', 'fecha_hora_inicio'), 'reservas.csv'),
        (v_vis, ('id_visita',), 'visitas.csv'),
        (v_asig, ('id_visita', 'id_mesa'), 'visitas_mesas.csv'),
    ):
        comprobar_unicos(v_filas, v_campos, v_archivo)
    v_suc_ids = {v['id_sucursal'] for v in v_suc}
    v_mesa_ids = {v['id_mesa']: v for v in v_mesas}
    v_res_ids = {v['id_reserva']: v for v in v_res}
    v_vis_ids = {v['id_visita']: v for v in v_vis}
    v_corte = datetime.combine(p_corte, datetime.min.time())
    v_conteos_res = Counter()
    v_asig_vis = defaultdict(list)
    v_ocupaciones = defaultdict(list)
    for v_m in v_mesas:
        if v_m['id_sucursal'] not in v_suc_ids:
            error('mesas.csv', v_m['_fila'], 'id_sucursal', 'Sucursal inexistente')
    for v_r in v_res:
        v_inicio = v_r['fecha_hora_inicio']
        v_fin = v_r['fecha_hora_fin_estimada']
        if v_r['id_sucursal'] not in v_suc_ids:
            error('reservas.csv', v_r['_fila'], 'id_sucursal', 'Sucursal inexistente')
        if v_r['estado'] not in ('atendida', 'cancelada', 'no_asistio'):
            error('reservas.csv', v_r['_fila'], 'estado', 'Estado inválido')
        if not 1 <= v_r['cantidad_personas'] <= 8:
            error('reservas.csv', v_r['_fila'], 'cantidad_personas', 'Debe estar entre 1 y 8')
        if not (p_inicio <= v_inicio.date() < p_corte and v_inicio < v_fin <= v_corte):
            error('reservas.csv', v_r['_fila'], 'fecha_hora_inicio', 'Período o secuencia inválidos')
        if v_inicio.time().minute != 0 or not (HORA_PRIMERA_RESERVA <= v_inicio.time() <= HORA_ULTIMA_RESERVA):
            error('reservas.csv', v_r['_fila'], 'fecha_hora_inicio', 'Horario de reserva inválido')
        if (v_fin - v_inicio).total_seconds() / 60 != DURACION_ESTIMADA_RESERVA_MINUTOS:
            error('reservas.csv', v_r['_fila'], 'fecha_hora_fin_estimada', 'Duración estimada incorrecta')
    for v_v in v_vis:
        v_id = v_v['id_visita']
        v_llegada, v_salida = v_v['fecha_hora_llegada'], v_v['fecha_hora_salida']
        if v_v['id_sucursal'] not in v_suc_ids:
            error('visitas.csv', v_v['_fila'], 'id_sucursal', 'Sucursal inexistente')
        if not 1 <= v_v['cantidad_personas'] <= 8:
            error('visitas.csv', v_v['_fila'], 'cantidad_personas', 'Debe estar entre 1 y 8')
        if not (p_inicio <= v_llegada.date() < p_corte and v_llegada < v_salida < v_corte):
            error('visitas.csv', v_v['_fila'], 'fecha_hora_llegada', 'Período o secuencia inválidos')
        if v_llegada.time() < HORA_APERTURA or v_salida.time() > HORA_CIERRE:
            error('visitas.csv', v_v['_fila'], 'fecha_hora_llegada', 'Fuera del horario de atención')
        if not DURACION_VISITA_MINUTOS_MIN <= (v_salida - v_llegada).total_seconds()/60 <= DURACION_VISITA_MINUTOS_MAX:
            error('visitas.csv', v_v['_fila'], 'fecha_hora_salida', 'Duración de visita inválida')
        v_reserva_id = v_v['id_reserva']
        if v_reserva_id is None:
            if v_llegada.time() > HORA_ULTIMA_LLEGADA_SIN_RESERVA:
                error('visitas.csv', v_v['_fila'], 'fecha_hora_llegada', 'Llegada sin reserva demasiado tarde')
        else:
            v_r = v_res_ids.get(v_reserva_id)
            if v_r is None or v_r['estado'] != 'atendida':
                error('visitas.csv', v_v['_fila'], 'id_reserva', 'Reserva inexistente o no atendida')
            if (v_r['id_sucursal'], v_r['cantidad_personas']) != (v_v['id_sucursal'], v_v['cantidad_personas']):
                error('visitas.csv', v_v['_fila'], 'id_reserva', 'Sucursal/personas no coinciden')
            v_desfase = (v_llegada - v_r['fecha_hora_inicio']).total_seconds()/60
            if not DESFASE_LLEGADA_MINUTOS_MIN <= v_desfase <= DESFASE_LLEGADA_MINUTOS_MAX:
                error('visitas.csv', v_v['_fila'], 'fecha_hora_llegada', 'Desfase fuera de rango')
            v_conteos_res[v_reserva_id] += 1
    for v_r in v_res:
        v_esperado = 1 if v_r['estado'] == 'atendida' else 0
        if v_conteos_res[v_r['id_reserva']] != v_esperado:
            error('reservas.csv', v_r['_fila'], 'estado', f'Reserva {v_r["id_reserva"]}: visitas esperadas {v_esperado}, encontradas {v_conteos_res[v_r["id_reserva"]]}')
    for v_a in v_asig:
        v_v = v_vis_ids.get(v_a['id_visita'])
        v_m = v_mesa_ids.get(v_a['id_mesa'])
        if v_v is None or v_m is None:
            error('visitas_mesas.csv', v_a['_fila'], 'id_visita/id_mesa', 'Visita o mesa inexistente')
        if v_v['id_sucursal'] != v_m['id_sucursal']:
            error('visitas_mesas.csv', v_a['_fila'], 'id_mesa', 'Mesa de otra sucursal')
        v_min = (v_a['fecha_hora_liberacion'] - v_v['fecha_hora_salida']).total_seconds()/60
        if not LIBERACION_MINUTOS_MIN <= v_min <= LIBERACION_MINUTOS_MAX:
            error('visitas_mesas.csv', v_a['_fila'], 'fecha_hora_liberacion', 'Minutos de liberación inválidos')
        if v_a['fecha_hora_liberacion'] >= v_corte or v_a['fecha_hora_liberacion'].time() > HORA_CIERRE:
            error('visitas_mesas.csv', v_a['_fila'], 'fecha_hora_liberacion', 'Liberación fuera del período/horario')
        v_asig_vis[v_a['id_visita']].append(v_a)
        v_ocupaciones[v_a['id_mesa']].append((v_v['fecha_hora_llegada'], v_a['fecha_hora_liberacion'], v_v['id_visita']))
    v_capacidades = {}
    for v_v in v_vis:
        v_lista = v_asig_vis[v_v['id_visita']]
        if not v_lista:
            error('visitas.csv', v_v['_fila'], 'id_visita', 'Visita sin mesas')
        v_capacidad = sum(v_mesa_ids[v_a['id_mesa']]['capacidad'] for v_a in v_lista)
        if v_capacidad < v_v['cantidad_personas']:
            error('visitas.csv', v_v['_fila'], 'cantidad_personas', 'Capacidad asignada insuficiente')
        v_capacidades[v_v['id_visita']] = v_capacidad
    for v_id_mesa, v_intervalos in v_ocupaciones.items():
        v_intervalos.sort()
        for v_anterior, v_actual in zip(v_intervalos, v_intervalos[1:]):
            if v_anterior[1] > v_actual[0]:
                error('visitas_mesas.csv', 0, 'id_mesa', f'Mesa {v_id_mesa}: visitas {v_anterior[2]} y {v_actual[2]} superpuestas')
    return v_capacidades


def preparar_tablas(p_datos, p_capacidades, p_inicio, p_corte):
    v_suc, v_mesas = p_datos['sucursales.csv'], p_datos['mesas.csv']
    v_res, v_vis, v_asig = p_datos['reservas.csv'], p_datos['visitas.csv'], p_datos['visitas_mesas.csv']
    v_tablas = {}
    v_tablas['dim_sucursal'] = [{v_c: v[v_c] for v_c in COLUMNAS_TABLAS['dim_sucursal']} for v in v_suc]
    v_tablas['dim_mesa'] = [{v_c: v[v_c] for v_c in COLUMNAS_TABLAS['dim_mesa']} for v in v_mesas]
    v_fechas = []
    v_fecha = p_inicio
    while v_fecha < p_corte:
        v_dia = v_fecha.isoweekday()
        v_fechas.append(dict(id_fecha=int(v_fecha.strftime('%Y%m%d')), fecha=v_fecha,
                             anio=v_fecha.year, mes=v_fecha.month, nombre_mes=MESES[v_fecha.month-1],
                             dia_mes=v_fecha.day, dia_semana=v_dia, nombre_dia=DIAS[v_dia-1]))
        v_fecha += timedelta(days=1)
    v_tablas['dim_fecha'] = v_fechas
    v_tablas['dim_hora'] = [dict(id_hora=v_h, etiqueta=f'{v_h:02d}:00') for v_h in range(24)]
    v_tablas['fact_reserva'] = [dict(id_reserva=v['id_reserva'], id_sucursal=v['id_sucursal'],
        id_fecha=int(v['fecha_hora_inicio'].strftime('%Y%m%d')), id_hora=v['fecha_hora_inicio'].hour,
        fecha_hora_inicio=v['fecha_hora_inicio'], fecha_hora_fin_estimada=v['fecha_hora_fin_estimada'],
        cantidad_personas=v['cantidad_personas'], estado=v['estado']) for v in v_res]
    v_tablas['fact_visita'] = [dict(id_visita=v['id_visita'], id_sucursal=v['id_sucursal'],
        id_fecha=int(v['fecha_hora_llegada'].strftime('%Y%m%d')), id_hora=v['fecha_hora_llegada'].hour,
        id_reserva_origen=v['id_reserva'], fecha_hora_llegada=v['fecha_hora_llegada'],
        fecha_hora_salida=v['fecha_hora_salida'], cantidad_personas=v['cantidad_personas'],
        capacidad_asignada=p_capacidades[v['id_visita']]) for v in v_vis]
    v_vis_ids = {v['id_visita']: v for v in v_vis}
    v_tablas['fact_uso_mesa'] = [dict(id_visita_origen=v['id_visita'], id_mesa=v['id_mesa'],
        id_sucursal=v_vis_ids[v['id_visita']]['id_sucursal'],
        id_fecha=int(v_vis_ids[v['id_visita']]['fecha_hora_llegada'].strftime('%Y%m%d')),
        fecha_hora_llegada=v_vis_ids[v['id_visita']]['fecha_hora_llegada'],
        fecha_hora_salida=v_vis_ids[v['id_visita']]['fecha_hora_salida'],
        fecha_hora_liberacion=v['fecha_hora_liberacion']) for v in v_asig]
    return v_tablas


def comprobar_modelo(p_cursor):
    v_tablas = list(COLUMNAS_TABLAS)
    p_cursor.execute('''SELECT table_name, column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY(%s)''', (v_tablas,))
    v_encontradas = defaultdict(set)
    for v_tabla, v_columna in p_cursor.fetchall():
        v_encontradas[v_tabla].add(v_columna)
    for v_tabla, v_campos in COLUMNAS_TABLAS.items():
        if not set(v_campos).issubset(v_encontradas[v_tabla]):
            raise RuntimeError(f'Modelo SQL faltante o incompatible: {v_tabla}; columnas faltantes: {set(v_campos)-v_encontradas[v_tabla]}')


def cargar_tablas(p_conexion, p_tablas):
    # Nombres de tabla/columnas son constantes internas, no vienen de CSV.
    with p_conexion.cursor() as v_cursor:
        comprobar_modelo(v_cursor)
        for v_tabla in reversed(list(COLUMNAS_TABLAS)):
            v_cursor.execute(f'DELETE FROM {v_tabla}')
        for v_tabla, v_columnas in COLUMNAS_TABLAS.items():
            v_sql = (f'INSERT INTO {v_tabla} (' + ', '.join(v_columnas) + ') VALUES ('
                     + ', '.join(['%s'] * len(v_columnas)) + ')')
            v_filas = [tuple(v_fila[v_campo] for v_campo in v_columnas) for v_fila in p_tablas[v_tabla]]
            # executemany mantiene la carga dentro de la misma transacción.
            if v_filas:
                v_cursor.executemany(v_sql, v_filas)


def escribir_error(p_error):
    v_ruta = Path(__file__).resolve().parent / 'errores_carga.csv'
    with v_ruta.open('w', encoding='utf-8', newline='') as v_archivo:
        v_escritor = csv.writer(v_archivo)
        v_escritor.writerow(('archivo', 'fila', 'campo', 'motivo'))
        if isinstance(p_error, ErrorFuente):
            v_escritor.writerow((p_error.archivo, p_error.fila, p_error.campo, p_error.motivo))
        else:
            v_escritor.writerow(('carga_datamart', '', '', str(p_error)))


def cargar_datamart(p_directorio_fuentes, p_ruta_config):
    """Valida CSV antes de conectar y reemplaza solo el DataMart en una transacción."""
    try:
        v_directorio = Path(p_directorio_fuentes)
        v_fuentes = {v_archivo: leer_fuente(v_directorio / v_archivo, v_campos)
                     for v_archivo, v_campos in CAMPOS.items()}
        v_filas_leidas = {v_archivo: len(v_filas) for v_archivo, v_filas in v_fuentes.items()}
        v_datos = transformar(v_fuentes)
        v_capacidades = validar_datos(v_datos, FECHA_INICIO, FECHA_CORTE_EXCLUSIVA)
        v_tablas = preparar_tablas(v_datos, v_capacidades, FECHA_INICIO, FECHA_CORTE_EXCLUSIVA)
        # No se conecta a PostgreSQL hasta que los cinco CSV sean válidos.
        with obtener_conexion(p_ruta_config) as v_conexion:
            if v_conexion.info.dbname != 'restaurante_olap':
                raise RuntimeError('Conexión rechazada: dbname debe ser restaurante_olap')
            cargar_tablas(v_conexion, v_tablas)
            # El context manager confirma al salir sin error y revierte al fallar.
        v_error = Path(__file__).resolve().parent / 'errores_carga.csv'
        if v_error.exists():
            v_error.unlink()
        return {'filas_leidas': v_filas_leidas,
                'filas_cargadas': {v_tabla: len(v_filas) for v_tabla, v_filas in v_tablas.items()}}
    except Exception as v_error:
        escribir_error(v_error)
        raise


if __name__ == '__main__':
    v_proyecto = Path(__file__).resolve().parent.parent
    print(cargar_datamart(v_proyecto / 'fuentes', v_proyecto / 'config.ini'))
