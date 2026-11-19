# ============================================================
# PROYECTO 3 - GENERADOR DE RESERVAS
# Responsable: Nathalie
#
# Proposito:
# Generar reservas simuladas y reproducibles para
# Oakland Mall y Ciudad Cayala.
#
# Entradas:
# proyecto3/fuentes/sucursales.csv
# proyecto3/fuentes/mesas.csv
# Parametros compartidos de parametros.py
#
# Salida:
# proyecto3/fuentes/reservas.csv
#
# Ejecucion:
# python proyecto3/python/generar_reservas.py
# ============================================================

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from parametros import (
    FECHA_INICIO,
    FECHA_CORTE_EXCLUSIVA,
    HORA_PRIMERA_RESERVA,
    HORA_ULTIMA_RESERVA,
    DURACION_ESTIMADA_RESERVA_MINUTOS,
    TOTAL_RESERVAS, PESOS_MES, PESOS_DIA_SEMANA, PESOS_HORA,
    FACTOR_VOLUMEN_MIN, FACTOR_VOLUMEN_MAX,
    PROBABILIDAD_ATENCION_MIN, PROBABILIDAD_ATENCION_MAX,
    PROPORCION_CANCELADAS_MIN, PROPORCION_CANCELADAS_MAX,
    distribuir_total,
    PERSONAS_POR_GRUPO,
    PROBABILIDADES_PERSONAS,
    SEMILLA_RESERVAS
)


# Directorio del proyecto, sin rutas personales
DIRECTORIO_PROYECTO = Path(__file__).resolve().parent.parent
DIRECTORIO_FUENTES = DIRECTORIO_PROYECTO / "fuentes"


def leer_catalogo(p_ruta, p_columnas):
    """
    Lee un catalogo CSV y valida sus encabezados.

    Parametros:
        p_ruta: ruta del archivo CSV.
        p_columnas: encabezados esperados.

    Devuelve:
        Lista de diccionarios con los registros.
    """

    if not p_ruta.is_file():
        raise FileNotFoundError(
            f"No existe el archivo: {p_ruta}"
        )

    with p_ruta.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as v_archivo:

        v_lector = csv.DictReader(v_archivo)

        if v_lector.fieldnames != p_columnas:
            raise ValueError(
                f"Encabezados incorrectos en {p_ruta.name}. "
                f"Esperados: {p_columnas}"
            )

        v_registros = list(v_lector)

    if not v_registros:
        raise ValueError(
            f"El catalogo {p_ruta.name} esta vacio."
        )

    return v_registros


def cargar_catalogos(p_directorio_fuentes):
    """
    Carga los catalogos de sucursales y mesas.
    """

    v_directorio = Path(p_directorio_fuentes)

    v_sucursales = leer_catalogo(
        v_directorio / "sucursales.csv",
        ["id_sucursal", "nombre", "direccion"]
    )

    v_mesas = leer_catalogo(
        v_directorio / "mesas.csv",
        [
            "id_mesa",
            "id_sucursal",
            "numero",
            "capacidad",
            "zona"
        ]
    )

    # Validar identificadores de sucursal
    v_ids_sucursales = set()

    for v_sucursal in v_sucursales:
        v_id = int(v_sucursal["id_sucursal"])

        if v_id <= 0 or v_id in v_ids_sucursales:
            raise ValueError(
                "ID de sucursal invalido o duplicado."
            )

        v_ids_sucursales.add(v_id)

    # Validar identificadores y referencias de mesas
    v_ids_mesas = set()

    for v_mesa in v_mesas:
        v_id_mesa = int(v_mesa["id_mesa"])
        v_id_sucursal = int(v_mesa["id_sucursal"])
        v_capacidad = int(v_mesa["capacidad"])

        if v_id_mesa <= 0 or v_id_mesa in v_ids_mesas:
            raise ValueError(
                "ID de mesa invalido o duplicado."
            )

        if v_id_sucursal not in v_ids_sucursales:
            raise ValueError(
                "Una mesa pertenece a una sucursal inexistente."
            )

        if v_capacidad <= 0:
            raise ValueError(
                "La capacidad de una mesa debe ser positiva."
            )

        v_ids_mesas.add(v_id_mesa)

    return v_sucursales, v_mesas


