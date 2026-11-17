"""
Módulo de Gestión de Compras y Coordinación con Inventario.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Callable

from app.database import (
    transaccion,
    ErrorBaseDatos,
    ErrorTransaccion,
    ErrorNoEncontrado,
    ErrorRestriccion,
    ErrorPermiso
)
from app.auth import SesionUsuario, validar_permisos_operacion


def registrar_compra(
    id_proveedor: int,
    id_sucursal: int,
    detalles_insumos: List[Dict[str, Any]],
    funcion_ingreso_lotes: Optional[Callable[[Any, int, List[Dict[str, Any]]], Any]] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> int:
    """
    Registra compra y llama a la entrada de inventario utilizando la misma conexión.
    Confirma solo al terminar todo; si falla inventario, revierte la compra.
    """
    validar_permisos_operacion(
        sesion,
        roles_permitidos=["administrador", "gerente"],
        id_sucursal_operacion=id_sucursal
    )

    if not detalles_insumos:
        raise ValueError("Debe incluir al menos un insumo en la compra.")

    id_auditoria = sesion.id_usuario if sesion else None

    with transaccion(conn, id_usuario=id_auditoria) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'compra'
                );
                """
            )
            if not cur.fetchone()[0]:
                raise ErrorBaseDatos(
                    "La estructura de 'compra' no está instalada en el esquema base. "
                    "Ejecute 'bd/extension_compras_proveedores.sql' para habilitarla."
                )

            cur.execute("SELECT id_proveedor FROM proveedor WHERE id_proveedor = %s;", (id_proveedor,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"El proveedor con ID {id_proveedor} no existe.")

            cur.execute("SELECT id_sucursal FROM sucursal WHERE id_sucursal = %s;", (id_sucursal,))
            if not cur.fetchone():
                raise ErrorNoEncontrado(f"La sucursal con ID {id_sucursal} no existe.")

            total_compra = Decimal("0.00")
            lotes_para_inventario = []

            for item in detalles_insumos:
                id_insumo = item["id_insumo"]
                cantidad = Decimal(str(item["cantidad"]))
                precio_u = Decimal(str(item["precio_unitario"]))
                f_caducidad = item["fecha_caducidad"]
                f_recepcion = item.get("fecha_recepcion", date.today())

                if cantidad <= 0:
                    raise ValueError(f"La cantidad para el insumo {id_insumo} debe ser mayor a cero.")
                if precio_u < 0:
                    raise ValueError(f"El precio unitario para el insumo {id_insumo} no puede ser negativo.")

                total_compra += cantidad * precio_u
                lotes_para_inventario.append({
                    "id_insumo": id_insumo,
                    "id_sucursal": id_sucursal,
                    "fecha_recepcion": f_recepcion,
                    "fecha_caducidad": f_caducidad,
                    "cantidad": cantidad
                })

            cur.execute(
                """
                INSERT INTO compra (id_proveedor, id_sucursal, total)
                VALUES (%s, %s, %s)
                RETURNING id_compra;
                """,
                (id_proveedor, id_sucursal, total_compra)
            )
            id_compra = cur.fetchone()[0]

            for item in detalles_insumos:
                cur.execute(
                    """
                    INSERT INTO detalle_compra (id_compra, id_insumo, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (
                        id_compra,
                        item["id_insumo"],
                        Decimal(str(item["cantidad"])),
                        Decimal(str(item["precio_unitario"]))
                    )
                )

            if funcion_ingreso_lotes is not None:
                try:
                    funcion_ingreso_lotes(c, id_sucursal, lotes_para_inventario)
                except Exception as inv_err:
                    raise ErrorTransaccion(
                        f"Fallo en el ingreso a inventario de lotes: {inv_err}. La compra se revertirá."
                    ) from inv_err
            else:
                for lote_item in lotes_para_inventario:
                    cur.execute(
                        """
                        INSERT INTO lote (
                            id_insumo, id_sucursal, fecha_recepcion, fecha_caducidad, cantidad_disponible
                        )
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (
                            lote_item["id_insumo"],
                            id_sucursal,
                            lote_item["fecha_recepcion"],
                            lote_item["fecha_caducidad"],
                            lote_item["cantidad"]
                        )
                    )

            return id_compra


def consultar_compras(
    id_sucursal: Optional[int] = None,
    id_proveedor: Optional[int] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Consulta compras registradas."""
    if sesion:
        validar_permisos_operacion(sesion, roles_permitidos=["administrador", "gerente"])
        if not sesion.es_administrador:
            id_sucursal = sesion.id_sucursal

    with transaccion(conn) as c:
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'compra'
                );
                """
            )
            if not cur.fetchone()[0]:
                return []

            query = """
                SELECT 
                    c.id_compra,
                    c.id_proveedor,
                    p.nombre AS nombre_proveedor,
                    c.id_sucursal,
                    s.nombre AS nombre_sucursal,
                    c.fecha_hora,
                    c.total
                FROM compra c
                JOIN proveedor p ON p.id_proveedor = c.id_proveedor
                JOIN sucursal s ON s.id_sucursal = c.id_sucursal
                WHERE (%s::INTEGER IS NULL OR c.id_sucursal = %s)
                  AND (%s::INTEGER IS NULL OR c.id_proveedor = %s)
                ORDER BY c.fecha_hora DESC;
            """
            cur.execute(query, (id_sucursal, id_sucursal, id_proveedor, id_proveedor))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
