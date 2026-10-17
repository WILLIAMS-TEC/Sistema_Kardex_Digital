"""
Sistema de Diseño UI/UX - Sistema Inventarios Kardex Digital.
Tokens de Diseño, Fuentes y Componentes del Command Center.

En este archivo centralizo todas las constantes de color, tipografía Segoe UI
y funciones auxiliares para generar tarjetas con estética Glassmorphism,
botones de alto contraste y pastillas de estado del sistema.
"""

import customtkinter as ctk

# Diccionario de tokens de diseño para mantener consistencia cromática en todo el software
THEME_TOKENS = {
    "bg": "#0B132B",             # Fondo azul noche slate profundo
    "card": "#1E293B",           # Superficie de tarjeta Slate 800
    "card_alt": "#27354A",       # Superficie secundaria / hover
    "dock": "#131F33",           # Barra superior de navegación flotante
    "border": "#334155",         # Bordes finos elegantes Slate 700
    "border_glow": "#3B82F6",    # Bordes interactivos azul zafiro
    "text": "#F8FAFC",           # Tipografía blanca nítida
    "muted": "#94A3B8",          # Tipografía secundaria gris azulada
    "dim": "#64748B",            # Texto atenuado para leyendas menores
    "blue": "#2563EB",           # Azul Zafiro Real primario para acciones destacadas
    "blue_hover": "#1D4ED8",
    "cyan": "#06B6D4",           # Cian Turquesa Digital para resaltar códigos e insignias
    "cyan_hover": "#0891B2",
    "mint": "#10B981",           # Verde Esmeralda para éxito, entradas de inventario y stock óptimo
    "mint_hover": "#059669",
    "amber": "#F59E0B",          # Ámbar Cálido para salidas y alertas preventivas de bajo stock
    "amber_hover": "#D97706",
    "amber_bg": "#451A03",
    "crimson": "#EF4444",        # Rojo Coral para alertas críticas y stock cero
    "crimson_hover": "#DC2626",
    "crimson_bg": "#4C0519",
    "teal": "#14B8A6",
    "purple": "#8B5CF6",         # Púrpura para auditoría y reportes ejecutivos
    "purple_hover": "#7C3AED",
}


def cmd_font(size=12, weight="normal", slant="roman"):
    """Aquí construyo una tipografía Segoe UI estilizada con el tamaño y peso solicitado."""
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight, slant=slant)


def glass_card(parent, **kwargs):
    """
    En esta función creo una tarjeta modular con bordes redondeados (corner_radius=14)
    y una línea de contorno sutil que le da el aspecto elegante de tarjeta flotante.
    """
    options = dict(
        fg_color=THEME_TOKENS["card"],
        corner_radius=14,
        border_width=1,
        border_color=THEME_TOKENS["border"]
    )
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)


def action_button(parent, text, command=None, accent="blue", **kwargs):
    """
    Aquí genero botones de acción con esquinas redondeadas y contraste cromático según su acento:
    - 'blue': Para botones primarios de guardado y navegación.
    - 'mint': Para transacciones de entrada de mercadería.
    - 'amber': Para despachos o salidas.
    - 'crimson': Para rechazar solicitudes o cerrar sesión.
    """
    if accent == "blue":
        fg = THEME_TOKENS["blue"]
        hover = THEME_TOKENS["blue_hover"]
        text_color = "#FFFFFF"
    elif accent == "cyan":
        fg = THEME_TOKENS["cyan"]
        hover = THEME_TOKENS["cyan_hover"]
        text_color = "#0B132B"
    elif accent == "mint":
        fg = THEME_TOKENS["mint"]
        hover = THEME_TOKENS["mint_hover"]
        text_color = "#FFFFFF"
    elif accent == "amber":
        fg = THEME_TOKENS["amber"]
        hover = THEME_TOKENS["amber_hover"]
        text_color = "#0B132B"
    elif accent == "crimson":
        fg = THEME_TOKENS["crimson"]
        hover = THEME_TOKENS["crimson_hover"]
        text_color = "#FFFFFF"
    elif accent == "purple":
        fg = THEME_TOKENS["purple"]
        hover = THEME_TOKENS["purple_hover"]
        text_color = "#FFFFFF"
    else:
        fg = THEME_TOKENS["card_alt"]
        hover = THEME_TOKENS["border_glow"]
        text_color = THEME_TOKENS["text"]

    options = dict(
        text=text,
        command=command,
        height=42,
        corner_radius=10,
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        font=cmd_font(12, "bold")
    )
    options.update(kwargs)
    return ctk.CTkButton(parent, **options)


class StatusPill(ctk.CTkFrame):
    """
    Aquí diseño una pastilla o insignia redondeada para mostrar el estado en vivo
    del sistema (ej. 'En Línea', 'Sesión Segura') en la barra superior.
    """
    def __init__(self, parent, label="EN LÍNEA", color=None, **kwargs):
        c = color or THEME_TOKENS["mint"]
        super().__init__(parent, fg_color=THEME_TOKENS["card"], corner_radius=12,
                         border_width=1, border_color=THEME_TOKENS["border"], **kwargs)
        # Punto luminoso indicador
        dot = ctk.CTkLabel(self, text="●", font=cmd_font(8, "bold"), text_color=c)
        dot.pack(side="left", padx=(10, 4), pady=4)
        # Texto del estado
        lbl = ctk.CTkLabel(self, text=label, font=cmd_font(9, "bold"), text_color=THEME_TOKENS["text"])
        lbl.pack(side="left", padx=(0, 10), pady=4)
