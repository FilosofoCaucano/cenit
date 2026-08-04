"""Motor de posición solar.

Implementación del algoritmo simplificado de posición solar de NOAA / Meeus
("Astronomical Algorithms"). No requiere descargar efemérides ni librerías
astronómicas externas: solo usa la librería estándar de Python.

Precisión típica: declinación solar ~0.01°, ecuación del tiempo ~pocos segundos.
Suficiente para calcular fechas de paso cenital y posición solar aproximada.
"""

import math
from datetime import datetime, timedelta, timezone

COLOMBIA_TZ = timezone(timedelta(hours=-5))


def julian_day(dt: datetime) -> float:
    """Día juliano correspondiente a un datetime (se asume/convierte a UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)

    year, month = dt.year, dt.month
    # Los microsegundos importan: solar_noon_utc devuelve un instante con
    # fracción de segundo, y descartarla movía la declinación lo suficiente
    # para cambiar de día cuando el paso cenital cae casi justo entre dos
    # mediodías (Meta/San Martín, 2035: los dos días quedan a 0.1943° del
    # cenit y los separa 1.4e-5°).
    seconds = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    day = dt.day + seconds / 86400

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + a // 4

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


def _sun_position(jd: float):
    """Devuelve (declinación en grados, ecuación del tiempo en minutos)."""
    t = (jd - 2451545.0) / 36525.0

    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0

    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    m_rad = math.radians(m)

    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    c = (
        (1.914602 - t * (0.004817 + 0.000014 * t)) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )

    true_long = l0 + c

    omega = 125.04 - 1934.136 * t
    apparent_long = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))

    eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    eps_corr = eps0 + 0.00256 * math.cos(math.radians(omega))

    decl = math.degrees(
        math.asin(math.sin(math.radians(eps_corr)) * math.sin(math.radians(apparent_long)))
    )

    y = math.tan(math.radians(eps_corr) / 2.0) ** 2
    l0_rad = math.radians(l0)

    eot = 4.0 * math.degrees(
        y * math.sin(2 * l0_rad)
        - 2 * e * math.sin(m_rad)
        + 4 * e * y * math.sin(m_rad) * math.cos(2 * l0_rad)
        - 0.5 * y * y * math.sin(4 * l0_rad)
        - 1.25 * e * e * math.sin(2 * m_rad)
    )

    return decl, eot


def declination(dt: datetime) -> float:
    """Declinación solar (grados) en el instante dt."""
    return _sun_position(julian_day(dt))[0]


def equation_of_time(dt: datetime) -> float:
    """Ecuación del tiempo (minutos) en el instante dt."""
    return _sun_position(julian_day(dt))[1]


def solar_noon_utc(day, longitude_deg: float) -> datetime:
    """Instante UTC del mediodía solar (sol cruzando el meridiano local) para una fecha.

    longitude_deg: positivo al este, negativo al oeste (Colombia es negativo).
    """
    base = datetime(day.year, day.month, day.day, 12, 0, tzinfo=timezone.utc)
    eot = equation_of_time(base)
    minutes_from_midnight = 720 - 4 * longitude_deg - eot
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(
        minutes=minutes_from_midnight
    )


def solar_elevation(dt: datetime, lat_deg: float, lon_deg: float) -> float:
    """Elevación solar (grados) sobre el horizonte para una ubicación e instante dados."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)

    decl, eot = _sun_position(julian_day(dt))

    utc_minutes = dt.hour * 60 + dt.minute + dt.second / 60
    true_solar_time = utc_minutes + 4 * lon_deg + eot
    hour_angle = (true_solar_time / 4.0) - 180.0

    lat_rad = math.radians(lat_deg)
    decl_rad = math.radians(decl)
    ha_rad = math.radians(hour_angle)

    return math.degrees(
        math.asin(
            math.sin(lat_rad) * math.sin(decl_rad)
            + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad)
        )
    )


def shadow_length(height_m: float, elevation_deg: float):
    """Longitud de la sombra proyectada por un objeto vertical. None si el sol está bajo el horizonte."""
    if elevation_deg <= 0.05:
        return None
    return height_m / math.tan(math.radians(elevation_deg))
