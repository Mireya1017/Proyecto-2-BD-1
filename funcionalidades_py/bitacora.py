"""
Módulo de Consulta de Bitácora de Auditoría.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.database import transaccion, ErrorPermiso
from app.auth import SesionUsuario, validar_permisos_operacion


def consultar_bitacora(
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    id_usuario: Optional[int] = None,
    tabla: Optional[str] = None,
    operacion: Optional[str] = None,
    limite: int = 100,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Consulta bitácora para administradores con filtros de fecha, usuario, tabla y operación."""
    validar_permisos_operacion(sesion, roles_permitidos="administrador")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            query = """
                SELECT 
                    b.id_bitacora,
                    b.fecha_hora,
                    b.id_usuario,
                    COALESCE(u.nombre_usuario, 'Sistema / Script') AS nombre_usuario,
                    b.tabla,
                    b.operacion,
                    b.registro
                FROM bitacora b
                LEFT JOIN usuario u ON u.id_usuario = b.id_usuario
                WHERE (%s::TIMESTAMP IS NULL OR b.fecha_hora >= %s)
                  AND (%s::TIMESTAMP IS NULL OR b.fecha_hora <= %s)
                  AND (%s::INTEGER IS NULL OR b.id_usuario = %s)
                  AND (%s::VARCHAR IS NULL OR LOWER(b.tabla) = LOWER(%s))
                  AND (%s::VARCHAR IS NULL OR UPPER(b.operacion) = UPPER(%s))
                ORDER BY b.fecha_hora DESC, b.id_bitacora DESC
                LIMIT %s;
            """
            cur.execute(
                query,
                (
                    fecha_desde, fecha_desde,
                    fecha_hasta, fecha_hasta,
                    id_usuario, id_usuario,
                    tabla, tabla,
                    operacion, operacion,
                    limite
                )
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def listar_tablas_auditadas(
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> List[str]:
    """Retorna las tablas registradas en la bitácora."""
    validar_permisos_operacion(sesion, roles_permitidos="administrador")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT DISTINCT tabla FROM bitacora ORDER BY tabla ASC;")
            return [row[0] for row in cur.fetchall()]
