from configparser import ConfigParser
from pathlib import Path

import psycopg


def obtener_conexion():
    v_ruta = Path(__file__).resolve().parent.parent / "config.ini"

    v_config = ConfigParser(interpolation=None)

    if not v_config.read(v_ruta, encoding="utf-8"):
        raise FileNotFoundError(
            "No se encontró config.ini en la raíz del proyecto."
        )

    v_datos = v_config["postgresql"]

    v_conexion = psycopg.connect(
        host=v_datos["host"],
        port=v_datos["port"],
        dbname=v_datos["dbname"],
        user=v_datos["user"],
        password=v_datos["password"]
    )

    return v_conexion