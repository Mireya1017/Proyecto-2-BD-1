
"""
Conexión a la base de datos del Proyecto 3.

Propósito:
    Obtener una conexión a PostgreSQL utilizando un
    archivo de configuración externo.

Entrada:
    p_ruta_config: ruta del archivo config.ini.

Salida:
    Conexión a la base restaurante_olap.

Ejecución:
    Este módulo se importa desde otros programas.
"""

import configparser
from pathlib import Path

import psycopg


def obtener_conexion(p_ruta_config):
    v_ruta = Path(p_ruta_config)

    if not v_ruta.is_file():
        raise FileNotFoundError(
            f"No existe el archivo de configuración: {v_ruta}"
        )

    v_config = configparser.ConfigParser()
    v_config.read(v_ruta, encoding="utf-8")

    if "postgresql" not in v_config:
        raise ValueError(
            "Falta la sección [postgresql] en config.ini."
        )

    v_datos = v_config["postgresql"]

    v_conexion = psycopg.connect(
        host=v_datos["host"],
        port=v_datos.getint("port"),
        dbname=v_datos["dbname"],
        user=v_datos["user"],
        password=v_datos["password"]
    )

    return v_conexion
