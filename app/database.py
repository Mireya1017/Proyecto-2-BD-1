"""
Módulo de Conexión Compartida y Gestión Transaccional.
Provee conexiones reutilizables a PostgreSQL para todos los módulos del sistema (Pablo, Nathalie, Yu-fong)
y garantiza el control transaccional unificado y la auditoría mediante app.id_usuario.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any

from app.config import DB_CONFIG, DatabaseConfig

logger = logging.getLogger("app.database")

try:
    import psycopg2
    from psycopg2 import pool, extras
    POSTGRES_DRIVER = "psycopg2"
except ImportError:
    try:
        import psycopg
        from psycopg_pool import ConnectionPool
        POSTGRES_DRIVER = "psycopg"
    except ImportError:
        POSTGRES_DRIVER = None


class ErrorBaseDatos(Exception):
    """Excepción base para errores de base de datos."""
    pass

class ErrorConexion(ErrorBaseDatos):
    """Fallo al establecer o recuperar conexión con la base de datos."""
    pass

class ErrorTransaccion(ErrorBaseDatos):
    """Fallo durante la ejecución de una transacción."""
    pass

class ErrorRestriccion(ErrorBaseDatos):
    """Violación de una restricción de integridad o trigger en la BD."""
    pass

class ErrorPermiso(Exception):
    """Operación rechazada por falta de permisos del rol del usuario."""
    pass

class ErrorAutenticacion(Exception):
    """Credenciales inválidas o usuario no autenticado."""
    pass

class ErrorDisponibilidad(ErrorBaseDatos):
    """Mesas no disponibles en el horario o sucursal solicitados."""
    pass

class ErrorCapacidad(ErrorBaseDatos):
    """Capacidad insuficiente de mesas asignadas para la cantidad de personas."""
    pass

class ErrorNoEncontrado(Exception):
    """El recurso o registro solicitado no existe en el sistema."""
    pass


_CONNECTION_POOL: Any = None


def inicializar_pool(config: Optional[DatabaseConfig] = None) -> None:
    """Inicializa el pool de conexiones compartido a PostgreSQL."""
    global _CONNECTION_POOL
    if _CONNECTION_POOL is not None:
        return

    cfg = config or DB_CONFIG
    if POSTGRES_DRIVER is None:
        logger.warning("No se encontró controlador PostgreSQL (psycopg2 o psycopg). Modo sin conexión activa.")
        return

    try:
        if POSTGRES_DRIVER == "psycopg2":
            _CONNECTION_POOL = psycopg2.pool.ThreadedConnectionPool(
                minconn=cfg.min_conn,
                maxconn=cfg.max_conn,
                **cfg.to_dict()
            )
            logger.info("Pool de conexiones PostgreSQL (psycopg2) inicializado exitosamente.")
        elif POSTGRES_DRIVER == "psycopg":
            _CONNECTION_POOL = ConnectionPool(
                conninfo=f"host={cfg.host} port={cfg.port} dbname={cfg.dbname} user={cfg.user} password={cfg.password}",
                min_size=cfg.min_conn,
                max_size=cfg.max_conn,
                open=True
            )
            logger.info("Pool de conexiones PostgreSQL (psycopg) inicializado exitosamente.")
    except Exception as e:
        logger.error(f"Error al inicializar pool de conexiones: {e}")
        raise ErrorConexion(f"No fue posible conectar con la base de datos PostgreSQL: {e}") from e


def cerrar_pool() -> None:
    """Cierra todas las conexiones del pool al detener la aplicación."""
    global _CONNECTION_POOL
    if _CONNECTION_POOL is not None:
        try:
            if hasattr(_CONNECTION_POOL, "closeall"):
                _CONNECTION_POOL.closeall()
            elif hasattr(_CONNECTION_POOL, "close"):
                _CONNECTION_POOL.close()
            logger.info("Pool de conexiones PostgreSQL cerrado correctamente.")
        except Exception as e:
            logger.warning(f"Error al cerrar pool de conexiones: {e}")
        finally:
            _CONNECTION_POOL = None


def obtener_conexion() -> Any:
    """Obtiene una conexión reutilizable desde el pool."""
    global _CONNECTION_POOL
    if _CONNECTION_POOL is None:
        inicializar_pool()

    if _CONNECTION_POOL is None:
        raise ErrorConexion("El controlador o pool de conexiones no está disponible.")

    try:
        if POSTGRES_DRIVER == "psycopg2":
            return _CONNECTION_POOL.getconn()
        elif POSTGRES_DRIVER == "psycopg":
            return _CONNECTION_POOL.getconn()
    except Exception as e:
        raise ErrorConexion(f"Error al obtener conexión del pool: {e}") from e


def liberar_conexion(conn: Any) -> None:
    """Devuelve la conexión activa al pool para que pueda ser reutilizada."""
    global _CONNECTION_POOL
    if _CONNECTION_POOL is not None and conn is not None:
        try:
            if POSTGRES_DRIVER == "psycopg2":
                _CONNECTION_POOL.putconn(conn)
            elif POSTGRES_DRIVER == "psycopg":
                _CONNECTION_POOL.putconn(conn)
        except Exception as e:
            logger.warning(f"Error al devolver conexión al pool: {e}")


def establecer_contexto_usuario(conn: Any, id_usuario: Optional[int]) -> None:
    """
    Comunica el identificador del usuario autenticado a la transacción actual mediante app.id_usuario.
    is_local=true garantiza que el contexto sea exclusivo de la transacción actual.
    """
    if id_usuario is not None:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.id_usuario', %s, true);", (str(id_usuario),))
    else:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.id_usuario', '', true);")


@contextmanager
def transaccion(conn: Optional[Any] = None, id_usuario: Optional[int] = None) -> Generator[Any, None, None]:
    """
    Gestor de contexto transaccional compartido para todos los módulos.
    """
    es_propietario = False
    conexion_activa = conn

    if conexion_activa is None:
        conexion_activa = obtener_conexion()
        es_propietario = True
        if hasattr(conexion_activa, "autocommit"):
            conexion_activa.autocommit = False

    try:
        if id_usuario is not None:
            establecer_contexto_usuario(conexion_activa, id_usuario)

        yield conexion_activa

        if es_propietario:
            conexion_activa.commit()

    except Exception as e:
        if es_propietario:
            try:
                conexion_activa.rollback()
            except Exception as rollback_err:
                logger.error(f"Error al ejecutar ROLLBACK: {rollback_err}")

        error_msg = str(e)
        if "Las mesas de una reserva o visita deben ser de la misma zona" in error_msg:
            raise ErrorRestriccion("Error de asignación: Las mesas deben ser de la misma zona.") from e
        elif "La mesa debe pertenecer a la misma sucursal" in error_msg:
            raise ErrorRestriccion("Error de asignación: Las mesas deben pertenecer a la misma sucursal.") from e
        elif "ya tiene una reserva en ese horario" in error_msg:
            raise ErrorDisponibilidad(f"Conflicto de horario: {error_msg}") from e
        elif "las mesas admiten" in error_msg and "se necesitan" in error_msg:
            raise ErrorCapacidad(f"Capacidad insuficiente: {error_msg}") from e
        elif "violates unique constraint" in error_msg or "llave duplicada" in error_msg.lower():
            raise ErrorRestriccion(f"Registro duplicado o conflicto de unicidad: {error_msg}") from e
        raise

    finally:
        if es_propietario and conexion_activa is not None:
            liberar_conexion(conexion_activa)
