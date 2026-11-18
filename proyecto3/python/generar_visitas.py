
"""
Generador de visitas y asignaciones de mesas - Proyecto 3.

Propósito:
    Generar visitas con y sin reserva a partir de
    los catálogos y las reservas del restaurante.

Entradas:
    fuentes/sucursales.csv
    fuentes/mesas.csv
    fuentes/reservas.csv

Salidas:
    fuentes/visitas.csv
    fuentes/visitas_mesas.csv

Ejecución prevista:
    python proyecto3/python/generar_visitas.py
"""

import csv
import random

from datetime import datetime, timedelta
from pathlib import Path

def leer_csv(p_ruta):
    v_ruta = Path(p_ruta)

    if not v_ruta.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo: {v_ruta}"
        )

    with v_ruta.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as v_archivo:

        v_lector = csv.DictReader(v_archivo)

        if v_lector.fieldnames is None:
            raise ValueError(
                f"El archivo no tiene encabezados: {v_ruta}"
            )

        v_registros = list(v_lector)

    return v_registros


def generar_visitas(
    p_directorio_fuentes,
    p_fecha_inicio,
    p_fecha_corte_exclusiva,
    p_semilla
):
    v_directorio = Path(p_directorio_fuentes)

    v_sucursales = leer_csv(
        v_directorio / "sucursales.csv"
    )

    v_mesas = leer_csv(
        v_directorio / "mesas.csv"
    )

    v_reservas = leer_csv(
        v_directorio / "reservas.csv"
    )

    v_aleatorio = random.Random(p_semilla)

    # En los siguientes pasos:
    # 1. Validaremos los datos de entrada.
    # 2. Generaremos visitas con reserva.
    # 3. Generaremos visitas sin reserva.
    # 4. Asignaremos mesas disponibles.
    # 5. Guardaremos los dos archivos CSV.

    raise NotImplementedError(
        "El generador todavía está en desarrollo."
    )