def generar_horarios_disponibles(
    p_fecha_inicio,
    p_fecha_corte_exclusiva
):
    """
    Genera horarios posibles para reservas.

    Cada fecha tiene horarios completos desde
    las 11:00 hasta las 20:00.

    No genera horarios repetidos.
    """

    if p_fecha_inicio >= p_fecha_corte_exclusiva:
        raise ValueError(
            "El periodo de generacion no es valido."
        )

    v_horarios = []
    v_fecha = p_fecha_inicio

    while v_fecha < p_fecha_corte_exclusiva:

        for v_hora in range(
            HORA_PRIMERA_RESERVA.hour,
            HORA_ULTIMA_RESERVA.hour + 1
        ):

            v_inicio = datetime.combine(
                v_fecha,
                HORA_PRIMERA_RESERVA
            ).replace(hour=v_hora)

            v_fin = v_inicio + timedelta(
                minutes=DURACION_ESTIMADA_RESERVA_MINUTOS
            )

            v_horarios.append(
                (v_inicio, v_fin)
            )

        v_fecha += timedelta(days=1)

    return v_horarios


def generar_reservas_mes(
    p_id_sucursal,
    p_anio,
    p_mes,
    p_horarios,
    p_generador,
    p_cantidad
):
    """Genera una cantidad variable de reservas, sin cuotas de estados.

    Los pesos de mes, dia y hora son supuestos del escenario simulado.
    Las mismas reglas se aplican a ambas sucursales.
    """
    v_horarios_mes = [
        (v_inicio, v_fin)
        for v_inicio, v_fin in p_horarios
        if v_inicio.year == p_anio and v_inicio.month == p_mes
    ]
    if p_cantidad > len(v_horarios_mes):
        raise ValueError(
            f"No hay suficientes horarios para sucursal {p_id_sucursal}, "
            f"mes {p_mes}: se solicitaron {p_cantidad}."
        )

    v_prob_atencion = p_generador.uniform(
        PROBABILIDAD_ATENCION_MIN, PROBABILIDAD_ATENCION_MAX
    )
    v_prob_cancelacion = (1 - v_prob_atencion) * p_generador.uniform(
        PROPORCION_CANCELADAS_MIN, PROPORCION_CANCELADAS_MAX
    )
    v_prob_inasistencia = 1 - v_prob_atencion - v_prob_cancelacion

    # Seleccion ponderada SIN reemplazo: no repite sucursal/fecha/hora.
    v_pesos = [
        PESOS_DIA_SEMANA[v_inicio.weekday()] * PESOS_HORA[v_inicio.hour]
        for v_inicio, _ in v_horarios_mes
    ]
    v_reservas = []
    for _ in range(p_cantidad):
        v_indice = p_generador.choices(
            range(len(v_horarios_mes)), weights=v_pesos, k=1
        )[0]
        v_inicio, v_fin = v_horarios_mes.pop(v_indice)
        v_pesos.pop(v_indice)
        v_estado = p_generador.choices(
            ['atendida', 'cancelada', 'no_asistio'],
            weights=[v_prob_atencion, v_prob_cancelacion, v_prob_inasistencia],
            k=1
        )[0]
        v_personas = p_generador.choices(
            PERSONAS_POR_GRUPO, weights=PROBABILIDADES_PERSONAS, k=1
        )[0]
        v_reservas.append({
            'id_sucursal': p_id_sucursal,
            'fecha_hora_inicio': v_inicio,
            'fecha_hora_fin_estimada': v_fin,
            'cantidad_personas': v_personas,
            'estado': v_estado
        })
    return v_reservas


