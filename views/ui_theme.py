"""
Sistema de Diseño y Paleta Visual para Sistema Inventarios Kardex Digital.
Diseño moderno en tonos Esmeralda / Obsidiana Cyber-Corporate y Gris Platino.

Comentarios pedagógicos en primera persona: Explico la selección de tokens de color,
el trazado vectorial en canvas para libros y cajas, y los componentes visuales interactivos.
"""

import tkinter as tk
import customtkinter as ctk


# ---------------------------------------------------------------------------
# PALETA OSCURA (Obsidian & Emerald Cyber-Corporate)
# ---------------------------------------------------------------------------
# En este diccionario defino los códigos hexadecimales para el tema oscuro.
# Utilizo tonos azul noche profundo para reducir el cansancio visual y acentos
# cian, verde esmeralda y ámbar para destacar estados críticos y llamadas a la acción.
DARK_COLORS = {
    "app": "#0B132B",          # Fondo principal azul noche / slate profundo
    "sidebar": "#101D35",      # Barra lateral azul noche estructurada
    "panel": "#14233C",        # Paneles contenedores
    "card": "#1E293B",         # Tarjetas de contenido (Slate 800)
    "card_alt": "#27354A",     # Tarjetas alternas / hover
    "field": "#111C2E",        # Campos de texto y entradas redondeadas
    "border": "#334155",       # Bordes elegantes Slate 700
    "border_soft": "#223147",  # Separadores sutiles
    "text": "#F8FAFC",         # Texto principal nítido blanco hielo
    "muted": "#94A3B8",        # Texto secundario legible Slate 400
    "muted_2": "#64748B",      # Texto atenuado
    "blue": "#2563EB",         # Acento Primario: Azul Zafiro Real
    "blue_dark": "#1D4ED8",    # Azul Intenso para estados hover y activos
    "cyan": "#06B6D4",         # Cian Turquesa Digital
    "green": "#10B981",        # Verde Esmeralda (Óptimo / Éxito)
    "mint": "#10B981",         # Menta esmeralda
    "green_bg": "#064E3B",     # Fondo suave verde
    "yellow": "#F59E0B",       # Ámbar Dorado (Advertencia / Bajo Stock)
    "amber": "#F59E0B",        # Ámbar
    "yellow_bg": "#451A03",    # Fondo suave amarillo/ámbar
    "red": "#EF4444",          # Rojo Coral (Alerta / Agotado)
    "red_bg": "#4C0519",       # Fondo suave rojo/carmesí
    "purple": "#8B5CF6",       # Púrpura Analítica / Auditoría
    "header": "#13223A",       # Barra de títulos y encabezados
}

# ---------------------------------------------------------------------------
# PALETA CLARA (Crisp Platinum & Emerald Corporate)
# ---------------------------------------------------------------------------
# En este diccionario defino la contraparte para el tema claro, manteniendo la misma
# semántica de variables para que el intercambio de tema sea instantáneo y sin romper estilos.
LIGHT_COLORS = {
    "app": "#F1F5F9",          # Fondo general slate claro
    "sidebar": "#E2E8F0",      # Barra lateral clara estructurada
    "panel": "#FFFFFF",        # Paneles blancos inmaculados
    "card": "#FFFFFF",         # Tarjetas blancas
    "card_alt": "#F8FAFC",     # Tarjetas hover
    "field": "#F1F5F9",        # Campos de entrada
    "border": "#CBD5E1",       # Bordes sutiles
    "border_soft": "#E2E8F0",  # Líneas de división
    "text": "#0F172A",         # Tipografía oscura nítida Slate 900
    "muted": "#475569",        # Texto secundario legible
    "muted_2": "#64748B",      # Texto accesorio
    "blue": "#2563EB",         # Azul Zafiro Corporativo
    "blue_dark": "#1D4ED8",    # Azul Profundo
    "cyan": "#0284C7",         # Azul Zafiro secundario
    "green": "#059669",        # Estado Óptimo
    "mint": "#059669",         # Menta esmeralda
    "green_bg": "#D1FAE5",     # Fondo suave verde
    "yellow": "#D97706",       # Estado Advertencia
    "amber": "#D97706",        # Ámbar
    "yellow_bg": "#FEF3C7",    # Fondo suave ámbar
    "red": "#DC2626",          # Estado Alerta
    "red_bg": "#FEE2E2",       # Fondo suave rojo
    "purple": "#7C3AED",       # Púrpura Analítica
    "header": "#E2E8F0",       # Encabezado
}

