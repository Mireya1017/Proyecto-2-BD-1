# funcionalidades_py/usuarios.py
import hashlib
import hmac
import secrets
from funcionalidades_py.conexion import obtener_conexion
from funcionalidades_py.sesion import crear_sesion
from funcionalidades_py.transacciones import ejecutar_transaccion

ROLES_PERMITIDOS = ("administrador", "gerente", "mesero")
ITERACIONES_HASH = 260_000


def generar_hash_contrasena(p_contrasena: str) -> str:
    """Genera un hash seguro con sal aleatoria usando PBKDF2-HMAC-SHA256."""
    if not p_contrasena or len(p_contrasena.strip()) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    v_sal = secrets.token_hex(16)
    v_hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        p_contrasena.encode("utf-8"),
        bytes.fromhex(v_sal),
        ITERACIONES_HASH,
    )
    return f"pbkdf2_sha256${ITERACIONES_HASH}${v_sal}${v_hash_bytes.hex()}"


def verificar_contrasena(p_contrasena: str, p_hash_guardado: str) -> bool:
    """Verifica una contraseña en texto plano contra el hash con sal almacenado."""
    try:
        v_algoritmo, v_iter_str, v_sal, v_hash_hex = p_hash_guardado.split("$")
        if v_algoritmo != "pbkdf2_sha256":
            return False
        v_hash_calc = hashlib.pbkdf2_hmac(
            "sha256",
            p_contrasena.encode("utf-8"),
            bytes.fromhex(v_sal),
            int(v_iter_str),
        ).hex()
        return hmac.compare_digest(v_hash_calc, v_hash_hex)
    except Exception:
        return False


def validar_permiso(p_sesion: dict, p_roles_permitidos: tuple | list) -> None:
    """Comprueba que la sesión sea válida y que su rol tenga permiso."""
    if not p_sesion or "id_usuario" not in p_sesion or "rol" not in p_sesion:
        raise PermissionError("No existe una sesión autenticada activa.")
    if p_sesion["rol"] not in p_roles_permitidos:
        raise PermissionError(
            f"El rol '{p_sesion['rol']}' no tiene permiso para ejecutar esta operación."
        )


def validar_acceso_sucursal(p_sesion: dict, p_id_sucursal_objetivo: int | None = None) -> int:
    """
    Valida que el usuario pueda operar sobre la sucursal indicada.
    El administrador puede operar en cualquier sede; gerente y mesero solo en su sucursal habitual.
    """
    if not p_sesion:
        raise PermissionError("No existe una sesión autenticada activa.")
    if p_sesion["rol"] == "administrador":
        if p_id_sucursal_objetivo is None:
            return int(p_sesion["id_sucursal"])
        return int(p_id_sucursal_objetivo)

    v_sucursal_usuario = int(p_sesion["id_sucursal"])
    if p_id_sucursal_objetivo is not None and int(p_id_sucursal_objetivo) != v_sucursal_usuario:
        raise PermissionError(
            f"El rol '{p_sesion['rol']}' solo puede operar en su sucursal asignada (ID {v_sucursal_usuario})."
        )
    return v_sucursal_usuario


def registrar_primer_administrador(
    p_nombre_usuario: str, p_contrasena: str, p_id_sucursal: int
) -> int:
    """
    Registra al primer administrador cuando la tabla usuario está vacía.
    No establece app.id_usuario para que la bitácora registre NULL en id_usuario.
    """
    v_nombre = (p_nombre_usuario or "").strip()
    if not v_nombre:
        raise ValueError("El nombre de usuario es obligatorio.")

    v_hash = generar_hash_contrasena(p_contrasena)
    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute("SELECT COUNT(*) FROM usuario;")
            if v_cur.fetchone()[0] > 0:
                raise PermissionError(
                    "Ya existe al menos un usuario. Utilice una sesión de administrador para crear más usuarios."
                )

            v_cur.execute("SELECT 1 FROM sucursal WHERE id_sucursal = %s;", (p_id_sucursal,))
            if not v_cur.fetchone():
                raise ValueError(f"La sucursal con ID {p_id_sucursal} no existe.")

            v_cur.execute(
                """
                INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
                VALUES (%s, %s, 'administrador', %s)
                RETURNING id_usuario;
                """,
                (v_nombre, v_hash, int(p_id_sucursal)),
            )
            v_id_usuario = v_cur.fetchone()[0]
        v_conexion.commit()
        return v_id_usuario
    except Exception:
        v_conexion.rollback()
        raise
    finally:
        v_conexion.close()


