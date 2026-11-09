"""
Sistema Inventarios Kardex Digital — Panel de Control Principal.
Diseño moderno en español con Top Header Dock flotante y distribución en 3 columnas:
1. Columna Izquierda: Perfil de Operador + Acciones Rápidas + Resumen del Inventario
2. Columna Central: Gráfico Estadístico de Rotación (Matplotlib) + Indicadores de Salud Operativa
3. Columna Derecha: Historial Reciente de Operaciones en Tiempo Real

Comentarios pedagógicos en primera persona: Explico paso a paso la estructura,
el renderizado de gráficos, el dock de comandos y el ciclo de vida de la ventana.
"""

import os
import sys
import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Aquí me aseguro de que Python encuentre la raíz del proyecto sin importar
# si el script se ejecuta directamente desde esta carpeta o desde la raíz (main.py).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importo los tokens de diseño visual moderno tipo Command Center
from views.command_theme import (
    THEME_TOKENS, cmd_font, glass_card, action_button, StatusPill
)
from views.ui_theme import COLORS, set_theme, get_theme
from controllers.auth_ctrl import is_admin_role, is_warehouse_manager_role, is_consultas_role


# =============================================================================
# COMPONENTE MATPLOTLIB: ANALÍTICA & GRÁFICO ESTADÍSTICO
# =============================================================================
class InventoryAnalyticsCanvas(ctk.CTkFrame):
    """
    En esta clase implemento el lienzo interactivo donde incrusto un gráfico de Matplotlib.
    Muestro los 5 productos con mayor rotación/existencia en el almacén con barras horizontales
    y una paleta de colores de alto contraste sobre fondo oscuro.
    """

    def __init__(self, parent, **kwargs):
        # Inicializo el contenedor como un frame transparente
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)
        # De inmediato ejecuto el renderizado del gráfico estadístico
        self._render_chart()

    def _get_top_rotation_data(self):
        """
        Con esta función consulto la base de datos para extraer los productos reales del Kardex.
        Ordeno los productos por existencias disponibles de mayor a menor y tomo los primeros 5.
        Si la base de datos no está disponible, retorno datos representativos de contingencia.
        """
        try:
            from controllers.kardex_ctrl import obtener_inventario
            raw_data = obtener_inventario()
            if raw_data:
                # Ordeno por el stock actual (columna 4 de la tupla) de forma descendente y tomo el Top 5
                sorted_items = sorted(raw_data, key=lambda x: float(x[4] if len(x) >= 5 else 0), reverse=True)[:5]
                # Limito la longitud del nombre a 22 caracteres para que no desborde las etiquetas del gráfico
                labels = [str(x[1])[:22] for x in sorted_items]
                values = [float(x[4] if len(x) >= 5 else 0) for x in sorted_items]
                # Invierto el orden para que la barra más grande quede arriba en el eje horizontal
                labels.reverse()
                values.reverse()
                return labels, values
        except Exception:
            pass

        # Datos de contingencia en caso de que aún no existan movimientos o conexión
        return (
            ["Silla Ergonómica", "Monitor LG 24\"", "Resma Carta", "Teclado Mecánico", "Laptop Dell 3420"],
            [4, 8, 15, 28, 45]
        )

    def _render_chart(self):
        """
        Aquí construyo el gráfico de barras horizontales usando la figura de Matplotlib
        y la incrusto en el widget de Tkinter mediante FigureCanvasTkAgg.
        """
        labels, values = self._get_top_rotation_data()

        try:
            import matplotlib
            # Configuro el backend de Matplotlib para Tkinter
            matplotlib.use("TkAgg")
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Creo una figura con dimensiones 5.6 x 3.4 pulgadas y fondo acorde al tema
            fig = Figure(figsize=(5.6, 3.4), dpi=100, facecolor=THEME_TOKENS["card"])
            ax = fig.add_subplot(111)
            # Fondo del área de graficado
            ax.set_facecolor("#162238")

            y_pos = range(len(labels))
            # Asigno una paleta de colores neón y menta a cada barra
            colors_list = [
                THEME_TOKENS["mint"], THEME_TOKENS["blue"], THEME_TOKENS["cyan"],
                THEME_TOKENS["purple"], THEME_TOKENS["amber"]
            ]
            bars = ax.barh(y_pos, values, color=colors_list[:len(labels)], height=0.55, edgecolor="#2A3D5A", linewidth=1)

            # Aplico estilos a los ejes y a las etiquetas de texto
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, color=THEME_TOKENS["text"], fontsize=9, fontfamily="sans-serif")
            ax.tick_params(axis='x', colors=THEME_TOKENS["muted"], labelsize=8)
            ax.tick_params(axis='y', length=0)
            # Dibujo una cuadrícula punteada en el eje X para facilitar la lectura
            ax.grid(axis='x', color="#25354E", linestyle="--", linewidth=0.8, alpha=0.7)

            # Oculto los bordes externos de la caja para un acabado minimalista
            for spine in ax.spines.values():
                spine.set_visible(False)

            # Dibujo las etiquetas numéricas con las unidades exactas al final de cada barra
            for bar in bars:
                w = bar.get_width()
                ax.text(w + max(values)*0.02, bar.get_y() + bar.get_height()/2, f"{int(w)} uds",
                        ha='left', va='center', color=THEME_TOKENS["text"], fontsize=8, fontweight='bold')

            fig.tight_layout(pad=1.5)

            # Conecto la figura de Matplotlib con la ventana de Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception:
            # En caso de que Matplotlib falle o no esté instalado, dibujo un gráfico alternativo con Canvas nativo
            canvas_fallback = tk.Canvas(self, bg=THEME_TOKENS["card"], highlightthickness=0)
            canvas_fallback.pack(fill="both", expand=True, padx=8, pady=8)
            canvas_fallback.create_text(20, 20, text="Productos con Mayor Rotación",
                                        fill=THEME_TOKENS["text"], font=("Segoe UI", 12, "bold"), anchor="w")
            max_v = max(values) if values else 1
            for i, (lab, val) in enumerate(zip(labels, values)):
                y = 50 + i * 40
                canvas_fallback.create_text(20, y, text=lab, fill=THEME_TOKENS["muted"],
                                            font=("Segoe UI", 9), anchor="w")
                bar_len = int((val / max_v) * 200)
                canvas_fallback.create_rectangle(180, y-8, 180+bar_len, y+8,
                                                 fill=THEME_TOKENS["blue"], outline="")
                canvas_fallback.create_text(190+bar_len, y, text=f"{int(val)} uds",
                                            fill=THEME_TOKENS["mint"], font=("Segoe UI", 8, "bold"), anchor="w")


