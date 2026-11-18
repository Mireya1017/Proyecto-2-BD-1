"""
Módulo de Seguridad, Autenticación y Control de Acceso (RBAC).
Gestiona el hash y sal de contraseñas, la representación de la sesión activa
y la validación estricta de permisos dentro de las operaciones de negocio.
"""

import os
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional, List, Union

from app.database import ErrorPermiso, ErrorAutenticacion

ITERACIONES_HASH = 100000
ALGORITMO_HASH = "sha256"
ROLES_VALIDOS = ("administrador", "gerente", "mesero")


def generar_hash_contrasena(contrasena: str, sal: Optional[bytes] = None) -> str:
    """
    Genera un hash criptográfico protegido con sal utilizando PBKDF2-HMAC-SHA256.
    Retorna el formato: pbkdf2_sha256$iteraciones$sal_hex$hash_hex
    """
    if not contrasena or not isinstance(contrasena, str):
        raise ValueError("La contraseña debe ser una cadena no vacía.")

    if sal is None:
        sal = secrets.token_bytes(16)

    derivada = hashlib.pbkdf2_hmac(
        ALGORITMO_HASH,
        contrasena.encode("utf-8"),
        sal,
        ITERACIONES_HASH
    )
    return f"pbkdf2_{ALGORITMO_HASH}${ITERACIONES_HASH}${sal.hex()}${derivada.hex()}"


def verificar_contrasena(contrasena: str, hash_almacenado: str) -> bool:
    """
    Verifica si una contraseña en texto claro coincide con el hash con sal almacenado.
    """
    if not contrasena or not hash_almacenado:
        return False

    try:
        partes = hash_almacenado.split("$")
        if len(partes) != 4 or not partes[0].startswith("pbkdf2_"):
            return False

        _, iteraciones_str, sal_hex, hash_hex = partes
        iteraciones = int(iteraciones_str)
        sal = bytes.fromhex(sal_hex)

        hash_calculado = hashlib.pbkdf2_hmac(
            ALGORITMO_HASH,
            contrasena.encode("utf-8"),
            sal,
            iteraciones
        ).hex()

        return hmac.compare_digest(hash_calculado, hash_hex)
    except Exception:
        return False


@dataclass(frozen=True)
class SesionUsuario:
    """
    Representación del usuario autenticado en la sesión.
    Contiene la identidad, rol y sucursal habitual para control de acceso y auditoría.
    """
    id_usuario: int
    nombre_usuario: str
    rol: str
    id_sucursal: int

    def __post_init__(self):
        if self.rol not in ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: '{self.rol}'. Debe ser uno de {ROLES_VALIDOS}")

    @property
    def es_administrador(self) -> bool:
        return self.rol == "administrador"

    @property
    def es_gerente(self) -> bool:
        return self.rol == "gerente"

    @property
    def es_mesero(self) -> bool:
        return self.rol == "mesero"

    def puede_operar_en_sucursal(self, id_sucursal_destino: int) -> bool:
        if self.es_administrador:
            return True
        return self.id_sucursal == id_sucursal_destino


def validar_permisos_operacion(
    sesion: Optional[SesionUsuario],
    roles_permitidos: Union[str, List[str]],
    id_sucursal_operacion: Optional[int] = None
) -> None:
    """
    Valida de forma estricta los permisos de sesión antes de ejecutar una operación de negocio.
    """
    if sesion is None:
        raise ErrorAutenticacion("Operación rechazada: Requiere iniciar sesión previamente.")

    if isinstance(roles_permitidos, str):
        roles_permitidos = [roles_permitidos]

    if sesion.rol not in roles_permitidos:
        raise ErrorPermiso(
            f"Acceso denegado: El rol '{sesion.rol}' no tiene permisos para esta acción. "
            f"Roles autorizados: {', '.join(roles_permitidos)}."
        )

    if id_sucursal_operacion is not None and not sesion.puede_operar_en_sucursal(id_sucursal_operacion):
        raise ErrorPermiso(
            f"Acceso denegado: El usuario '{sesion.nombre_usuario}' está asignado a la sucursal {sesion.id_sucursal} "
            f"y no puede operar en la sucursal {id_sucursal_operacion}."
        )