def op_registrar_usuario(p_conexion, p_sesion: dict, p_datos: dict) -> int:
    """
    Operación transaccional para crear usuarios.
    Recibe (p_conexion, p_sesion, p_datos) según el estándar de ejecutar_transaccion.
    """
    validar_permiso(p_sesion, ("administrador",))

    v_nombre = (p_datos.get("nombre_usuario") or "").strip()
    v_contrasena = p_datos.get("contrasena") or ""
    v_rol = (p_datos.get("rol") or "").strip().lower()
    v_id_sucursal = p_datos.get("id_sucursal")

    if not v_nombre:
        raise ValueError("El nombre de usuario es obligatorio.")
    if v_rol not in ROLES_PERMITIDOS:
        raise ValueError(f"Rol inválido. Roles permitidos: {ROLES_PERMITIDOS}.")
    if not v_id_sucursal:
        raise ValueError("Debe indicar la sucursal habitual del usuario.")

    v_hash = generar_hash_contrasena(v_contrasena)

    with p_conexion.cursor() as v_cur:
        v_cur.execute("SELECT 1 FROM sucursal WHERE id_sucursal = %s;", (v_id_sucursal,))
        if not v_cur.fetchone():
            raise ValueError(f"La sucursal {v_id_sucursal} no existe.")

        v_cur.execute("SELECT 1 FROM usuario WHERE nombre_usuario = %s;", (v_nombre,))
        if v_cur.fetchone():
            raise ValueError(f"El nombre de usuario '{v_nombre}' ya está registrado.")

        v_cur.execute(
            """
            INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, id_sucursal)
            VALUES (%s, %s, %s, %s)
            RETURNING id_usuario;
            """,
            (v_nombre, v_hash, v_rol, int(v_id_sucursal)),
        )
        return v_cur.fetchone()[0]


def registrar_usuario(p_sesion: dict, p_datos: dict) -> int:
    """Ejecuta el registro de un nuevo usuario dentro del manejador de transacciones."""
    return ejecutar_transaccion(p_sesion, op_registrar_usuario, p_datos)


def iniciar_sesion(p_nombre_usuario: str, p_contrasena: str) -> dict:
    """Valida credenciales contra la BD y devuelve la estructura oficial crear_sesion."""
    v_nombre = (p_nombre_usuario or "").strip()
    if not v_nombre or not p_contrasena:
        raise ValueError("Debe proporcionar nombre de usuario y contraseña.")

    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                SELECT u.id_usuario, u.nombre_usuario, u.contrasena_hash,
                       u.rol, u.id_sucursal, s.nombre AS nombre_sucursal
                FROM usuario u
                JOIN sucursal s ON s.id_sucursal = u.id_sucursal
                WHERE u.nombre_usuario = %s;
                """,
                (v_nombre,),
            )
            v_fila = v_cur.fetchone()
            if not v_fila:
                raise ValueError("Usuario o contraseña incorrectos.")

            v_id_usu, v_nom_usu, v_hash_bd, v_rol, v_id_suc, v_nom_suc = v_fila
            if not verificar_contrasena(p_contrasena, v_hash_bd):
                raise ValueError("Usuario o contraseña incorrectos.")

            v_sesion = crear_sesion(v_id_usu, v_rol, v_id_suc)
            v_sesion["nombre_usuario"] = v_nom_usu
            v_sesion["nombre_sucursal"] = v_nom_suc
            return v_sesion
    finally:
        v_conexion.close()


def cerrar_sesion(p_sesion: dict) -> None:
    """Limpia el diccionario de sesión."""
    if isinstance(p_sesion, dict):
        p_sesion.clear()


def listar_usuarios(p_sesion: dict) -> list[dict]:
    """Devuelve la lista de usuarios registrados (solo para administradores)."""
    validar_permiso(p_sesion, ("administrador",))
    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                """
                SELECT u.id_usuario, u.nombre_usuario, u.rol,
                       u.id_sucursal, s.nombre AS sucursal
                FROM usuario u
                JOIN sucursal s ON s.id_sucursal = u.id_sucursal
                ORDER BY u.id_usuario ASC;
                """
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()


def listar_sucursales() -> list[dict]:
    """Lista las sucursales registradas."""
    v_conexion = obtener_conexion()
    try:
        with v_conexion.cursor() as v_cur:
            v_cur.execute(
                "SELECT id_sucursal, nombre, direccion FROM sucursal ORDER BY id_sucursal ASC;"
            )
            v_cols = [d[0] for d in v_cur.description]
            return [dict(zip(v_cols, f)) for f in v_cur.fetchall()]
    finally:
        v_conexion.close()