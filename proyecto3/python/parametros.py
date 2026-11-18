
# ============================================================
# PROYECTO 3 - PARAMETROS COMPARTIDOS
# Responsable: Nathalie
#
# Proposito:
# Centralizar las reglas de generacion de reservas y visitas.
#
# Entradas:
# No recibe archivos ni parametros externos.
#
# Salidas:
# Constantes compartidas para los generadores Python.
#
# Uso:
# from parametros import FECHA_INICIO, SEMILLA_RESERVAS
# ============================================================

from datetime import date, time


# ------------------------------------------------------------
# PERIODO DE ANALISIS
# ------------------------------------------------------------

FECHA_INICIO = date(2026, 5, 1)
FECHA_CORTE_EXCLUSIVA = date(2026, 11, 1)


# ------------------------------------------------------------
# CANTIDADES POR MES Y SUCURSAL
# ------------------------------------------------------------

RESERVAS_ATENDIDAS_POR_MES_SUCURSAL = 150
RESERVAS_CANCELADAS_POR_MES_SUCURSAL = 25
RESERVAS_NO_ASISTIO_POR_MES_SUCURSAL = 25

VISITAS_SIN_RESERVA_POR_MES_SUCURSAL = 100


# ------------------------------------------------------------
# HORARIOS DEL RESTAURANTE
# ------------------------------------------------------------

HORA_APERTURA = time(11, 0)
HORA_CIERRE = time(23, 0)

HORA_PRIMERA_RESERVA = time(11, 0)
HORA_ULTIMA_RESERVA = time(20, 0)

HORA_ULTIMA_LLEGADA_SIN_RESERVA = time(20, 30)


# ------------------------------------------------------------
# DURACIONES Y VARIACIONES
# ------------------------------------------------------------

DURACION_ESTIMADA_RESERVA_MINUTOS = 90

DESFASE_LLEGADA_MINUTOS_MIN = -10
DESFASE_LLEGADA_MINUTOS_MAX = 10

DURACION_VISITA_MINUTOS_MIN = 45
DURACION_VISITA_MINUTOS_MAX = 90

LIBERACION_MINUTOS_MIN = 5
LIBERACION_MINUTOS_MAX = 20


# ------------------------------------------------------------
# TAMANO DE LOS GRUPOS Y PROBABILIDADES
# ------------------------------------------------------------

PERSONAS_POR_GRUPO = [1, 2, 3, 4, 5, 6, 7, 8]

PROBABILIDADES_PERSONAS = [
    0.05,
    0.30,
    0.15,
    0.25,
    0.10,
    0.10,
    0.03,
    0.02
]


# ------------------------------------------------------------
# SEMILLAS PARA REPRODUCIBILIDAD
# ------------------------------------------------------------

SEMILLA_RESERVAS = 3088
SEMILLA_VISITAS = 3089
