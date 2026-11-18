"""
Suite Completa de Pruebas Unitarias para el Módulo de Pablo (Integrante 2).
Valida seguridad, hash PBKDF2, roles, permisos, lógica de reservas, concurrencia,
reporte de sucursales con CTEs, coordinación de compras con inventario y menús de consola.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.auth import (
    generar_hash_contrasena,
    verificar_contrasena,
    SesionUsuario,
    validar_permisos_operacion
)
from app.database import (
    ErrorAutenticacion,
    ErrorPermiso,
    ErrorCapacidad,
    ErrorRestriccion,
    ErrorTransaccion,
    establecer_contexto_usuario
)
from app.reservas import (
    sugerir_mesas_adecuadas,
    crear_reserva,
    modificar_reserva,
    cancelar_reserva,
    ADVISORY_LOCK_RESERVAS
)
from app.compras import registrar_compra
from app.reportes import reporte_rendimiento_sucursales
from app.consola import formatear_tabla, obtener_opciones_menu_pablo


class TestSeguridadYAuth(unittest.TestCase):
    """Pruebas de hash criptográfico, sal y autenticación."""

    def test_hash_contrasena_genera_formato_correcto(self):
        h = generar_hash_contrasena("MiPasswordSeguro123!")
        partes = h.split("$")
        self.assertEqual(len(partes), 4)
        self.assertEqual(partes[0], "pbkdf2_sha256")
        self.assertEqual(partes[1], "100000")
        self.assertEqual(len(partes[2]), 32)
        self.assertEqual(len(partes[3]), 64)

    def test_verificacion_contrasena_correcta(self):
        h = generar_hash_contrasena("ContraseñaCorrecta123")
        self.assertTrue(verificar_contrasena("ContraseñaCorrecta123", h))

    def test_verificacion_contrasena_incorrecta(self):
        h = generar_hash_contrasena("ContraseñaCorrecta123")
        self.assertFalse(verificar_contrasena("ContraseñaErronea", h))
        self.assertFalse(verificar_contrasena("", h))

    def test_contrasenas_identicas_tienen_hashes_distintos_por_sal(self):
        h1 = generar_hash_contrasena("ClaveRepetida")
        h2 = generar_hash_contrasena("ClaveRepetida")
        self.assertNotEqual(h1, h2)
        self.assertTrue(verificar_contrasena("ClaveRepetida", h1))
        self.assertTrue(verificar_contrasena("ClaveRepetida", h2))


class TestSesionYPermisos(unittest.TestCase):
    """Pruebas de roles y matriz de permisos RBAC."""

    def setUp(self):
        self.admin = SesionUsuario(id_usuario=1, nombre_usuario="admin", rol="administrador", id_sucursal=1)
        self.gerente_1 = SesionUsuario(id_usuario=2, nombre_usuario="gerente1", rol="gerente", id_sucursal=1)
        self.mesero_1 = SesionUsuario(id_usuario=3, nombre_usuario="mesero1", rol="mesero", id_sucursal=1)

    def test_rol_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            SesionUsuario(id_usuario=9, nombre_usuario="hacker", rol="superadmin", id_sucursal=1)

    def test_admin_tiene_acceso_general(self):
        self.assertTrue(self.admin.puede_operar_en_sucursal(1))
        self.assertTrue(self.admin.puede_operar_en_sucursal(2))
        self.assertTrue(self.admin.es_administrador)

    def test_gerente_solo_accede_su_sucursal(self):
        self.assertTrue(self.gerente_1.puede_operar_en_sucursal(1))
        self.assertFalse(self.gerente_1.puede_operar_en_sucursal(2))

    def test_validacion_permiso_sin_sesion_falla(self):
        with self.assertRaises(ErrorAutenticacion):
            validar_permisos_operacion(None, roles_permitidos="administrador")

    def test_validacion_permiso_rol_inadecuado_falla(self):
        with self.assertRaises(ErrorPermiso):
            validar_permisos_operacion(self.mesero_1, roles_permitidos=["administrador", "gerente"])

    def test_validacion_permiso_sucursal_inadecuada_falla(self):
        with self.assertRaises(ErrorPermiso):
            validar_permisos_operacion(self.gerente_1, roles_permitidos="gerente", id_sucursal_operacion=2)

    def test_validacion_permiso_admin_ignora_restriccion_sucursal(self):
        validar_permisos_operacion(self.admin, roles_permitidos="administrador", id_sucursal_operacion=2)


class TestAuditoriaContexto(unittest.TestCase):
    """Prueba de propagación del identificador de usuario para auditoría."""

    def test_establecer_contexto_usuario_invoca_set_config_local(self):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        establecer_contexto_usuario(mock_conn, id_usuario=42)

        # Debe llamar set_config con is_local=true
        mock_cur.execute.assert_called_once_with(
            "SELECT set_config('app.id_usuario', %s, true);",
            ('42',)
        )


class TestLogicaReservas(unittest.TestCase):
    """Pruebas de algoritmo de sugerencia y validación de reservas."""

    def test_advisory_lock_id_coincide_con_bd(self):
        self.assertEqual(ADVISORY_LOCK_RESERVAS, 308802)

    def test_sugerir_mesas_capacidad_exacta(self):
        mesas = [
            {"id_mesa": 1, "numero": 1, "capacidad": 2, "zona": "interior"},
            {"id_mesa": 2, "numero": 2, "capacidad": 4, "zona": "interior"},
            {"id_mesa": 3, "numero": 3, "capacidad": 6, "zona": "interior"},
        ]
        sug = sugerir_mesas_adecuadas(mesas, cantidad_personas=4, zona_preferida="interior")
        self.assertTrue(len(sug) >= 1)
        self.assertEqual(sug[0][0]["capacidad"], 4)

    def test_sugerir_mesas_agrupa_misma_zona(self):
        mesas = [
            {"id_mesa": 1, "numero": 1, "capacidad": 2, "zona": "interior"},
            {"id_mesa": 2, "numero": 2, "capacidad": 2, "zona": "interior"},
            {"id_mesa": 5, "numero": 5, "capacidad": 4, "zona": "exterior"},
        ]
        sug = sugerir_mesas_adecuadas(mesas, cantidad_personas=3, zona_preferida="interior")
        self.assertTrue(len(sug) >= 1)
        combo = sug[0]
        total_cap = sum(m["capacidad"] for m in combo)
        self.assertGreaterEqual(total_cap, 3)
        self.assertTrue(all(m["zona"] == "interior" for m in combo))

    def test_crear_reserva_valida_fechas_y_personas(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        ahora = datetime.now()

        # Personas <= 0
        with self.assertRaises(ValueError):
            crear_reserva(1, 1, ahora, ahora + timedelta(hours=2), 0, [1], sesion=admin)

        # Fin <= Inicio
        with self.assertRaises(ValueError):
            crear_reserva(1, 1, ahora, ahora - timedelta(hours=1), 4, [1], sesion=admin)

        # Sin mesas
        with self.assertRaises(ValueError):
            crear_reserva(1, 1, ahora, ahora + timedelta(hours=2), 4, [], sesion=admin)

    def test_crear_reserva_rechaza_mesas_de_distinta_zona(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Cliente existe, sucursal existe, mesas devuelven zona interior y exterior
        mock_cur.fetchone.side_effect = [
            [1], # cliente
            [1], # sucursal
        ]
        mock_cur.fetchall.return_value = [
            (1, 1, 4, "interior"),
            (5, 1, 4, "exterior")
        ]

        ahora = datetime.now()
        with self.assertRaises(ErrorRestriccion) as ctx:
            crear_reserva(
                id_cliente=1, id_sucursal=1,
                fecha_hora_inicio=ahora, fecha_hora_fin_estimada=ahora + timedelta(hours=2),
                cantidad_personas=4, ids_mesas=[1, 5],
                sesion=admin, conn=mock_conn
            )
        self.assertIn("diferentes zonas", str(ctx.exception))

    def test_crear_reserva_rechaza_capacidad_insuficiente(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchone.side_effect = [
            [1], # cliente
            [1], # sucursal
        ]
        # Mesa admite solo 2 personas y se piden 4
        mock_cur.fetchall.return_value = [
            (1, 1, 2, "interior")
        ]

        ahora = datetime.now()
        with self.assertRaises(ErrorCapacidad) as ctx:
            crear_reserva(
                id_cliente=1, id_sucursal=1,
                fecha_hora_inicio=ahora, fecha_hora_fin_estimada=ahora + timedelta(hours=2),
                cantidad_personas=4, ids_mesas=[1],
                sesion=admin, conn=mock_conn
            )
        self.assertIn("Capacidad insuficiente", str(ctx.exception))


class TestComprasEInventarioCoordinado(unittest.TestCase):
    """Prueba de la coordinación atómica entre compras e inventario (Pablo y Nathalie)."""

    def test_compra_revierte_si_falla_inventario(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchone.side_effect = [
            [True], # existe tabla compra
            [1],    # existe proveedor
            [1],    # existe sucursal
            [101],  # RETURNING id_compra = 101
        ]

        def funcion_nathalie_con_error(conn, id_sucursal, lotes):
            raise RuntimeError("Error al persistir existencias en lote.")

        detalles = [{
            "id_insumo": 1,
            "cantidad": 500,
            "precio_unitario": 0.05,
            "fecha_caducidad": date.today() + timedelta(days=30)
        }]

        with self.assertRaises(ErrorTransaccion) as ctx:
            registrar_compra(
                id_proveedor=1,
                id_sucursal=1,
                detalles_insumos=detalles,
                funcion_ingreso_lotes=funcion_nathalie_con_error,
                sesion=admin,
                conn=mock_conn
            )
        self.assertIn("Fallo en el ingreso a inventario de lotes", str(ctx.exception))


class TestReportesCTE(unittest.TestCase):
    """Prueba del reporte de sucursales y prevención de producto cartesiano."""

    def test_reporte_consolida_sin_multiplicar(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Simulamos resultados de la consulta con CTEs:
        # Fila: (id_sucursal, nombre, direccion, reservas, ventas, importe)
        mock_cur.fetchall.return_value = [
            (1, "Oakland Mall", "Dirección OM", 3, 3, Decimal("168.00")),
            (2, "Ciudad Cayalá", "Dirección CC", 2, 1, Decimal("90.00"))
        ]

        rep = reporte_rendimiento_sucursales(sesion=admin, conn=mock_conn)

        self.assertEqual(rep["totales"]["total_reservas"], 5)
        self.assertEqual(rep["totales"]["total_ventas"], 4)
        self.assertEqual(rep["totales"]["total_importe_vendido"], 258.00)
        self.assertEqual(len(rep["filas"]), 2)


class TestConsolaMenues(unittest.TestCase):
    """Pruebas de la capa de presentación y opciones para Yu-fong."""

    def test_opciones_menu_administrador_incluye_todo(self):
        admin = SesionUsuario(1, "admin", "administrador", 1)
        opciones = obtener_opciones_menu_pablo(admin)
        self.assertIn("reservas", opciones)
        self.assertIn("compras", opciones)
        self.assertIn("usuarios", opciones)
        self.assertIn("bitacora", opciones)
        self.assertIn("reporte_sucursales", opciones)

    def test_opciones_menu_mesero_solo_reservas(self):
        mesero = SesionUsuario(3, "mesero", "mesero", 1)
        opciones = obtener_opciones_menu_pablo(mesero)
        self.assertIn("reservas", opciones)
        self.assertNotIn("usuarios", opciones)
        self.assertNotIn("bitacora", opciones)
        self.assertNotIn("reporte_sucursales", opciones)
        self.assertNotIn("compras", opciones)

    def test_formatear_tabla_genera_tabla_legible(self):
        filas = [
            {"id": 1, "nombre": "Oakland Mall", "ventas": 10},
            {"id": 2, "nombre": "Ciudad Cayalá", "ventas": 5}
        ]
        tabla = formatear_tabla(filas)
        self.assertIn("Oakland Mall", tabla)
        self.assertIn("Ciudad Cayalá", tabla)
        self.assertIn("+", tabla)

    def test_formatear_tabla_vacia_retorna_aviso(self):
        tabla = formatear_tabla([])
        self.assertIn("No se encontraron registros", tabla)


if __name__ == "__main__":
    unittest.main()
