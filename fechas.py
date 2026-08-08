"""Fechas en español, sin depender del locale de la máquina.

strftime("%B") devuelve el mes en el idioma que tenga configurado el sistema, y
Python arranca sin locale: en un equipo cualquiera salía "01 de April de 2026".
En un ejecutable que se reparte a desconocidos eso además es inconsistente —
cada quien vería una cosa—, y setlocale no sirve de red de seguridad porque el
nombre del locale español cambia entre Windows y Linux y puede no estar
instalado. Con una tabla propia el resultado es el mismo en todas partes.
"""

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

MESES_CORTOS = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]


def _hora12(dt):
    """Hora en formato de 12 horas, como se escribe en Colombia."""
    hora = dt.hour % 12 or 12
    sufijo = "a. m." if dt.hour < 12 else "p. m."
    return f"{hora}:{dt.minute:02d} {sufijo}"


def dia_mes_anio(dt):
    """'01 de abril de 2026'"""
    return f"{dt.day:02d} de {MESES[dt.month - 1]} de {dt.year}"


def completa(dt):
    """'01 de abril de 2026, 12:00 p. m.'"""
    return f"{dia_mes_anio(dt)}, {_hora12(dt)}"


def dia_mes_corto(dt):
    """'01 abr'"""
    return f"{dt.day:02d} {MESES_CORTOS[dt.month - 1]}"
