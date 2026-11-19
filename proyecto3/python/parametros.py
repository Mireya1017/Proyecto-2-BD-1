"""Parametros compartidos del escenario simulado del Proyecto 3.

Se conservan 2400 reservas y 3000 visitas en todo el periodo.
Las cantidades por sucursal/mes y los estados dejan de ser cuotas iguales.
Los pesos y probabilidades son SUPUESTOS de simulacion, no datos reales.
No se fijan diferencias de calidad o rendimiento entre sucursales.
"""

from datetime import date, time
from math import floor

FECHA_INICIO = date(2026, 5, 1)
FECHA_CORTE_EXCLUSIVA = date(2026, 11, 1)

TOTAL_RESERVAS = 2400
TOTAL_VISITAS = 3000

# Variacion aleatoria de volumen alrededor del peso mensual.
FACTOR_VOLUMEN_MIN = 0.85
FACTOR_VOLUMEN_MAX = 1.15

# Hipotesis de demanda mensual; no representa estacionalidad comprobada.
PESOS_MES = {5: 0.85, 6: 0.95, 7: 1.10, 8: 1.05, 9: 0.90, 10: 1.15}

# Lunes = 0 y domingo = 6 (datetime.weekday).
PESOS_DIA_SEMANA = {0: 0.85, 1: 0.85, 2: 0.95, 3: 1.0,
                    4: 1.15, 5: 1.40, 6: 1.30}

# Hipotesis de mayor demanda durante almuerzo y cena.
PESOS_HORA = {11: 0.7, 12: 1.3, 13: 2.2, 14: 2.0, 15: 1.0,
              16: 0.6, 17: 0.8, 18: 1.5, 19: 1.8, 20: 1.1}

# Cada sucursal/mes recibe probabilidades dentro de los mismos rangos.
# No se fuerzan cantidades ni porcentajes exactos de estados.
PROBABILIDAD_ATENCION_MIN = 0.68
PROBABILIDAD_ATENCION_MAX = 0.84
PROPORCION_CANCELADAS_MIN = 0.45
PROPORCION_CANCELADAS_MAX = 0.65

HORA_APERTURA = time(11, 0)
HORA_CIERRE = time(23, 0)
HORA_PRIMERA_RESERVA = time(11, 0)
HORA_ULTIMA_RESERVA = time(20, 0)
HORA_ULTIMA_LLEGADA_SIN_RESERVA = time(20, 30)

DURACION_ESTIMADA_RESERVA_MINUTOS = 90
DESFASE_LLEGADA_MINUTOS_MIN = -10
DESFASE_LLEGADA_MINUTOS_MAX = 10
DURACION_VISITA_MINUTOS_MIN = 45
DURACION_VISITA_MINUTOS_MAX = 90
LIBERACION_MINUTOS_MIN = 5
LIBERACION_MINUTOS_MAX = 20

PERSONAS_POR_GRUPO = [1, 2, 3, 4, 5, 6, 7, 8]
PROBABILIDADES_PERSONAS = [0.05, 0.30, 0.15, 0.25, 0.10, 0.10, 0.03, 0.02]
SEMILLA_RESERVAS = 3088
SEMILLA_VISITAS = 3089


def distribuir_total(p_total, p_claves, p_pesos):
    """Reparte enteros por pesos y conserva exactamente el total global.

    Primero asigna la parte entera; las unidades restantes van a las
    fracciones mayores. El orden de entrada resuelve los empates.
    """
    if p_total < 0 or len(p_claves) != len(p_pesos) or not p_claves:
        raise ValueError("Total, claves o pesos invalidos.")
    if any(v_peso <= 0 for v_peso in p_pesos):
        raise ValueError("Los pesos deben ser positivos.")
    v_suma = sum(p_pesos)
    v_cuotas = [p_total * v_peso / v_suma for v_peso in p_pesos]
    v_cantidades = [floor(v_cuota) for v_cuota in v_cuotas]
    v_pendientes = p_total - sum(v_cantidades)
    v_orden = sorted(range(len(p_claves)),
                     key=lambda v_i: (-(v_cuotas[v_i] - v_cantidades[v_i]), v_i))
    for v_i in v_orden[:v_pendientes]:
        v_cantidades[v_i] += 1
    return dict(zip(p_claves, v_cantidades))