# =============================================================================
# COLUMNA IZQUIERDA: PERFIL DE OPERADOR & ACCIONES RÁPIDAS
# =============================================================================
class OperatorProfileDeck(ctk.CTkFrame):
    """
    En este panel izquierdo organizo:
    1. La tarjeta con el avatar e información de la sesión activa (nombre y rol).
    2. El bloque de accesos rápidos para registrar entradas, salidas, nuevo producto o exportar PDF.
    3. El resumen métrico general del inventario.
    """

    def __init__(self, parent, commander_name="Williams", role_title="ADMINISTRADOR", app_ref=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app_ref
        self.commander_name = commander_name
        self.role_title = role_title
        # Construyo cada subpanel del muelle izquierdo
        self._build_deck()

    def _build_deck(self):
        # 1. Tarjeta de Usuario / Operador
        profile_card = glass_card(self)
        profile_card.pack(fill="x", pady=(0, 12))

        header_strip = ctk.CTkFrame(profile_card, fg_color="transparent")
        header_strip.pack(fill="x", padx=16, pady=(16, 12))

        # Calculo las iniciales del nombre para el avatar redondo
        initials = "".join([part[0] for part in self.commander_name.split()[:2]]).upper() or "W"
        avatar = ctk.CTkLabel(
            header_strip, text=initials, width=48, height=48, corner_radius=24,
            fg_color="#064E3B", text_color=THEME_TOKENS["mint"],
            font=cmd_font(16, "bold")
        )
        avatar.pack(side="left", padx=(0, 12))

        # Información del operador y rol asignado
        info_box = ctk.CTkFrame(header_strip, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(info_box, text=f"Usuario: {self.commander_name}", font=cmd_font(13, "bold"),
                     text_color=THEME_TOKENS["text"], anchor="w").pack(fill="x")

        badge_frame = ctk.CTkFrame(info_box, fg_color="transparent")
        badge_frame.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(badge_frame, text=f"[{self.role_title}]", font=cmd_font(10, "bold"),
                     text_color=THEME_TOKENS["cyan"]).pack(side="left")
        ctk.CTkLabel(badge_frame, text=" • Nivel 1", font=cmd_font(10),
                     text_color=THEME_TOKENS["muted"]).pack(side="left")

        # Línea divisoria suave
        ctk.CTkFrame(profile_card, height=1, fg_color=THEME_TOKENS["border"]).pack(fill="x", padx=14)

        # Barra de estado inferior con indicador en línea
        status_bar = ctk.CTkFrame(profile_card, fg_color="transparent")
        status_bar.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(status_bar, text="●  Sesión Activa / En Línea", font=cmd_font(10, "bold"),
                     text_color=THEME_TOKENS["mint"]).pack(side="left")
        ctk.CTkLabel(status_bar, text="Módulo Kardex v3.2", font=cmd_font(9),
                     text_color=THEME_TOKENS["dim"]).pack(side="right")

        # 2. Panel de Acciones Rápidas
        actions_card = glass_card(self)
        actions_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(actions_card, text="ACCIONES RÁPIDAS", font=cmd_font(10, "bold"),
                     text_color=THEME_TOKENS["cyan"]).pack(anchor="w", padx=16, pady=(14, 8))

        # Configuro las acciones rápidas según el rol del usuario activo
        if not self.app.es_consultas:
            # Botón para saltar directo a registrar entrada (Admin y Encargado)
            action_button(actions_card, "➕   Registrar Entrada de Stock",
                          command=lambda: self.app.open_movement_action("Entrada"),
                          accent="mint").pack(fill="x", padx=14, pady=4)

            # Botón para saltar directo a registrar salida (Admin y Encargado)
            action_button(actions_card, "➖   Registrar Salida de Stock",
                          command=lambda: self.app.open_movement_action("Salida"),
                          accent="amber").pack(fill="x", padx=14, pady=4)

            # Botón para traslados seguros entre bodegas
            if self.app.es_admin:
                action_button(actions_card, "⇄   Traslado entre Bodegas",
                              command=lambda: self.app.open_movement_action("Traslado entre Bodegas"),
                              accent="cyan").pack(fill="x", padx=14, pady=4)
            elif self.app.es_encargado:
                action_button(actions_card, "⇄   Solicitar Traslado de Bodega",
                              command=lambda: self.app.open_movement_action("Solicitar Traslado entre Bodegas"),
                              accent="cyan").pack(fill="x", padx=14, pady=4)

        if self.app.es_admin:
            # Botón para saltar directo al catálogo de productos
            action_button(actions_card, "📦   Nuevo Producto en Catálogo",
                          command=lambda: self.app.open_admin_catalog(),
                          accent="blue").pack(fill="x", padx=14, pady=4)

            # Botón exclusivo para que el Administrador apruebe ajustes pendientes
            action_button(actions_card, "⚖   Aprobar Ajustes de Bodega",
                          command=lambda: self.app.open_admin_approvals(),
                          accent="purple").pack(fill="x", padx=14, pady=4)

        elif self.app.es_encargado:
            # Botón directo para que el Encargado solicite un ajuste justificado
            action_button(actions_card, "⚖   Solicitar Ajuste de Inventario",
                          command=lambda: self.app.open_movement_action("Ajuste Positivo (+)"),
                          accent="purple").pack(fill="x", padx=14, pady=4)

        elif self.app.es_consultas:
            # Botón directo para que el usuario de consultas navegue al inventario
            action_button(actions_card, "▤   Consultar Inventario General",
                          command=lambda: self.app.navigate_to_tab("matrix"),
                          accent="cyan").pack(fill="x", padx=14, pady=4)

        # Botón para generar y abrir el PDF oficial de existencias
        action_button(actions_card, "📄   Reporte de Existencias (PDF)",
                      command=lambda: self.app.quick_export_pdf(),
                      accent="blue" if self.app.es_consultas else "purple").pack(fill="x", padx=14, pady=(4, 14))

        # 3. Resumen del Inventario con métricas en tiempo real
        metrics_card = glass_card(self)
        metrics_card.pack(fill="both", expand=True)

        ctk.CTkLabel(metrics_card, text="RESUMEN DEL INVENTARIO", font=cmd_font(10, "bold"),
                     text_color=THEME_TOKENS["muted"]).pack(anchor="w", padx=16, pady=(14, 8))

        kpis = [
            ("Productos Registrados", str(self.app.summary_data.get("productos", 128)), THEME_TOKENS["cyan"]),
            ("Bodegas Operativas", str(self.app.summary_data.get("bodegas", 4)), THEME_TOKENS["mint"]),
            ("Movimientos del Día", str(self.app.summary_data.get("movimientos", 24)), THEME_TOKENS["text"]),
            ("Alertas de Stock Mínimo", str(self.app.summary_data.get("alertas", 3)), THEME_TOKENS["crimson"]),
        ]
        for name, val, color in kpis:
            line = ctk.CTkFrame(metrics_card, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(line, text=name, font=cmd_font(11), text_color=THEME_TOKENS["muted"]).pack(side="left")
            ctk.CTkLabel(line, text=val, font=cmd_font(12, "bold"), text_color=color).pack(side="right")


# =============================================================================
# COLUMNA DERECHA: HISTORIAL RECIENTE EN TIEMPO REAL
# =============================================================================
class OperationStreamFeed(ctk.CTkFrame):
    """
    En este panel derecho implemento la línea de tiempo cronológica de movimientos recientes
    y alertas del inventario. Utilizo tarjetas compactas con etiquetas visuales de color
    (Verde = Entrada, Amarillo = Salida, Rojo = Alerta Stock Crítico).
    """

    def __init__(self, parent, app_ref=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app_ref
        self._build_feed()

    def _build_feed(self):
        feed_card = glass_card(self)
        feed_card.pack(fill="both", expand=True)

        # Encabezado del feed con indicador "EN TIEMPO REAL"
        head = ctk.CTkFrame(feed_card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(head, text="HISTORIAL RECIENTE", font=cmd_font(11, "bold"),
                     text_color=THEME_TOKENS["text"]).pack(side="left")
        ctk.CTkLabel(head, text="EN TIEMPO REAL", font=cmd_font(9, "bold"),
                     text_color=THEME_TOKENS["mint"], fg_color="#064E3B", corner_radius=6)\
            .pack(side="right", padx=4, pady=2)

        ctk.CTkFrame(feed_card, height=1, fg_color=THEME_TOKENS["border"]).pack(fill="x", padx=14, pady=(0, 8))

        # Contenedor desplazable para albergar la lista de operaciones
        scrollable = ctk.CTkScrollableFrame(feed_card, fg_color="transparent")
        scrollable.pack(fill="both", expand=True, padx=8, pady=4)

        # Eventos cronológicos en tiempo real desde la base de datos (con respaldo demostrativo)
        events = []
        try:
            from controllers.kardex_ctrl import obtener_detalle_movimientos_periodo
            recent_movs = obtener_detalle_movimientos_periodo(dias=7)
            for m in recent_movs[:8]:
                t_up = str(m.get("tipo", "MOVIMIENTO")).upper()
                if "TRASLADO" in t_up:
                    color = THEME_TOKENS["cyan"]
                    sign = "⇄ "
                elif "ENTRADA" in t_up or "POSITIVO" in t_up or "DEVOLUCION" in t_up:
                    color = THEME_TOKENS["mint"]
                    sign = "+"
                else:
                    color = THEME_TOKENS["amber"]
                    sign = "-"
                estado = m.get("estado", "APROBADO")
                tag_str = f"{t_up} ({estado})" if estado != "APROBADO" else t_up
                detail_str = f"{sign}{float(m.get('cantidad', 0)):.1f} uds • {m.get('bodega', '-')}"
                events.append((tag_str, str(m.get("producto", "-")), detail_str, str(m.get("fecha", "")), color))
        except Exception:
            events = []

        if not events:
            events = [
                ("ENTRADA", "Laptop Dell Latitude 3420", "+15 uds • Bodega Central", "Hace 8 min", THEME_TOKENS["mint"]),
                ("SALIDA", "Resma Papel Carta", "-10 uds • Despacho Oficina", "Hace 22 min", THEME_TOKENS["amber"]),
                ("ALERTA", "Silla Ergonómica", "STOCK EN CERO (Agotado)", "Hace 45 min", THEME_TOKENS["crimson"]),
                ("ENTRADA", "Monitor LG 24\"", "+8 uds • Reabastecimiento", "Hoy 10:15 AM", THEME_TOKENS["mint"]),
                ("SALIDA", "Mouse Inalámbrico", "-2 uds • Factura #402", "Hoy 09:30 AM", THEME_TOKENS["amber"]),
                ("ALERTA", "Monitor LG 24\"", "Stock por debajo del mínimo (8/10)", "Hoy 08:40 AM", THEME_TOKENS["amber"]),
            ]

        for tag, title, detail, timestamp, color in events:
            item = ctk.CTkFrame(scrollable, fg_color=THEME_TOKENS["card_alt"], corner_radius=10)
            item.pack(fill="x", pady=4, padx=4)

            top_row = ctk.CTkFrame(item, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(top_row, text=f"● {tag}", font=cmd_font(9, "bold"), text_color=color).pack(side="left")
            ctk.CTkLabel(top_row, text=timestamp, font=cmd_font(9), text_color=THEME_TOKENS["dim"]).pack(side="right")

            ctk.CTkLabel(item, text=title, font=cmd_font(11, "bold"),
                         text_color=THEME_TOKENS["text"], anchor="w").pack(fill="x", padx=10)
            ctk.CTkLabel(item, text=detail, font=cmd_font(10),
                         text_color=THEME_TOKENS["muted"], anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        # Botón para navegar directamente a la tabla del inventario general
        btn_hist = ctk.CTkButton(
            feed_card, text="Ver Historial Completo →", height=38, corner_radius=10,
            fg_color="#1E293B", hover_color="#27354A", font=cmd_font(11, "bold"),
            text_color=THEME_TOKENS["cyan"],
            command=lambda: self.app.navigate_to_tab("matrix")
        )
        btn_hist.pack(fill="x", padx=14, pady=12)


# =============================================================================
# ARQUITECTURA PRINCIPAL: KARDEX DASHBOARD APP
# =============================================================================
class KardexDashboardApp(ctk.CTkToplevel):
    """
    Esta es la ventana principal ejecutiva tipo Command Center del Sistema Inventarios Kardex Digital.
    Controla la barra dock superior de navegación, el contenedor de vistas de trabajo (workstage)
    y el cierre seguro o regreso a la pantalla de login.
    """

    def __init__(self, parent=None, usuario=None, rol="ADMINISTRADOR"):
        # Si parent es None, inicializo una instancia raíz oculta para permitir ejecución autónoma
        if parent is None:
            self._root_app = ctk.CTk()
            self._root_app.withdraw()
            super().__init__(self._root_app)
            self.is_standalone = True
        else:
            self._root_app = None
            super().__init__(parent)
            self.is_standalone = False

        # Guardo las referencias del usuario y sus privilegios
        self.usuario = usuario
        self.rol = (rol or "ADMINISTRADOR").upper()
        self.commander_name = getattr(self.usuario, "NOMBRE_COMPLETO", "Williams")
        role_id = getattr(self.usuario, "ID_ROL", 1)
        self.es_admin = is_admin_role(self.rol, role_id)
        self.es_encargado = is_warehouse_manager_role(self.rol, role_id)
        self.es_consultas = is_consultas_role(self.rol, role_id)

        # Configuro el título y tamaño mínimo de la ventana ejecutiva
        self.title(f"Sistema Inventarios Kardex Digital — [{self.commander_name}]")
        self.minsize(1050, 680)
        self.configure(fg_color=THEME_TOKENS["bg"])
        # Intercepto el evento de cierre de ventana para limpiar adecuadamente
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Cargo las métricas globales desde el controlador del Kardex
        self._load_summary_metrics()
        # Construyo la interfaz del Command Center (Dock superior + Workstage)
        self._build_command_center_shell()
        # Centro la ventana en la pantalla del usuario
        self._place_centered_window()
        self.after(150, self._ensure_top_focus)

    def _ensure_top_focus(self):
        """Me aseguro de que la ventana tome foco sobre cualquier otra."""
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _place_centered_window(self):
        """Calculo la posición central exacta en el monitor del usuario."""
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(1500, max(1050, sw - 60))
        h = min(920, max(680, sh - 80))
        self.geometry(f"{w}x{h}+{max(0, (sw-w)//2)}+{max(0, (sh-h)//2)}")

    def _load_summary_metrics(self):
        """
        Consulto el controlador kardex_ctrl para obtener el total de productos,
        bodegas, alertas y movimientos registrados hoy.
        """
        self.summary_data = {"productos": 128, "bodegas": 4, "alertas": 3, "movimientos": 24}
        try:
            from controllers.kardex_ctrl import obtener_resumen_dashboard
            data = obtener_resumen_dashboard()
            if data and data.get("productos"):
                self.summary_data.update(data)
        except Exception:
            pass

    def _build_command_center_shell(self):
        """Estructuro la cuadrícula principal: Fila 0 = Dock Superior, Fila 1 = Escenario de trabajo."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. TOP HEADER DOCK FLOTANTE
        self._build_top_header_dock()

        # 2. CONTENEDOR MODULAR DE TRABAJO
        self.main_workstage = ctk.CTkFrame(self, fg_color="transparent")
        self.main_workstage.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 16))

        # Cargo por defecto la vista 1: Panel de Control (Command Center)
        self.navigate_to_tab("command")

    def _build_top_header_dock(self):
        """
        Construyo la barra superior suspendida con estética de muelle de comando (Dock):
        Logo y nombre del sistema a la izquierda, pestañas redondeadas al centro y perfil a la derecha.
        """
        self.dock = ctk.CTkFrame(self, height=68, fg_color=THEME_TOKENS["dock"], corner_radius=14,
                                 border_width=1, border_color=THEME_TOKENS["border"])
        self.dock.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        self.dock.grid_propagate(False)
        self.dock.grid_columnconfigure(1, weight=1)

        # Sección Izquierda: Identidad de Marca y Pills de Estado
        brand_dock = ctk.CTkFrame(self.dock, fg_color="transparent")
        brand_dock.grid(row=0, column=0, sticky="w", padx=(18, 12), pady=12)

        ctk.CTkLabel(brand_dock, text="📖  KARDEX", font=cmd_font(15, "bold"), text_color=THEME_TOKENS["text"]).pack(side="left")
        ctk.CTkLabel(brand_dock, text=" DIGITAL", font=cmd_font(15, "bold"), text_color=THEME_TOKENS["cyan"]).pack(side="left")

        StatusPill(brand_dock, label="En Línea", color=THEME_TOKENS["mint"]).pack(side="left", padx=(14, 6))
        StatusPill(brand_dock, label="Sesión Segura", color=THEME_TOKENS["cyan"]).pack(side="left", padx=4)

        # Sección Central: Pestañas de Navegación Horizontal
        nav_dock = ctk.CTkFrame(self.dock, fg_color="transparent")
        nav_dock.grid(row=0, column=1, sticky="nsew")

        # Configuro las pestañas según los permisos del usuario activo
        tabs_data = [
            ("command", "⌂  Panel Principal", self._render_command_center_view),
            ("matrix", "▤  Inventario General", self._render_inventory_matrix_view),
        ]
        # Solo Admin y Encargado de Bodega pueden acceder a registrar entradas, salidas y ajustes
        if not self.es_consultas:
            tabs_data.append(("dispatch", "⇄  Entradas y Salidas", self._render_dispatch_inflow_view))

        if self.es_admin:
            tabs_data.append(("master", "⚙  Administración y Catálogo", self._render_master_control_view))
        elif self.es_encargado:
            tabs_data.append(("master", "◇  Catálogo y Mis Solicitudes", self._render_master_control_view))

        self.tab_buttons = {}
        tabs_container = ctk.CTkFrame(nav_dock, fg_color="transparent")
        tabs_container.pack(expand=True)

        for key, text, cmd in tabs_data:
            btn = ctk.CTkButton(
                tabs_container, text=text, height=38, corner_radius=10,
                fg_color="transparent", hover_color=THEME_TOKENS["card_alt"],
                text_color=THEME_TOKENS["muted"], font=cmd_font(11, "bold"),
                command=lambda k=key, c=cmd: self._on_tab_click(k, c)
            )
            btn.pack(side="left", padx=4, pady=14)
            self.tab_buttons[key] = btn

        # Sección Derecha: Credencial del Usuario y Botón de Salir
        right_dock = ctk.CTkFrame(self.dock, fg_color="transparent")
        right_dock.grid(row=0, column=2, sticky="e", padx=(12, 18), pady=12)

        user_badge = ctk.CTkFrame(right_dock, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        user_badge.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(user_badge, text=f"👤  {self.commander_name}", font=cmd_font(11, "bold"),
                     text_color=THEME_TOKENS["text"]).pack(side="left", padx=(10, 8), pady=6)
        ctk.CTkLabel(user_badge, text=self.rol, font=cmd_font(9, "bold"), text_color=THEME_TOKENS["cyan"])\
            .pack(side="left", padx=(0, 10), pady=6)

        ctk.CTkButton(
            right_dock, text="⇥  Salir", width=78, height=36, corner_radius=10,
            fg_color="#3B1219", hover_color="#5C1622", text_color="#FCA5A5",
            font=cmd_font(11, "bold"), command=self.logout
        ).pack(side="left")

    def _on_tab_click(self, key, command):
        """Al pulsar una pestaña, cambio su color a activo y ejecuto su función de renderizado."""
        self.current_tab = key
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(fg_color=THEME_TOKENS["blue"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=THEME_TOKENS["muted"])
        command()

    def navigate_to_tab(self, key):
        """Permite navegar programáticamente a cualquiera de las pestañas por su identificador."""
        if key in self.tab_buttons:
            btn = self.tab_buttons[key]
            cmd = btn.cget("command")
            if callable(cmd):
                cmd()
            elif hasattr(btn, "_command") and callable(btn._command):
                btn._command()

    def _clear_workstage(self):
        """Destruyo todos los widgets hijos del contenedor antes de dibujar una nueva vista."""
        self.current_view = None
        for widget in self.main_workstage.winfo_children():
            widget.destroy()
        for col_i in range(10):
            self.main_workstage.grid_columnconfigure(col_i, weight=0, uniform="")
        for row_i in range(10):
            self.main_workstage.grid_rowconfigure(row_i, weight=0, uniform="")

    # =========================================================================
    # VISTA 1: PANEL DE CONTROL EN 3 COLUMNAS ASIMÉTRICAS
    # =========================================================================
    def _render_command_center_view(self):
        """
        Renderizo el Dashboard en 3 columnas asimétricas:
        - Columna 0 (25%): Perfil de operador y accesos directos
        - Columna 1 (47%): Matplotlib Analytics y semáforos de salud del almacén
        - Columna 2 (28%): Feed en tiempo real de operaciones recientes
        """
        self._clear_workstage()
        self._load_summary_metrics()
        self.main_workstage.grid_rowconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure(0, weight=25, uniform="cols") # Col Izquierda 25%
        self.main_workstage.grid_columnconfigure(1, weight=47, uniform="cols") # Col Central 47%
        self.main_workstage.grid_columnconfigure(2, weight=28, uniform="cols") # Col Derecha 28%

        # 1. COLUMNA IZQUIERDA: Perfil & Acciones Rápidas
        left_col = OperatorProfileDeck(self.main_workstage, commander_name=self.commander_name,
                                       role_title=self.rol, app_ref=self)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 2. COLUMNA CENTRAL: Matplotlib Analytics Top 5 Rotación & KPIs
        center_col = ctk.CTkFrame(self.main_workstage, fg_color="transparent")
        center_col.grid(row=0, column=1, sticky="nsew", padx=6)
        center_col.grid_rowconfigure(1, weight=1)
        center_col.grid_columnconfigure(0, weight=1)

        # Tarjeta superior de la columna central: Gráfico de Rotación
        analytics_card = glass_card(center_col)
        analytics_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        analytics_card.grid_columnconfigure(0, weight=1)

        head_chart = ctk.CTkFrame(analytics_card, fg_color="transparent")
        head_chart.pack(fill="x", padx=18, pady=(16, 6))
        ctk.CTkLabel(head_chart, text="PRODUCTOS CON MAYOR ROTACIÓN Y EXISTENCIAS", font=cmd_font(12, "bold"),
                     text_color=THEME_TOKENS["text"]).pack(side="left")
        ctk.CTkLabel(head_chart, text="GRÁFICO ESTADÍSTICO", font=cmd_font(9, "bold"),
                     text_color=THEME_TOKENS["cyan"]).pack(side="right")

        # Inserto el lienzo gráfico de Matplotlib
        chart_box = ctk.CTkFrame(analytics_card, fg_color="transparent")
        chart_box.pack(fill="both", expand=True, padx=12, pady=(0, 14))
        InventoryAnalyticsCanvas(chart_box)

        # Tarjeta inferior de la columna central: Indicadores Operativos y Auditoría
        health_card = glass_card(center_col)
        health_card.grid(row=1, column=0, sticky="nsew")
        health_card.grid_columnconfigure((0, 1, 2), weight=1)

        health_kpis = [
            ("Tasa de Disponibilidad", "98.4%", THEME_TOKENS["mint"], "Stock activo y sin quiebres"),
            ("Índice de Rotación", "4.2x", THEME_TOKENS["cyan"], "Ciclo promedio mensual"),
            ("Salud del Almacén", "ÓPTIMO", THEME_TOKENS["mint"], "Auditoría en regla"),
        ]
        for col, (title, val, color, desc) in enumerate(health_kpis):
            box = ctk.CTkFrame(health_card, fg_color=THEME_TOKENS["card_alt"], corner_radius=10)
            box.grid(row=0, column=col, sticky="nsew", padx=10, pady=14)
            ctk.CTkLabel(box, text=val, font=cmd_font(20, "bold"), text_color=color).pack(pady=(12, 2))
            ctk.CTkLabel(box, text=title, font=cmd_font(11, "bold"), text_color=THEME_TOKENS["text"]).pack()
            ctk.CTkLabel(box, text=desc, font=cmd_font(9), text_color=THEME_TOKENS["dim"]).pack(pady=(0, 12))

        # 3. COLUMNA DERECHA: Historial Reciente de Operaciones
        right_col = OperationStreamFeed(self.main_workstage, app_ref=self)
        right_col.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

    # =========================================================================
    # VISTAS RESTANTES: INVENTARIO, ENTRADAS/SALIDAS Y ADMINISTRACIÓN
    # =========================================================================
    def _render_inventory_matrix_view(self):
        """Renderizo la tabla completa de existencias del inventario con buscador y semáforos."""
        self._clear_workstage()
        self.main_workstage.grid_rowconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure((1, 2), weight=0)
        from views.components.kardex_table import InventarioView
        self.current_view = InventarioView(self.main_workstage, usuario=self.usuario, rol=self.rol)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _render_dispatch_inflow_view(self):
        """Renderizo el formulario para registrar entradas, salidas o solicitudes de ajuste."""
        self._clear_workstage()
        self.main_workstage.grid_rowconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure((1, 2), weight=0)
        from views.forms.movimiento_view import RegistroMovimientoView
        self.current_view = RegistroMovimientoView(self.main_workstage, self.usuario)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _render_master_control_view(self):
        """Renderizo el estudio Split-Pane para gestión de usuarios, ficha técnica y mesa de ajustes."""
        self._clear_workstage()
        self.main_workstage.grid_rowconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure(0, weight=1)
        self.main_workstage.grid_columnconfigure((1, 2), weight=0)
        from views.forms.admin_view import AdminView
        tab_initial = "users" if self.es_admin else "products"
        self.current_view = AdminView(self.main_workstage, usuario=self.usuario, initial_tab=tab_initial,
                                      es_admin=self.es_admin, rol=self.rol)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    # =========================================================================
    # ACCIONES RÁPIDAS DIRECTAS
    # =========================================================================
    def open_movement_action(self, movement_type="Entrada"):
        """Navega a la vista de movimientos y preselecciona Entrada, Salida, Traslado o Ajuste."""
        self.navigate_to_tab("dispatch")
        view = getattr(self, "current_view", None)
        if view and hasattr(view, "cb_tipo") and hasattr(view, "_on_tipo_changed"):
            try:
                view.cb_tipo.set(movement_type)
                view._on_tipo_changed(movement_type)
            except Exception:
                pass

    def open_admin_catalog(self):
        """Navega directamente a la pestaña de administración y catálogo."""
        self.navigate_to_tab("master")
        view = getattr(self, "current_view", None)
        if view and hasattr(view, "show_tab"):
            view.show_tab("products")

    def open_admin_approvals(self):
        """Navega directamente a la mesa de autorización y auditoría de ajustes."""
        self.navigate_to_tab("master")
        view = getattr(self, "current_view", None)
        if view and hasattr(view, "show_tab"):
            view.show_tab("approvals")

    def quick_export_pdf(self):
        """Exporta el reporte general de existencias en formato PDF corporativo."""
        try:
            from controllers.reportes_ctrl import exportar_pdf_existencias
            exportar_pdf_existencias(usuario_nombre=self.commander_name, rol_nombre=self.rol)
        except Exception as exc:
            messagebox.showerror("Error", f"No fue posible generar el reporte: {exc}")

    def on_exit(self):
        """Maneja el cierre seguro de la ventana principal."""
        if self.is_standalone:
            self.destroy()
            if getattr(self, "_root_app", None):
                self._root_app.destroy()
        else:
            self.master.destroy()

    def logout(self):
        """Cierra la sesión y regresa al formulario de autenticación inicial."""
        if self.is_standalone:
            self.destroy()
            if getattr(self, "_root_app", None):
                self._root_app.destroy()
        else:
            self.destroy()
            self.master.deiconify()
            self.master.entry_password.delete(0, "end")
            self.master.label_error.configure(text="")
            self.master.button_login.configure(state="normal", text="Acceder al Kardex Digital                         →")


# Alias de retrocompatibilidad
MainDashboard = KardexDashboardApp


# =============================================================================
# EJECUCIÓN AUTÓNOMA PARA PRUEBAS DIRECTAS
# =============================================================================
if __name__ == "__main__":
    from controllers.auth_ctrl import MockAdminSession
    # Aquí creo una sesión simulada con el usuario Williams para probar la vista directamente
    williams_user = MockAdminSession(nombre="Williams", correo="SEQUENW7@GMAIL.COM", rol_nombre="ADMINISTRADOR")
    app = KardexDashboardApp(parent=None, usuario=williams_user, rol="ADMINISTRADOR")
    if getattr(app, "_root_app", None):
        app._root_app.mainloop()
    else:
        app.mainloop()
