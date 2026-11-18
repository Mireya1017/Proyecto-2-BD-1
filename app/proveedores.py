"""
Módulo de Gestión de Proveedores de Insumos.
"""

from typing import Optional, List, Dict, Any

from app.database import transaccion, ErrorBaseDatos, ErrorNoEncontrado, ErrorPermiso
from app.auth import SesionUsuario, validar_permisos_operacion


def registrar_proveedor(
    nombre: str,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    direccion: Optional[str] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> int:
    """Registra un nuevo proveedor de insumos (administrador o gerente)."""
    validar_permisos_operacion(sesion, roles_permitidos=["administrador", "gerente"])

    if not nombre or not nombre.strip():
        raise ValueError("El nombre del proveedor no puede estar vacío.")

    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'proveedor'
                );
                """
            )
            existe_tabla = cur.fetchone()[0]
            if not existe_tabla:
                raise ErrorBaseDatos(
                    "La tabla 'proveedor' no está instalada en el esquema base. "
                    "Ejecute 'bd/extension_compras_proveedores.sql' para habilitarla."
                )

            cur.execute(
                """
                INSERT INTO proveedor (nombre, telefono, email, direccion)
                VALUES (%s, %s, %s, %s)
                RETURNING id_proveedor;
                """,
                (nombre.strip(), telefono, email, direccion)
            )
            return cur.fetchone()[0]


def consultar_proveedores(
    filtro_nombre: Optional[str] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Consulta el catálogo de proveedores de insumos registrados."""
    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'proveedor'
                );
                """
            )
            if not cur.fetchone()[0]:
                return []

            query = """
                SELECT id_proveedor, nombre, telefono, email, direccion
                FROM proveedor
                WHERE (%s::VARCHAR IS NULL OR nombre ILIKE %s)
                ORDER BY nombre ASC;
            """
            patron = f"%{filtro_nombre.strip()}%" if filtro_nombre else None
            cur.execute(query, (patron, patron))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
