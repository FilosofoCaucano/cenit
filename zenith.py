"""Cálculo de las fechas de Paso Cenital del Sol para una ubicación dada.

El "paso cenital" ocurre cuando, al mediodía solar, el sol queda exactamente
perpendicular sobre un punto (declinación solar == latitud del lugar). Esto
solo es posible entre los trópicos (-23.437° y 23.437°), donde ocurre dos
veces al año. Colombia está enteramente dentro de esa franja.
"""

from datetime import date, datetime, timedelta

import solar

TROPIC_LIMIT = 23.437


def _declination_at_local_noon(day: date, lat: float, lon: float) -> float:
    noon_utc = solar.solar_noon_utc(day, lon)
    return solar.declination(noon_utc)


def find_zenith_passages(lat: float, lon: float, year: int):
    """Lista de datetimes (UTC) de los pasos cenitales del sol en el año dado."""
    if abs(lat) > TROPIC_LIMIT:
        return []

    start = date(year, 1, 1)
    days_in_year = (date(year + 1, 1, 1) - start).days

    diffs = [
        _declination_at_local_noon(start + timedelta(days=i), lat, lon) - lat
        for i in range(days_in_year + 1)
    ]

    passage_days = []
    for i in range(len(diffs) - 1):
        d0, d1 = diffs[i], diffs[i + 1]
        if d0 == 0:
            passage_days.append(start + timedelta(days=i))
        elif d0 * d1 < 0:
            # El cruce cae entre dos mediodías solares: nos quedamos con el día
            # en que el sol pasa MÁS cerca del cenit. Comparar |d0| con |d1| es
            # equivalente a redondear la fracción, pero no depende del modo de
            # redondeo: round() de Python redondea al par y Math.round() de JS
            # redondea hacia arriba, así que en un empate exacto el escritorio y
            # el móvil daban días distintos (Meta/San Martín, 2035).
            passage_days.append(start + timedelta(days=i if abs(d0) <= abs(d1) else i + 1))

    return [solar.solar_noon_utc(d, lon) for d in passage_days]


def next_zenith_passage(lat: float, lon: float, now_utc: datetime):
    """Próximo paso cenital (datetime UTC) a partir de now_utc, o None si no aplica."""
    for year in (now_utc.year, now_utc.year + 1):
        for passage in find_zenith_passages(lat, lon, year):
            if passage > now_utc:
                return passage
    return None
