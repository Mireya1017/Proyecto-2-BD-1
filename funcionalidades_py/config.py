"""
Módulo de Configuración Externa.
Lee los parámetros de conexión y ejecución desde variables de entorno o archivo .env,
manteniendo las credenciales estrictamente fuera del código fuente.
"""

import os
from pathlib import Path
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuración inmutable de la base de datos PostgreSQL."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    dbname: str = os.getenv("DB_NAME", "restaurante_prueba")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    min_conn: int = int(os.getenv("DB_MIN_CONN", "1"))
    max_conn: int = int(os.getenv("DB_MAX_CONN", "10"))
    app_env: str = os.getenv("APP_ENV", "desarrollo")

    def to_dict(self) -> dict:
        """Devuelve un diccionario con los parámetros de conexión de psycopg2."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
        }

    def get_dsn_safe(self) -> str:
        """Devuelve una cadena de conexión sanitizada para logs (sin contraseña)."""
        return f"postgresql://{self.user}:***@{self.host}:{self.port}/{self.dbname}"


DB_CONFIG = DatabaseConfig()
