"""Simulador visual: globo 3D interactivo con el punto subsolar y los trópicos.

Se apoya en Plotly (mapa mundial ya incluido en la librería, sin descargar
datasets aparte) y se abre en el navegador por defecto del sistema.
"""

import os
import tempfile
import webbrowser
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go

import solar

TROPIC_LAT = 23.437


def _parallel_trace(lat_value, name, color, dash="dot"):
    lons = list(range(-180, 181, 2))
    lats = [lat_value] * len(lons)
    return go.Scattergeo(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=1.3, color=color, dash=dash),
        name=name,
    )


def _subsolar_point(dt_utc):
    decl = solar.declination(dt_utc)
    eot = solar.equation_of_time(dt_utc)
    utc_minutes = dt_utc.hour * 60 + dt_utc.minute + dt_utc.second / 60
    lon_sub = (720 - utc_minutes - eot) / 4
    lon_sub = ((lon_sub + 180) % 360) - 180
    return decl, lon_sub


def build_globe_figure(lat, lon, name, next_passage_utc):
    now = datetime.now(timezone.utc)

    fig = go.Figure()

    fig.add_trace(_parallel_trace(0, "Ecuador", "#6ec6ff", dash="solid"))
    fig.add_trace(_parallel_trace(TROPIC_LAT, "Trópico de Cáncer", "#f5b942"))
    fig.add_trace(_parallel_trace(-TROPIC_LAT, "Trópico de Capricornio", "#f5b942"))

    fig.add_trace(
        go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode="markers+text",
            marker=dict(size=10, color="#e06c75", symbol="circle"),
            text=[name],
            textposition="top center",
            name=name,
        )
    )

    sub_lat_now, sub_lon_now = _subsolar_point(now)
    fig.add_trace(
        go.Scattergeo(
            lon=[sub_lon_now],
            lat=[sub_lat_now],
            mode="markers+text",
            marker=dict(size=14, color="#ffe27a", symbol="star"),
            text=["☀ Sol ahora"],
            textposition="bottom center",
            name="Punto subsolar (ahora)",
        )
    )

    if next_passage_utc:
        sub_lat_p, sub_lon_p = _subsolar_point(next_passage_utc)
        fig.add_trace(
            go.Scattergeo(
                lon=[sub_lon_p],
                lat=[sub_lat_p],
                mode="markers",
                marker=dict(size=12, color="#7fdc7f", symbol="star"),
                name="Sol en el próximo paso cenital",
            )
        )

    # Recorrido anual del punto subsolar a la hora del mediodía solar de la ubicación
    frames = []
    slider_steps = []
    start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    noon_ref = solar.solar_noon_utc(now.date(), lon)
    hour_fixed, minute_fixed = noon_ref.hour, noon_ref.minute

    for i in range(0, 366, 4):
        moment = (start + timedelta(days=i)).replace(hour=hour_fixed, minute=minute_fixed)
        flat, flon = _subsolar_point(moment)
        label = moment.strftime("%d %b")
        frames.append(
            go.Frame(
                data=[go.Scattergeo(lon=[flon], lat=[flat])],
                traces=[4],
                name=label,
            )
        )
        slider_steps.append(
            dict(
                method="animate",
                args=[[label], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                label=moment.strftime("%d/%m"),
            )
        )

    fig.frames = frames

    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=lon, lat=lat, roll=0),
        showland=True,
        landcolor="#2b3a2f",
        showocean=True,
        oceancolor="#12202e",
        showcountries=True,
        countrycolor="#4a4a4a",
        showlakes=False,
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        title=f"Simulador del paso cenital — {name}",
        paper_bgcolor="#1a1a1a",
        font_color="white",
        legend=dict(bgcolor="rgba(0,0,0,0.4)"),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶ Reproducir año",
                        method="animate",
                        args=[None, dict(frame=dict(duration=60, redraw=True), fromcurrent=True)],
                    )
                ],
            )
        ],
        sliders=[dict(steps=slider_steps, currentvalue=dict(prefix="Día: "))],
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig


def open_globe_simulator(lat, lon, name, next_passage_utc):
    fig = build_globe_figure(lat, lon, name, next_passage_utc)
    path = os.path.join(tempfile.gettempdir(), "cenit_simulador.html")
    fig.write_html(path, auto_open=False)
    webbrowser.open(f"file:///{path}")
    return path
