"""
Módulo de Gestión de Usuarios y Autenticación.
"""

from typing import Optional, List, Dict, Any

from app.database import transaccion, ErrorAutenticacion, ErrorPermiso, ErrorRestriccion, ErrorNoEncontrado
from app.auth import (
    SesionUsuario,
    generar_hash_contrasena,
    verificar_contrasena,
    validar_permisos_operacion,
    ROLES_VALIDOS
)


def contar_usuarios(conn: Optional[Any] = None) -> int:
    """Retorna la cantidad total de usuarios registrados en el sistema."""
    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM usuario;")
            row = cur.fetchone()
            return row[0] if row else 0


def registrar_primer_administrador(
    nombre_usuario: str,
    contrasena: str,
    id_sucursal: int,
    conn: Optional[Any] = None
) -> int:
    """
    Procedimiento de configuración inicial para registrar al primer administrador del sistema.
    Solo se permite si la tabla 'usuario' se encuentra vacía.
    """
    total = contar_usuarios(conn)
    if total > 0:
        raise ErrorPermiso("Ya existen usuarios en el sistema. El primer administrador solo puede crearse en una base vacía.")

    if not nombre_usuario or not contrasena:
        raise ValueError("El nombre de usuario y la contraseña no pueden estar vacíos.")

    hash_pw = generar_hash_contrasena(contrasena)

    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute("SELECT id_sucursal FROM sucursal WHERE id_sucursal = %s;", (id_sucursal,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"La sucursal con ID {id_sucursal} no existe.")

            cur.execute(
                """
                INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
                VALUES (%s, %s, 'administrador', %s)
                RETURNING id_usuario;
                """,
                (nombre_usuario.strip(), hash_pw, id_sucursal)
            )
            return cur.fetchone()[0]


def registrar_usuario(
    nombre_usuario: str,
    contrasena: str,
    rol: str,
    id_sucursal: int,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> int:
    """Registra un nuevo usuario en el sistema (solo administrador)."""
    validar_permisos_operacion(sesion, roles_permitidos="administrador")

    rol_limpio = rol.strip().lower()
    if rol_limpio not in ROLES_VALIDOS:
        raise ValueError(f"Rol no válido: '{rol}'. Roles permitidos: {ROLES_VALIDOS}")

    nombre_limpio = nombre_usuario.strip()
    if len(nombre_limpio) < 3:
        raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
    if len(contrasena) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")

    hash_pw = generar_hash_contrasena(contrasena)
    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute("SELECT id_sucursal FROM sucursal WHERE id_sucursal = %s;", (id_sucursal,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"La sucursal con ID {id_sucursal} no existe.")

            cur.execute("SELECT id_usuario FROM usuario WHERE LOWER(nombre_usuario) = LOWER(%s);", (nombre_limpio,))
            if cur.fetchone():
                raise ErrorRestriccion(f"El nombre de usuario '{nombre_limpio}' ya está registrado.")

            cur.execute(
                """
                INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
                VALUES (%s, %s, %s, %s)
                RETURNING id_usuario;
                """,
                (nombre_limpio, hash_pw, rol_limpio, id_sucursal)
            )
            return cur.fetchone()[0]


def iniciar_sesion(
    nombre_usuario: str,
    contrasena: str,
    conn: Optional[Any] = None
) -> SesionUsuario:
    """Autentica a un usuario y retorna su SesionUsuario."""
    if not nombre_usuario or not contrasena:
        raise ErrorAutenticacion("Debe ingresar nombre de usuario y contraseña.")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT id_usuario, nombre_usuario, contrasena_hash, rol, id_sucursal
                FROM usuario
                WHERE LOWER(nombre_usuario) = LOWER(%s);
                """,
                (nombre_usuario.strip(),)
            )
            fila = cur.fetchone()

            if not fila:
                raise ErrorAutenticacion("Usuario o contraseña incorrectos.")

            id_usuario, nombre, hash_almacenado, rol, id_sucursal = fila

            if not verificar_contrasena(contrasena, hash_almacenado):
                raise ErrorAutenticacion("Usuario o contraseña incorrectos.")

            return SesionUsuario(
                id_usuario=id_usuario,
                nombre_usuario=nombre,
                rol=rol,
                id_sucursal=id_sucursal
            )


def cerrar_sesion(sesion: Optional[SesionUsuario]) -> None:
    """Finaliza la sesión del usuario."""
    pass


def listar_usuarios(
    sesion: Optional[SesionUsuario],
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Lista todos los usuarios (solo administrador)."""
    validar_permisos_operacion(sesion, roles_permitidos="administrador")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.id_usuario,
                    u.nombre_usuario,
                    u.rol,
                    u.id_sucursal,
                    s.nombre AS nombre_sucursal
                FROM usuario u
                JOIN sucursal s ON s.id_sucursal = u.id_sucursal
                ORDER BY u.id_usuario ASC;
                """
            )
            columnas = [desc[0] for desc in cur.description]
            resultados = []
            for row in cur.fetchall():
                resultados.append(dict(zip(columnas, row)))
            return resultados
