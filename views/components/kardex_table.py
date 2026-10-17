"""
Vista de Tabla de Inventario General y Semáforos de Stock.
Sistema Inventarios Kardex Digital.

En este componente programé la visualización paginada de existencias:
- Cálculo dinámico de semáforos de disponibilidad (Óptimo, Bajo, Agotado).
- Buscador predictivo en tiempo real por código SKU, producto o almacén.
- Filtros por bodega y por estado semafórico.
- Paginación interactiva (8 productos por página) y ordenamiento por columnas.
- Exportación directa del reporte oficial de existencias en formato PDF.
"""

import math
import customtkinter as ctk

from controllers.kardex_ctrl import obtener_inventario
from views.ui_theme import COLORS, HeroBanner, card, font, status_style


class InventarioView(ctk.CTkFrame):
    """
    Componente de tabla interactiva para consulta de inventario consolidado multi-bodega.
    """
    PAGE_SIZE = 8 # Número de registros visibles por página

    def __init__(self, parent, usuario=None, rol="CONSULTAS"):
        # Inicializo el contenedor principal transparente
        super().__init__(parent, fg_color="transparent")
        self.usuario = usuario
        self.rol = (rol or "CONSULTAS").upper()
        self.usuario_nombre = getattr(self.usuario, "NOMBRE_COMPLETO", "Usuario Consultas")
        
        # Configuro la cuadrícula expandible: fila 0 (banner), fila 1 (filtros), fila 2 (tabla)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Variables de control para paginación y ordenamiento
        self.current_page = 1
        self.sort_key = None
        self.sort_reverse = False
        
        # Cargo todos los registros desde la base de datos
        self.all_rows = self._load_rows()
        self.filtered_rows = list(self.all_rows)

        # Banner superior ilustrado con información del módulo
        HeroBanner(
            self, "Módulo de Existencias", "Tablero de Inventario y Semáforos",
            "Consulta el stock actual de productos con indicadores semafóricos de estado.\n"
            "Visualiza, busca, filtra y descarga el reporte oficial de existencias en PDF.",
            "Visibilidad total,\ncero descuadres.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))
        
        # Construyo los controles de filtrado y la estructura de la tabla
        self._build_filters()
        self._build_table()
        # Aplico los filtros iniciales para renderizar la primera página
        self._apply_filters()

    def _load_rows(self):
        """
        En este método traigo las existencias desde la base de datos
        y calculo para cada producto su estado semafórico (Óptimo, Bajo o Agotado).
        """
        try:
            source = obtener_inventario()
        except Exception:
            source = []
            
        # En caso de no tener conexión, utilizo productos tecnológicos de muestra
        if not source:
            source = [
                ("TEC-001", "Servidor Rack Dell PowerEdge R750", 2.0, "Bodega Central de Tecnología", 5.0),
                ("TEC-002", "Switch Administrable Cisco Catalyst 9300", 4.0, "Bodega Central de Tecnología", 2.0),
                ("TEC-003", "Laptop HP ProBook 450 G9 Core i7", 8.0, "Bodega Sucursal Norte", 15.0),
                ("TEC-004", "Monitor Gamer ASUS ROG Strix 27 Pulgadas", 10.0, "Bodega Sucursal Norte", 0.0),
            ]
            
        rows = []
        for item in source:
            values = tuple(item)
            if len(values) >= 6:
                code, product, _category, minimum, warehouse, current = values[:6]
            else:
                code, product, minimum, warehouse, current = values[:5]
                
            # Calculo el semáforo comparando stock actual contra stock mínimo
            state, color, bg = status_style(current, minimum)
            rows.append({
                "code": str(code),
                "product": str(product),
                "warehouse": str(warehouse),
                "minimum": float(minimum or 0),
                "current": float(current or 0),
                "state": state,
                "color": color,
                "state_bg": bg
            })
        return rows

    def _build_filters(self):
        """
        Aquí construyo la barra de filtros horizontal con buscador dinámico,
        selector de bodega, selector de estado semafórico y botón de exportación PDF.
        """
        filters = card(self, height=66)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        filters.grid_propagate(False)
        filters.grid_columnconfigure(0, weight=3) # Buscador
        filters.grid_columnconfigure(1, weight=2) # Bodega
        filters.grid_columnconfigure(2, weight=2) # Estado
        filters.grid_columnconfigure(3, weight=0) # Limpiar
        filters.grid_columnconfigure(4, weight=0) # Exportar PDF

        # Caja de búsqueda en vivo vinculada al evento KeyRelease
        self.search = ctk.CTkEntry(
            filters, placeholder_text="⌕   Buscar por código, producto o bodega...",
            height=42, corner_radius=8, fg_color=COLORS["field"],
            border_width=1, border_color=COLORS["border"],
            placeholder_text_color=COLORS["muted"], font=font(11)
        )
        self.search.grid(row=0, column=0, sticky="ew", padx=(14, 6), pady=12)
        self.search.bind("<KeyRelease>", lambda _e: self._apply_filters(reset=True))

        # Menú desplegable para filtrar por bodega específica
        warehouses = ["Todas las bodegas"] + sorted({r["warehouse"] for r in self.all_rows})
        self.warehouse_filter = ctk.CTkOptionMenu(
            filters, values=warehouses, height=42, corner_radius=8,
            fg_color=COLORS["field"], button_color=COLORS["field"],
            button_hover_color=COLORS["card_alt"], text_color=COLORS["text"],
            font=font(11), dropdown_font=font(11), command=lambda _v: self._apply_filters(reset=True))
        self.warehouse_filter.grid(row=0, column=1, sticky="ew", padx=6, pady=12)

        # Menú desplegable para filtrar por estado semafórico
        self.state_filter = ctk.CTkOptionMenu(
            filters, values=["Todos los estados", "Óptimo", "Bajo", "Agotado"],
            height=42, corner_radius=8, fg_color=COLORS["field"],
            button_color=COLORS["field"], button_hover_color=COLORS["card_alt"],
            text_color=COLORS["text"], font=font(11), dropdown_font=font(11),
            command=lambda _v: self._apply_filters(reset=True))
        self.state_filter.grid(row=0, column=2, sticky="ew", padx=6, pady=12)

        # Botón para restaurar todos los filtros
        ctk.CTkButton(
            filters, text="⟳  Limpiar", height=42, width=100,
            fg_color=COLORS["card_alt"], hover_color=COLORS["border"], border_width=1,
            border_color=COLORS["border"], corner_radius=8, font=font(10, "bold"),
            command=self.clear_filters
        ).grid(row=0, column=3, padx=6, pady=12)

        # Botón de alto contraste para generar y descargar el reporte oficial en PDF
        ctk.CTkButton(
            filters, text="📄   Descargar Existencias (PDF)", height=42, width=225,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"],
            corner_radius=8, font=font(11, "bold"),
            command=self.descargar_existencias
        ).grid(row=0, column=4, padx=(6, 14), pady=12)

    def _build_table(self):
        """
        Aquí construyo el armazón de la tabla:
        - Cabecera con columnas clickeables para ordenar alfabética o numéricamente.
        - Cuerpo scrollable donde se montan las filas de productos.
        - Pie de página con el contador y botones de paginación (Anterior / Siguiente).
        """
        self.table = card(self)
        self.table.grid(row=2, column=0, sticky="nsew")
        self.table.grid_rowconfigure(1, weight=1)
        self.table.grid_columnconfigure(0, weight=1)

        # Cabecera de la tabla con títulos y pesos proporcionales
        header = ctk.CTkFrame(self.table, fg_color=COLORS["header"], height=50, corner_radius=11)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        columns = (
            ("Código", "code", 13), ("Producto", "product", 22),
            ("Bodega", "warehouse", 18), ("Stock Mín.", "minimum", 11),
            ("Stock Actual", "current", 12), ("Estado", "state", 14),
            ("Acciones", None, 10)
        )
        for i, (label, key, weight) in enumerate(columns):
            header.grid_columnconfigure(i, weight=weight, uniform="table")
            command = (lambda k=key: self.sort_by(k)) if key else None
            ctk.CTkButton(
                header, text=f"{label}   ↕" if key else label, command=command,
                height=48, fg_color="transparent", hover_color=COLORS["card_alt"],
                text_color=COLORS["text"], font=font(10, "bold"),
                anchor="w" if i < 6 else "center"
            ).grid(row=0, column=i, sticky="ew", padx=5)

        # Contenedor deslizante para renderizar las filas de datos
        self.body = ctk.CTkScrollableFrame(
            self.table, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["border"]
        )
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)

        # Barra inferior de paginación
        footer = ctk.CTkFrame(self.table, height=64, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)
        
        self.count_label = ctk.CTkLabel(footer, text="", font=font(10), text_color=COLORS["muted"])
        self.count_label.grid(row=0, column=0, sticky="w", padx=20, pady=17)
        
        pager = ctk.CTkFrame(footer, fg_color="transparent")
        pager.grid(row=0, column=1, sticky="e", padx=18, pady=12)
        
        # Botón para ir a la página anterior
        self.prev_btn = ctk.CTkButton(
            pager, text="‹  Anterior", width=112, height=38,
            fg_color=COLORS["panel"], hover_color=COLORS["card_alt"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["muted"], command=lambda: self.change_page(-1)
        )
        self.prev_btn.pack(side="left", padx=4)
        
        # Indicador numérico de la página activa
        self.page_label = ctk.CTkLabel(
            pager, text="1", width=46, height=38, corner_radius=7,
            fg_color=COLORS["blue_dark"], font=font(11, "bold")
        )
        self.page_label.pack(side="left", padx=4)
        
        # Botón para ir a la página siguiente
        self.next_btn = ctk.CTkButton(
            pager, text="Siguiente  ›", width=112, height=38,
            fg_color=COLORS["panel"], hover_color=COLORS["card_alt"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["muted"], command=lambda: self.change_page(1)
        )
        self.next_btn.pack(side="left", padx=4)

    def _apply_filters(self, reset=False):
        """
        En este método filtro la lista de productos en memoria según lo escrito en el buscador,
        la bodega elegida y el estado semafórico, actualizando las filas visibles.
        """
        if reset:
            self.current_page = 1
        query = self.search.get().strip().casefold() if hasattr(self, "search") else ""
        warehouse = self.warehouse_filter.get() if hasattr(self, "warehouse_filter") else "Todas las bodegas"
        state = self.state_filter.get() if hasattr(self, "state_filter") else "Todos los estados"
        
        rows = []
        for row in self.all_rows:
            searchable = f"{row['code']} {row['product']} {row['warehouse']}".casefold()
            if query and query not in searchable:
                continue
            if warehouse != "Todas las bodegas" and row["warehouse"] != warehouse:
                continue
            if state != "Todos los estados" and row["state"] != state:
                continue
            rows.append(row)
        self.filtered_rows = rows
        self._render_rows()

    def _render_rows(self):
        """
        Aquí dibujo las filas correspondientes a la página activa actual:
        - Elimino las filas anteriores del frame.
        - Calculo el rango de índices según PAGE_SIZE.
        - Pinto cada celda con su insignia de semáforo y botón de detalle.
        """
        for widget in self.body.winfo_children():
            widget.destroy()
            
        pages = max(1, math.ceil(len(self.filtered_rows) / self.PAGE_SIZE))
        self.current_page = min(self.current_page, pages)
        start = (self.current_page - 1) * self.PAGE_SIZE
        visible = self.filtered_rows[start:start+self.PAGE_SIZE]
        
        for index, item in enumerate(visible):
            row = ctk.CTkFrame(self.body, fg_color="transparent", height=62)
            row.grid(row=index*2, column=0, sticky="ew")
            row.grid_propagate(False)
            for col, weight in enumerate((13, 22, 18, 11, 12, 14, 10)):
                row.grid_columnconfigure(col, weight=weight, uniform="table")

            # Columna 1: Código SKU con insignia cuadrada
            code_box = ctk.CTkFrame(row, fg_color="transparent")
            code_box.grid(row=0, column=0, sticky="w", padx=13)
            ctk.CTkLabel(code_box, text="▱", width=38, height=38, corner_radius=8,
                         fg_color="#15395C", text_color="#CDE2FF", font=font(17))\
                .pack(side="left", padx=(0, 10))
            ctk.CTkLabel(code_box, text=item["code"], font=font(10),
                         text_color=COLORS["text"]).pack(side="left")

            # Columna 2: Nombre o descripción del producto
            ctk.CTkLabel(row, text=item["product"], font=font(10), text_color=COLORS["text"],
                         anchor="w").grid(row=0, column=1, sticky="ew", padx=5)

            # Columna 3: Bodega asignada
            ctk.CTkLabel(row, text=item["warehouse"], font=font(10), text_color=COLORS["text"],
                         anchor="w").grid(row=0, column=2, sticky="ew", padx=5)

            # Columna 4: Stock Mínimo de alerta
            ctk.CTkLabel(row, text=f"{item['minimum']:.1f}", font=font(10),
                         text_color=COLORS["text"], anchor="w").grid(row=0, column=3, sticky="ew", padx=5)

            # Columna 5: Stock Físico Actual
            ctk.CTkLabel(row, text=f"{item['current']:.1f}", font=font(10),
                         text_color=COLORS["text"], anchor="w").grid(row=0, column=4, sticky="ew", padx=5)

            # Columna 6: Pastilla de semáforo con color de fondo suave y texto nítido
            ctk.CTkLabel(row, text=f"  ●   {item['state']}  ", height=36, corner_radius=8,
                         fg_color=item["state_bg"], text_color=item["color"], font=font(10))\
                .grid(row=0, column=5, sticky="ew", padx=5)

            # Columna 7: Botón de opciones para ver el expediente
            ctk.CTkButton(row, text="⋮", width=38, height=36, corner_radius=8,
                          fg_color=COLORS["field"], hover_color=COLORS["card_alt"],
                          border_width=1, border_color=COLORS["border"], font=font(18),
                          command=lambda data=item: self.show_actions(data))\
                .grid(row=0, column=6, padx=14)

            # Línea separadora sutil entre registros
            ctk.CTkFrame(self.body, height=1, fg_color=COLORS["border_soft"])\
                .grid(row=index*2+1, column=0, sticky="ew")

        # Si no hay resultados tras aplicar filtros, muestro mensaje explicativo
        if not visible:
            ctk.CTkLabel(self.body, text="No se encontraron productos que coincidan con los filtros aplicados.",
                         text_color=COLORS["muted"], font=font(12))\
                .grid(row=0, column=0, pady=80)
                
        # Actualizo el contador de productos y el estado de los botones de paginación
        self.count_label.configure(text=f"Mostrando {len(visible)} de {len(self.filtered_rows)} productos en catálogo")
        self.page_label.configure(text=str(self.current_page))
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < pages else "disabled")

    def sort_by(self, key):
        """En este método ordeno la lista filtrada por la columna seleccionada (ascendente o descendente)."""
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key, self.sort_reverse = key, False
        self.filtered_rows.sort(key=lambda item: item[key], reverse=self.sort_reverse)
        self.current_page = 1
        self._render_rows()

    def change_page(self, delta):
        """En este método cambio de página sumando o restando según el botón presionado."""
        pages = max(1, math.ceil(len(self.filtered_rows) / self.PAGE_SIZE))
        self.current_page = min(pages, max(1, self.current_page + delta))
        self._render_rows()

    def clear_filters(self):
        """Aquí limpio todos los campos de búsqueda y restablezco los filtros a su estado inicial."""
        self.search.delete(0, "end")
        self.warehouse_filter.set("Todas las bodegas")
        self.state_filter.set("Todos los estados")
        self._apply_filters(reset=True)

    def descargar_existencias(self):
        """
        Aquí invoco al motor de reportes en PDF (reportes_ctrl) para exportar el inventario oficial,
        respetando los filtros de bodega o estado actualmente seleccionados por el usuario.
        """
        from controllers.reportes_ctrl import exportar_pdf_existencias
        wh = self.warehouse_filter.get() if hasattr(self, "warehouse_filter") else "Todas las bodegas"
        st = self.state_filter.get() if hasattr(self, "state_filter") else "Todos los estados"
        exportar_pdf_existencias(
            usuario_nombre=self.usuario_nombre,
            rol_nombre=self.rol,
            filtro_bodega=wh if wh != "Todas las bodegas" else None,
            filtro_estado=st if st != "Todos los estados" else None
        )

    def show_actions(self, item):
        """Aquí despliego una ventana modal emergente con la ficha detallada del producto."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Ficha Técnica de Stock - {item['code']}")
        dialog.geometry("440x360")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["app"])

        box = card(dialog)
        box.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(box, text=item["product"], font=font(17, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(box, text=f"Código SKU: {item['code']}\nBodega: {item['warehouse']}\n"
                               f"Stock mínimo de seguridad: {item['minimum']:.1f}\nStock actual en Kardex: {item['current']:.1f}",
                     justify="left", font=font(12), text_color=COLORS["muted"])\
            .pack(anchor="w", padx=22, pady=10)

        # Semáforo en la ventana modal
        ctk.CTkLabel(box, text=f"  ●   {item['state']}  ", height=34, corner_radius=8,
                     fg_color=item["state_bg"], text_color=item["color"], font=font(11, "bold"))\
            .pack(anchor="w", padx=22, pady=4)
        
        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.pack(fill="x", padx=22, pady=(18, 14))
        
        # Botón para descargar el reporte oficial directamente desde el modal
        ctk.CTkButton(btn_row, text="📄  Descargar Reporte PDF", height=38, fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_dark"], font=font(10, "bold"),
                      command=lambda: (dialog.destroy(), self.descargar_existencias()))\
            .pack(side="left", fill="x", expand=True, padx=(0, 6))
            
        ctk.CTkButton(btn_row, text="Cerrar", width=90, height=38, fg_color=COLORS["field"],
                      hover_color=COLORS["card_alt"], command=dialog.destroy)\
            .pack(side="right")
