"""Cenit — Paso Cenital del Sol en Colombia.

Aplicación de escritorio que calcula, para cualquier ubicación de Colombia,
las dos fechas del año en que el sol pasa exactamente por el cenit al
mediodía solar (el momento en que los objetos verticales no proyectan
sombra). Es un fenómeno exclusivo de la franja tropical, que cubre menos
del 40% de la superficie terrestre y del que Colombia goza en su totalidad.
"""

from datetime import datetime, timedelta

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import fechas
import lugares
import mapsim
import solar
import zenith

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

KM_POR_GRADO = 111.32
DIAS_ENTRE_TROPICOS_PCT = 39.8  # % de la superficie terrestre entre los trópicos

# Cuánto se sigue mostrando "¡Es ahora!" después del instante exacto, antes de
# pasar a contar hacia el siguiente paso.
SEGUNDOS_AVISO_PASO = 300


class CenitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cenit — Paso Cenital del Sol en Colombia")
        self.geometry("1150x720")
        self.minsize(950, 620)

        self.lat = None
        self.lon = None
        self.location_name = None
        self.passages_this_year = []
        self.next_passage = None
        self.countdown_job = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

        # Ubicación inicial: Bogotá D.C.
        self.depto_menu.set("Bogotá D.C.")
        self._on_depto_change("Bogotá D.C.")
        self._calcular()

    # ---------------------------------------------------------- sidebar --

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="☀️ Cenit", font=ctk.CTkFont(size=26, weight="bold")
        ).pack(padx=20, pady=(24, 0), anchor="w")
        ctk.CTkLabel(
            sidebar,
            text="Paso Cenital del Sol\nen Colombia",
            font=ctk.CTkFont(size=13),
            text_color="gray70",
            justify="left",
        ).pack(padx=20, pady=(0, 24), anchor="w")

        ctk.CTkLabel(
            sidebar, text="Departamento", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(padx=20, pady=(0, 4), anchor="w")
        self.depto_menu = ctk.CTkOptionMenu(
            sidebar,
            values=lugares.NOMBRES_DEPARTAMENTOS,
            command=self._on_depto_change,
            width=220,
        )
        self.depto_menu.pack(padx=20, pady=(0, 12))

        ctk.CTkLabel(
            sidebar, text="Municipio", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(padx=20, pady=(0, 4), anchor="w")
        self.city_menu = ctk.CTkOptionMenu(
            sidebar, values=["—"], command=self._on_city_change, width=220
        )
        self.city_menu.pack(padx=20, pady=(0, 16))

        self.custom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        ctk.CTkLabel(self.custom_frame, text="Latitud").pack(anchor="w")
        self.lat_entry = ctk.CTkEntry(self.custom_frame, placeholder_text="ej. 4.7110")
        self.lat_entry.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(self.custom_frame, text="Longitud").pack(anchor="w")
        self.lon_entry = ctk.CTkEntry(self.custom_frame, placeholder_text="ej. -74.0721")
        self.lon_entry.pack(fill="x")

        self.calc_button = ctk.CTkButton(sidebar, text="Calcular", command=self._calcular)
        self.calc_button.pack(padx=20, pady=(20, 8), fill="x")

        self.globe_button = ctk.CTkButton(
            sidebar,
            text="🌍 Simulador 3D",
            fg_color="#3a7d44",
            hover_color="#2e6236",
            command=self._abrir_simulador,
        )
        self.globe_button.pack(padx=20, pady=(0, 8), fill="x")

        self.error_label = ctk.CTkLabel(sidebar, text="", text_color="#e06c75", wraplength=220)
        self.error_label.pack(padx=20, pady=(0, 10))

        ctk.CTkLabel(
            sidebar,
            text=(
                "El paso cenital solo ocurre\n"
                "entre los trópicos: cualquier\n"
                "punto de Colombia lo vive\n"
                "dos veces al año."
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            justify="left",
        ).pack(padx=20, pady=(30, 0), anchor="w", side="bottom")

    def _on_depto_change(self, departamento):
        """Al cambiar de departamento, recargamos su lista de municipios."""
        if departamento == lugares.PERSONALIZADO:
            self.city_menu.configure(values=["—"], state="disabled")
            self.city_menu.set("—")
            self.custom_frame.pack(padx=20, pady=(0, 12), fill="x")
            return

        self.custom_frame.pack_forget()
        municipios = lugares.municipios(departamento)
        self.city_menu.configure(values=municipios, state="normal")
        self.city_menu.set(municipios[0])

    def _on_city_change(self, _seleccion):
        pass

    # ------------------------------------------------------------- main --

    def _build_main(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(
            container, text="", font=ctk.CTkFont(size=22, weight="bold"), anchor="w"
        )
        self.header_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.subheader_label = ctk.CTkLabel(
            container, text="", font=ctk.CTkFont(size=13), text_color="gray70", anchor="w"
        )
        self.subheader_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        # Countdown card
        countdown_card = ctk.CTkFrame(container, corner_radius=14)
        countdown_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(
            countdown_card, text="Próximo paso cenital", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(16, 2))
        self.next_date_label = ctk.CTkLabel(countdown_card, text="—", font=ctk.CTkFont(size=15))
        self.next_date_label.pack()
        self.countdown_label = ctk.CTkLabel(
            countdown_card, text="—", font=ctk.CTkFont(size=34, weight="bold"), text_color="#f5b942"
        )
        self.countdown_label.pack(pady=(6, 18))

        # Both passages card
        passages_card = ctk.CTkFrame(container, corner_radius=14)
        passages_card.grid(row=3, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        ctk.CTkLabel(
            passages_card, text="Los dos pasos del año", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(padx=16, pady=(16, 8), anchor="w")
        self.passages_text = ctk.CTkLabel(
            passages_card, text="—", font=ctk.CTkFont(size=13), justify="left", anchor="w"
        )
        self.passages_text.pack(padx=16, pady=(0, 16), anchor="w")

        # Curious facts card
        facts_card = ctk.CTkFrame(container, corner_radius=14)
        facts_card.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        ctk.CTkLabel(
            facts_card, text="Datos curiosos", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(padx=16, pady=(16, 8), anchor="w")
        self.facts_text = ctk.CTkLabel(
            facts_card, text="—", font=ctk.CTkFont(size=13), justify="left", anchor="w", wraplength=380
        )
        self.facts_text.pack(padx=16, pady=(0, 16), anchor="w")

        # Shadow chart card
        chart_card = ctk.CTkFrame(container, corner_radius=14)
        chart_card.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 4))
        ctk.CTkLabel(
            chart_card,
            text="Sombra de un objeto de 1.7 m a lo largo del día",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=16, pady=(16, 4), anchor="w")
        ctk.CTkLabel(
            chart_card,
            text="Comparación entre hoy y el día del próximo paso cenital",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        ).pack(padx=16, pady=(0, 8), anchor="w")

        self.figure = Figure(figsize=(8, 3.4), dpi=100, facecolor="#242424")
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_card)
        self.canvas.get_tk_widget().pack(padx=12, pady=(0, 16), fill="both", expand=True)

    # --------------------------------------------------------------- logic --

    def _calcular(self):
        self.error_label.configure(text="")
        departamento = self.depto_menu.get()

        if departamento == lugares.PERSONALIZADO:
            try:
                lat = float(self.lat_entry.get().replace(",", "."))
                lon = float(self.lon_entry.get().replace(",", "."))
            except ValueError:
                self.error_label.configure(text="Ingresa latitud y longitud válidas.")
                return
            if not (-4.5 <= lat <= 13.5 and -82 <= lon <= -66):
                self.error_label.configure(
                    text="Esas coordenadas parecen estar fuera de Colombia."
                )
                return
            name = f"Coordenadas personalizadas ({lat:.4f}, {lon:.4f})"
        else:
            municipio = self.city_menu.get()
            coords = lugares.coordenadas(departamento, municipio)
            if coords is None:
                self.error_label.configure(text="Elige un municipio de la lista.")
                return
            lat, lon = coords
            name = f"{municipio}, {departamento}"

        self.lat, self.lon, self.location_name = lat, lon, name

        now_utc = datetime.now(solar.COLOMBIA_TZ).astimezone()
        this_year = now_utc.year
        self.passages_this_year = zenith.find_zenith_passages(lat, lon, this_year)
        self.next_passage = zenith.next_zenith_passage(lat, lon, now_utc)

        self._update_header()
        self._update_passages_panel()
        self._update_facts_panel()
        self._update_chart()
        self._start_countdown()

    def _update_header(self):
        self.header_label.configure(text=f"📍 {self.location_name}")
        self.subheader_label.configure(
            text=f"Latitud {self.lat:.4f}°, longitud {self.lon:.4f}°"
        )

    def _update_passages_panel(self):
        if not self.passages_this_year:
            self.passages_text.configure(
                text="Esta ubicación está fuera de la franja tropical: el sol nunca\n"
                "llega a pasar exactamente por el cenit aquí."
            )
            return

        etiquetas = ["Primer paso (sol subiendo hacia junio)", "Segundo paso (sol bajando hacia diciembre)"]
        lineas = []
        for etiqueta, p in zip(etiquetas, self.passages_this_year):
            local = p.astimezone(solar.COLOMBIA_TZ)
            lineas.append(f"{etiqueta}:\n  {fechas.completa(local)}")

        if len(self.passages_this_year) == 2:
            dias = (self.passages_this_year[1] - self.passages_this_year[0]).days
            lineas.append(f"\nDiferencia entre ambos: {dias} días.")

        self.passages_text.configure(text="\n".join(lineas))

    def _update_facts_panel(self):
        dist_ecuador = abs(self.lat) * KM_POR_GRADO
        hemisferio = "norte" if self.lat >= 0 else "sur"

        facts = [
            f"• Estás a ~{dist_ecuador:.0f} km del ecuador, en el hemisferio {hemisferio}.",
            f"• Solo el {DIAS_ENTRE_TROPICOS_PCT}% de la superficie terrestre está entre los "
            "trópicos y puede vivir este fenómeno; el resto del planeta nunca ve el sol "
            "exactamente en su cenit.",
            "• Durante el paso cenital, un poste o una persona de pie no proyecta ninguna "
            "sombra al mediodía solar, por unos segundos.",
            "• Culturas prehispánicas de los Andes usaban columnas y pozos verticales "
            "(gnómones) para detectar este momento y ajustar calendarios agrícolas y "
            "ceremoniales.",
            "• Cerca del ecuador el crepúsculo es corto y casi constante todo el año "
            "(~20 minutos), porque el sol sube y baja casi perpendicular al horizonte.",
        ]
        self.facts_text.configure(text="\n\n".join(facts))

    def _update_chart(self):
        self.ax.clear()

        today = datetime.now(solar.COLOMBIA_TZ).date()
        target_date = None
        if self.next_passage:
            target_date = self.next_passage.astimezone(solar.COLOMBIA_TZ).date()

        self._plot_shadow_curve(today, label="Hoy", color="#5aa9e6")
        if target_date and target_date != today:
            self._plot_shadow_curve(target_date, label="Día del paso cenital", color="#f5b942")

        self.ax.set_ylim(0, 5)
        self.ax.set_xlabel("Hora local", color="white")
        self.ax.set_ylabel("Longitud de sombra (m)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.set_facecolor("#242424")
        for spine in self.ax.spines.values():
            spine.set_color("gray")
        legend = self.ax.legend(facecolor="#242424", labelcolor="white", loc="upper right")
        self.figure.tight_layout()
        self.canvas.draw()

    def _plot_shadow_curve(self, day, label, color):
        hours, shadows = [], []
        for minute in range(6 * 60, 18 * 60 + 1, 5):
            local_dt = datetime(day.year, day.month, day.day, tzinfo=solar.COLOMBIA_TZ) + timedelta(
                minutes=minute
            )
            elev = solar.solar_elevation(local_dt, self.lat, self.lon)
            length = solar.shadow_length(1.7, elev)
            hours.append(minute / 60)
            shadows.append(min(length, 5) if length is not None else None)

        self.ax.plot(hours, shadows, label=label, color=color, linewidth=2)

    def _abrir_simulador(self):
        if self.lat is None:
            return
        self.error_label.configure(text="")
        try:
            mapsim.open_globe_simulator(self.lat, self.lon, self.location_name, self.next_passage)
        except Exception as exc:
            self.error_label.configure(text=f"No se pudo abrir el simulador: {exc}")

    def _start_countdown(self):
        if self.countdown_job is not None:
            self.after_cancel(self.countdown_job)
        self._tick_countdown()

    def _tick_countdown(self):
        if self.next_passage is None:
            self.countdown_label.configure(text="No aplica")
            self.next_date_label.configure(text="")
            return

        local = self.next_passage.astimezone(solar.COLOMBIA_TZ)
        self.next_date_label.configure(text=f"{fechas.completa(local)} (hora Colombia)")

        ahora = datetime.now(solar.COLOMBIA_TZ)
        remaining = self.next_passage - ahora
        if remaining.total_seconds() <= -SEGUNDOS_AVISO_PASO:
            # Ya pasó hace rato: se busca el siguiente. Sin esto la cuenta se
            # quedaba clavada en "¡Es ahora!" hasta que el usuario volviera a
            # pulsar Calcular, y es justo el día del paso cuando la gente abre
            # la aplicación.
            self.next_passage = zenith.next_zenith_passage(self.lat, self.lon, ahora)
            self.countdown_job = self.after(1000, self._tick_countdown)
            return
        if remaining.total_seconds() <= 0:
            self.countdown_label.configure(text="¡Es ahora!")
        else:
            days = remaining.days
            hours, rem = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(rem, 60)
            self.countdown_label.configure(
                text=f"{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"
            )

        self.countdown_job = self.after(1000, self._tick_countdown)


if __name__ == "__main__":
    app = CenitApp()
    app.mainloop()