def generar_reservas(
    p_directorio_fuentes,
    p_fecha_inicio,
    p_fecha_corte_exclusiva,
    p_semilla
):
    """
    Genera reservas reproducibles para todas las
    sucursales y meses del periodo.

    Entradas:
        Directorio CSV, fechas y semilla.

    Salida:
        reservas.csv con IDs consecutivos.

    Devuelve:
        Cantidad de reservas generadas.
    """

    v_directorio = Path(p_directorio_fuentes)

    v_sucursales, v_mesas = cargar_catalogos(
        v_directorio
    )

    v_ids_sucursales = sorted(
        int(v_sucursal["id_sucursal"])
        for v_sucursal in v_sucursales
    )

    v_capacidades = {
        v_id: sum(
            int(v_mesa["capacidad"])
            for v_mesa in v_mesas
            if int(v_mesa["id_sucursal"]) == v_id
        )
        for v_id in v_ids_sucursales
    }

    if any(v_capacidad < max(PERSONAS_POR_GRUPO)
           for v_capacidad in v_capacidades.values()):
        raise ValueError(
            "Una sucursal no tiene capacidad suficiente."
        )

    v_horarios = generar_horarios_disponibles(
        p_fecha_inicio,
        p_fecha_corte_exclusiva
    )

    v_generador = random.Random(p_semilla)
    v_reservas = []

    v_periodos = sorted({
        (v_inicio.year, v_inicio.month)
        for v_inicio, _ in v_horarios
    })

    # Solo el total del periodo es fijo; cada sucursal/mes varia.
    v_claves = [
        (v_id, v_anio, v_mes)
        for v_id in v_ids_sucursales
        for v_anio, v_mes in v_periodos
    ]
    v_pesos = [
        PESOS_MES.get(v_mes, 1.0)
        * v_generador.uniform(FACTOR_VOLUMEN_MIN, FACTOR_VOLUMEN_MAX)
        for _, _, v_mes in v_claves
    ]
    v_cantidades = distribuir_total(TOTAL_RESERVAS, v_claves, v_pesos)

    for v_id_sucursal in v_ids_sucursales:
        for v_anio, v_mes in v_periodos:

            v_reservas_mes = generar_reservas_mes(
                v_id_sucursal,
                v_anio,
                v_mes,
                v_horarios,
                v_generador,
                v_cantidades[(v_id_sucursal, v_anio, v_mes)]
            )

            v_reservas.extend(v_reservas_mes)

    # Orden cronologico por sucursal y fecha.
    v_reservas.sort(
        key=lambda v_fila: (
            v_fila["id_sucursal"],
            v_fila["fecha_hora_inicio"]
        )
    )

    v_columnas = [
        "id_reserva",
        "id_sucursal",
        "fecha_hora_inicio",
        "fecha_hora_fin_estimada",
        "cantidad_personas",
        "estado"
    ]

    v_ruta_salida = v_directorio / "reservas.csv"

    with v_ruta_salida.open(
        mode="w",
        encoding="utf-8",
        newline=""
    ) as v_archivo:

        v_escritor = csv.DictWriter(
            v_archivo,
            fieldnames=v_columnas
        )

        v_escritor.writeheader()

        for v_id, v_reserva in enumerate(
            v_reservas,
            start=1
        ):
            v_escritor.writerow({
                "id_reserva": v_id,
                "id_sucursal": v_reserva["id_sucursal"],
                "fecha_hora_inicio": (
                    v_reserva["fecha_hora_inicio"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                ),
                "fecha_hora_fin_estimada": (
                    v_reserva["fecha_hora_fin_estimada"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                ),
                "cantidad_personas": v_reserva["cantidad_personas"],
                "estado": v_reserva["estado"]
            })

    return len(v_reservas)




if __name__ == "__main__":

    v_total = generar_reservas(
        DIRECTORIO_FUENTES,
        FECHA_INICIO,
        FECHA_CORTE_EXCLUSIVA,
        SEMILLA_RESERVAS
    )

    print("Reservas generadas correctamente.")
    print("Total:", v_total)
    print("Archivo:", DIRECTORIO_FUENTES / "reservas.csv")