# Inicio con la paleta oscura por defecto
COLORS = dict(DARK_COLORS)
CURRENT_THEME = "Dark"

# Fuente del sistema
FONT = "Segoe UI"
FONT_DISPLAY = "Segoe UI"


def set_theme(mode):
    """
    Con esta función alterno entre el modo 'Dark' y 'Light'.
    Actualizo el diccionario global COLORS y la configuración de apariencia de CustomTkinter.
    """
    global CURRENT_THEME
    normalized = "Light" if str(mode).lower().startswith("light") else "Dark"
    CURRENT_THEME = normalized
    COLORS.clear()
    COLORS.update(LIGHT_COLORS if normalized == "Light" else DARK_COLORS)
    ctk.set_appearance_mode(normalized)
    return normalized


def get_theme():
    """Retorno el nombre del tema activo actualmente ('Dark' o 'Light')."""
    return CURRENT_THEME


def font(size=13, weight="normal", slant="roman"):
    """
    Función utilitaria para generar fuentes consistentes en toda la aplicación
    sin tener que repetir el nombre de la tipografía ni su escala.
    """
    return ctk.CTkFont(family=FONT, size=size, weight=weight, slant=slant)


def card(parent, **kwargs):
    """
    Constructor de tarjetas contenedoras con esquinas redondeadas y bordes sutiles.
    Permite encapsular widgets con un fondo diferenciado del lienzo principal.
    """
    defaults = dict(
        fg_color=COLORS["card"], corner_radius=12,
        border_width=1, border_color=COLORS["border"],
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def flat_button(parent, text, command=None, active=False, **kwargs):
    """
    Botón plano estilizado para menús o barras de navegación.
    Resalta con un borde cyan y color intenso cuando está marcado como activo.
    """
    defaults = dict(
        text=text, command=command, height=46, corner_radius=8,
        font=font(13, "bold" if active else "normal"), anchor="w",
        fg_color=COLORS["blue_dark"] if active else "transparent",
        hover_color=COLORS["card_alt"],
        text_color=COLORS["text"],
        border_width=1 if active else 0,
        border_color=COLORS["cyan"],
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


class BrandLogo(ctk.CTkFrame):
    """
    Emblema corporativo oficial para 'Sistema Inventarios Kardex Digital'.
    Dibuja un isotipo con el icono de un libro contable y la tipografía de marca.
    """

    def __init__(self, parent, compact=False, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        size = 44 if compact else 56

        # Insignia redondeada con acento azul y núcleo oscuro
        mark = ctk.CTkFrame(self, width=size, height=size, corner_radius=14,
                            fg_color=COLORS["blue"])
        mark.pack(side="left", padx=(0, 12))
        mark.pack_propagate(False)

        inner = ctk.CTkFrame(mark, width=int(size * .68), height=int(size * .68),
                             corner_radius=8, fg_color="#0F172A")
        inner.place(relx=.5, rely=.5, anchor="center")
        inner.pack_propagate(False)

        ctk.CTkLabel(inner, text="📖", font=font(18 if compact else 22),
                     text_color=COLORS["cyan"]).place(relx=.5, rely=.5, anchor="center")

        # Texto del logotipo: KARDEX en color principal y DIGITAL en cian
        text_box = ctk.CTkFrame(self, fg_color="transparent")
        text_box.pack(side="left")
        title = ctk.CTkFrame(text_box, fg_color="transparent")
        title.pack(anchor="w")
        ctk.CTkLabel(title, text="KARDEX", font=font(18 if compact else 25, "bold"),
                     text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(title, text=" DIGITAL", font=font(18 if compact else 25, "bold"),
                     text_color=COLORS["cyan"]).pack(side="left")
        ctk.CTkLabel(text_box, text="Sistema de Inventarios y Balances", font=font(10 if compact else 12),
                     text_color=COLORS["muted"]).pack(anchor="w")


class VectorIcon(tk.Canvas):
    """
    En esta clase implemento un motor de dibujo de iconos vectoriales matemáticos sobre un Canvas de Tkinter.
    Esto garantiza nitidez perfecta en cualquier resolución y evita que aparezcan caracteres rotos
    por falta de fuentes especiales en las computadoras donde se ejecute el sistema.
    """

    def __init__(self, parent, kind, size=28, bg=None, fg=None, command=None, **kwargs):
        self.size = size
        self.kind = kind
        self.fg = fg or COLORS["muted"]
        self.command = command
        super().__init__(parent, width=size, height=size, bg=bg or COLORS["panel"],
                         highlightthickness=0, bd=0, cursor="hand2" if command else "arrow", **kwargs)
        # Redibujo el icono cuando cambie de tamaño
        self.bind("<Configure>", self._draw)
        # Si se le asignó un comando, respondo al clic izquierdo del mouse
        if command:
            self.bind("<Button-1>", lambda _event: command())

    def _draw(self, _event=None):
        """Calculo las coordenadas matemáticas según el tipo de icono solicitado."""
        self.delete("all")
        s, c, w = self.size, self.fg, max(1, self.size // 14)
        if self.kind == "eye":
            # Icono de ojo para mostrar / ocultar contraseña
            self.create_arc(s*.14, s*.28, s*.86, s*.76, start=18, extent=144, style="arc", outline=c, width=w)
            self.create_arc(s*.14, s*.24, s*.86, s*.72, start=198, extent=144, style="arc", outline=c, width=w)
            self.create_oval(s*.42, s*.38, s*.58, s*.58, outline=c, width=w)
        elif self.kind == "user":
            # Icono de silueta de usuario
            self.create_oval(s*.36, s*.14, s*.64, s*.42, outline=c, width=w)
            self.create_arc(s*.20, s*.38, s*.80, s*.88, start=0, extent=180, style="arc", outline=c, width=w)
        elif self.kind == "lock":
            # Icono de candado de seguridad
            self.create_arc(s*.30, s*.12, s*.70, s*.55, start=0, extent=180, style="arc", outline=c, width=w)
            self.create_rectangle(s*.22, s*.38, s*.78, s*.82, outline=c, width=w)
            self.create_oval(s*.47, s*.55, s*.53, s*.61, fill=c, outline=c)
        elif self.kind == "calendar":
            # Icono de calendario de fecha
            self.create_rectangle(s*.18, s*.24, s*.82, s*.82, outline=c, width=w)
            self.create_line(s*.18, s*.39, s*.82, s*.39, fill=c, width=w)
            self.create_line(s*.34, s*.14, s*.34, s*.31, fill=c, width=w)
            self.create_line(s*.66, s*.14, s*.66, s*.31, fill=c, width=w)
        elif self.kind == "bell":
            # Icono de campana de alertas
            self.create_arc(s*.23, s*.20, s*.77, s*.73, start=0, extent=180, style="arc", outline=c, width=w)
            self.create_line(s*.23, s*.46, s*.18, s*.72, s*.82, s*.72, s*.77, s*.46, fill=c, width=w, smooth=True)
            self.create_arc(s*.40, s*.65, s*.60, s*.88, start=180, extent=180, style="arc", outline=c, width=w)
        elif self.kind == "box":
            # Icono de caja de mercadería / paquete
            self.create_polygon(s*.18, s*.32, s*.50, s*.14, s*.82, s*.32, s*.50, s*.50,
                                fill="", outline=c, width=w)
            self.create_polygon(s*.18, s*.32, s*.50, s*.50, s*.50, s*.86, s*.18, s*.67,
                                fill="", outline=c, width=w)
            self.create_polygon(s*.50, s*.50, s*.82, s*.32, s*.82, s*.67, s*.50, s*.86,
                                fill="", outline=c, width=w)
        elif self.kind == "users":
            # Icono de grupo de usuarios
            self.create_oval(s*.18, s*.18, s*.42, s*.42, outline=c, width=w)
            self.create_oval(s*.58, s*.18, s*.82, s*.42, outline=c, width=w)
            self.create_oval(s*.38, s*.10, s*.62, s*.36, outline=c, width=w)
            self.create_arc(s*.10, s*.37, s*.48, s*.80, start=0, extent=180, style="arc", outline=c, width=w)
            self.create_arc(s*.52, s*.37, s*.90, s*.80, start=0, extent=180, style="arc", outline=c, width=w)
            self.create_arc(s*.28, s*.30, s*.72, s*.82, start=0, extent=180, style="arc", outline=c, width=w)
        elif self.kind == "book":
            # Icono vectorial de libro contable Kardex
            self.create_polygon(s*.15, s*.20, s*.50, s*.28, s*.50, s*.85, s*.15, s*.77,
                                fill="", outline=c, width=w)
            self.create_polygon(s*.50, s*.28, s*.85, s*.20, s*.85, s*.77, s*.50, s*.85,
                                fill="", outline=c, width=w)
            self.create_line(s*.50, s*.28, s*.50, s*.85, fill=c, width=w+1)
        elif self.kind == "clipboard":
            # Icono de planilla o portapapeles de auditoría
            self.create_rectangle(s*.22, s*.22, s*.78, s*.88, outline=c, width=w)
            self.create_rectangle(s*.36, s*.14, s*.64, s*.26, fill=c, outline=c)
            self.create_line(s*.32, s*.42, s*.68, s*.42, fill=c, width=w)
            self.create_line(s*.32, s*.58, s*.68, s*.58, fill=c, width=w)
            self.create_line(s*.32, s*.74, s*.56, s*.74, fill=c, width=w)


class LibroKardexArt(tk.Canvas):
    """
    En este componente dibujo una ilustración vectorial refinada alusiva al Kardex:
    - Una base con una pila de libros contables cerrados.
    - Un libro mayor abierto en perspectiva con renglones de débitos y créditos en azul y verde.
    - Una cinta marcapáginas dorada.
    - Una caja de inventario suspendida a la derecha que simboliza el stock de mercancías.
    """

    def __init__(self, parent, bg=None, width=320, height=160, **kwargs):
        bg = bg or COLORS["panel"]
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, **kwargs)
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w * 0.5, h * 0.52

        # 1. Resplandor / Halo suave de fondo
        self.create_oval(cx - w*0.42, cy - h*0.38, cx + w*0.42, cy + h*0.38,
                         fill=COLORS["field"], outline="")

        # 2. Pila de libros inferiores que actúan como base del dibujo
        bx0, by0 = cx - w*0.34, cy + h*0.18
        bx1, by1 = cx + w*0.34, cy + h*0.36
        self.create_rectangle(bx0, by0, bx1, by1, fill=COLORS["blue_dark"], outline=COLORS["cyan"], width=1)
        self.create_rectangle(bx0 + 6, by0 + 4, bx1 - 6, by1 - 4, fill="#E2E8F0", outline="")
        self.create_line(bx0 + 10, by0 + 8, bx1 - 10, by0 + 8, fill="#94A3B8", width=1)
        self.create_line(bx0 + 10, by0 + 12, bx1 - 10, by0 + 12, fill="#CBD5E1", width=1)

        # 3. Libro mayor abierto (Kardex físico)
        ox0, oy0 = cx - w*0.30, cy - h*0.28
        ox1, oy1 = cx + w*0.30, cy + h*0.12
        spine_x = cx
        spine_top = oy0 + 8
        spine_bot = oy1

        # Tapas exteriores duras del libro
        self.create_polygon(ox0 - 4, oy0 + 6, spine_x, spine_top - 6,
                            spine_x, spine_bot + 4, ox0 - 4, oy1 + 4,
                            fill=COLORS["app"], outline=COLORS["blue"], width=2)
        self.create_polygon(spine_x, spine_top - 6, ox1 + 4, oy0 + 6,
                            ox1 + 4, oy1 + 4, spine_x, spine_bot + 4,
                            fill=COLORS["app"], outline=COLORS["blue"], width=2)

        # Página izquierda (Entradas de mercadería)
        self.create_polygon(ox0, oy0 + 8, spine_x, spine_top,
                            spine_x, spine_bot, ox0, oy1,
                            fill="#F8FAFC", outline="#CBD5E1", width=1)

        # Página derecha (Salidas y Saldos de inventario)
        self.create_polygon(spine_x, spine_top, ox1, oy0 + 8,
                            ox1, oy1, spine_x, spine_bot,
                            fill="#F1F5F9", outline="#CBD5E1", width=1)

        # Líneas de registro contable en página izquierda (Entradas en Azul)
        for i in range(5):
            ly = oy0 + 18 + i * ((oy1 - oy0 - 26) / 5)
            self.create_line(ox0 + 10, ly, spine_x - 10, ly - 2,
                             fill=COLORS["blue"] if i == 0 else "#94A3B8",
                             width=2 if i == 0 else 1)

        # Líneas de registro contable en página derecha (Saldos en Verde)
        for i in range(5):
            ly = oy0 + 18 + i * ((oy1 - oy0 - 26) / 5)
            self.create_line(spine_x + 10, ly - 2, ox1 - 10, ly,
                             fill=COLORS["green"] if i == 0 else "#94A3B8",
                             width=2 if i == 0 else 1)

        # Cinta de marcapáginas dorada que cuelga del lomo
        self.create_line(spine_x, spine_top, spine_x + 6, spine_bot + 16,
                          fill=COLORS["yellow"], width=3, capstyle=tk.ROUND)

        # 4. Caja de mercancía flotante a la derecha con acentos cian
        box_cx = ox1 + 4
        box_cy = oy0 - 2
        bs = min(w, h) * 0.12
        self.create_rectangle(box_cx - bs, box_cy - bs, box_cx + bs, box_cy + bs,
                              fill=COLORS["panel"], outline=COLORS["cyan"], width=2)
        self.create_line(box_cx - bs, box_cy, box_cx + bs, box_cy, fill=COLORS["cyan"], width=1)
        self.create_line(box_cx, box_cy - bs, box_cx, box_cy + bs, fill=COLORS["cyan"], width=1)


# Alias para mantener retrocompatibilidad con llamadas anteriores
CubeArt = LibroKardexArt


class HeroBanner(ctk.CTkFrame):
    """
    Banner de bienvenida institucional que combina títulos grandes, subtítulos explicativos,
    la ilustración del libro Kardex y un lema inspirador del control de inventarios.
    """

    def __init__(self, parent, eyebrow, title, lines, quote, **kwargs):
        super().__init__(parent, height=154, fg_color=COLORS["panel"], corner_radius=14,
                         border_width=1, border_color=COLORS["border"], **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Columna 0: Textos principales
        copy = ctk.CTkFrame(self, fg_color="transparent")
        copy.grid(row=0, column=0, sticky="nsew", padx=(22, 5), pady=16)
        ctk.CTkLabel(copy, text=eyebrow.upper(), font=font(10, "bold"),
                     text_color=COLORS["cyan"], anchor="w").pack(fill="x")
        ctk.CTkLabel(copy, text=title, font=font(26, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(copy, text=lines, font=font(12), justify="left",
                     text_color=COLORS["muted"], anchor="w").pack(fill="x")

        # Columna 1: Arte vectorial de libros
        art_holder = ctk.CTkFrame(self, fg_color="transparent")
        art_holder.grid(row=0, column=1, sticky="nsew")
        art = LibroKardexArt(art_holder, bg=COLORS["panel"], height=146)
        art.pack(fill="both", expand=True)

        # Columna 2: Cita corporativa y barra decorativa
        quote_box = ctk.CTkFrame(self, fg_color="transparent")
        quote_box.grid(row=0, column=2, sticky="nsew", padx=(0, 18), pady=32)
        ctk.CTkLabel(quote_box, text=quote, font=font(12, slant="italic"),
                     text_color=COLORS["text"], justify="left", anchor="w").pack(anchor="w")
        ctk.CTkFrame(quote_box, height=3, width=54, fg_color=COLORS["blue"],
                     corner_radius=2).pack(anchor="w", pady=(10, 0))


class SimpleDonut(tk.Canvas):
    """
    Gráfico de dona circular para visualizar la proporción de productos según su salud:
    - Verde: Stock Óptimo
    - Amarillo: Stock Bajo
    - Rojo: Agotado
    """

    def __init__(self, parent, values=(76, 17, 7), total=128, **kwargs):
        super().__init__(parent, bg=COLORS["card"], highlightthickness=0, **kwargs)
        self.values = values
        self.total = total
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        s = min(w, h) - 28
        x0, y0 = (w-s)/2, (h-s)/2
        start = 90
        # Dibujo los arcos proporcionales de cada segmento
        for value, color in zip(self.values, (COLORS["green"], COLORS["yellow"], COLORS["red"])):
            extent = -360 * value / max(1, sum(self.values))
            self.create_arc(x0, y0, x0+s, y0+s, start=start, extent=extent,
                            fill=color, outline=color)
            start += extent
        # Dibujo un círculo interior con el color de la tarjeta para formar el agujero de la dona
        inner = s * .62
        ix, iy = (w-inner)/2, (h-inner)/2
        self.create_oval(ix, iy, ix+inner, iy+inner, fill=COLORS["card"], outline=COLORS["card"])
        # Texto central con el total de productos
        self.create_text(w/2, h/2-8, text=str(self.total), fill=COLORS["text"],
                         font=(FONT, 22, "bold"))
        self.create_text(w/2, h/2+17, text="Productos", fill=COLORS["muted"],
                         font=(FONT, 10))


class BarChart(tk.Canvas):
    """
    Gráfico de barras agrupadas comparativo para ver entradas y salidas de los últimos 7 días.
    """

    def __init__(self, parent, data=None, **kwargs):
        super().__init__(parent, bg=COLORS["card"], highlightthickness=0, **kwargs)
        self.data = data
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        left, right, top, bottom = 38, w-10, 12, h-34
        
        if self.data and len(self.data) == 3:
            incoming, outgoing, labels = self.data
        else:
            incoming = (18, 27, 19, 27, 25, 29, 28)
            outgoing = (12, 18, 28, 21, 15, 21, 20)
            labels = ("21 May", "22 May", "23 May", "24 May", "25 May", "26 May", "27 May")
            
        max_val = max(max(incoming or [10]), max(outgoing or [10]), 10)
        import math
        top_scale = max(20, math.ceil(max_val / 10.0) * 10)

        # Dibujo las líneas horizontales de guía de la cuadrícula
        for i in range(5):
            y = bottom - (bottom-top)*i/4
            val_step = int(top_scale * i / 4)
            self.create_line(left, y, right, y, fill=COLORS["border_soft"])
            self.create_text(left-12, y, text=str(val_step), fill=COLORS["muted"], font=(FONT, 8))

        # Dibujo las barras verticales emparejadas (Entradas en Azul y Salidas en Cian)
        n_sections = max(1, len(labels))
        section = (right-left)/n_sections
        for i, (a, b) in enumerate(zip(incoming, outgoing)):
            x = left + i*section + section*.18
            scale = (bottom-top)/top_scale
            bar_w = section * .28
            self.create_rectangle(x, bottom-float(a)*scale, x+bar_w, bottom, fill=COLORS["blue"], outline="")
            self.create_rectangle(x+bar_w+2, bottom-float(b)*scale, x+bar_w*2+2, bottom, fill=COLORS["cyan"], outline="")
            lbl = labels[i] if i < len(labels) else ""
            self.create_text(left+(i+.5)*section, bottom+14, text=lbl, fill=COLORS["muted"], font=(FONT, 8))


def status_style(current, minimum):
    """
    Función semafórica que clasifica el stock actual frente al stock mínimo de seguridad:
    - Si el stock es <= 0: 'Agotado' con fondo rojo carmesí.
    - Si el stock es <= mínimo: 'Bajo' con fondo amarillo ámbar.
    - Si el stock supera el mínimo: 'Óptimo' con fondo verde esmeralda.
    """
    current = float(current or 0)
    minimum = float(minimum or 0)
    if current <= 0:
        return "Agotado", COLORS["red"], COLORS["red_bg"]
    if current <= minimum:
        return "Bajo", COLORS["yellow"], COLORS["yellow_bg"]
    return "Óptimo", COLORS["green"], COLORS["green_bg"]
