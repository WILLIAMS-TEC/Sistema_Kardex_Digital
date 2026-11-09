"""
Vista de Captura y Registro de Movimientos de Inventario y Traslados entre Bodegas.
Sistema Inventarios Kardex Digital.

En esta vista programé el formulario integral para registrar transacciones de inventario:
- Entradas de mercadería y compras directas a almacén.
- Despachos y salidas con validación matemática de existencia física y stock mínimo.
- Devoluciones de mercadería con trazabilidad.
- Traslados seguros entre bodegas (origen y destino) con control de reserva obligatoria.
- Envío de solicitudes de ajuste justificadas al Administrador para auditoría formal.
- Monitor en tiempo real de seguridad de stock: Existencia física, reserva mínima y cálculo de disponibilidad.

REGLAS DE SEGURIDAD Y CONDICIONES IMPLEMENTADAS:
1. Condición 1 (Stock Insuficiente): Si se solicitan 15 artículos y solo hay 10 en la bodega,
   la operación se bloquea inmediatamente porque no hay suficiente mercadería.
2. Condición 2 (Reserva de Stock Mínimo): Si se solicitan 12 artículos, hay 15 en bodega y el
   stock mínimo es 5, la operación se bloquea porque quedarían 3 artículos (15 - 12 = 3 < 5).
   Toda salida, ajuste negativo o traslado debe conservar al menos el stock mínimo configurado.
"""

import customtkinter as ctk

# Controladores de lógica transaccional y seguridad de inventario
from controllers.kardex_ctrl import (
    obtener_bodegas, obtener_productos, obtener_stock_producto,
    obtener_seguridad_stock, registrar_movimiento, obtener_motivos,
)
from controllers.auth_ctrl import (
    get_user_role, is_admin_role, is_warehouse_manager_role, is_consultas_role
)
from views.ui_theme import COLORS, HeroBanner, card, font


class RegistroMovimientoView(ctk.CTkScrollableFrame):
    """
    Clase principal del formulario de movimientos, traslados entre bodegas
    y solicitudes de ajuste de inventario con validación de seguridad de stock.
    """

    def __init__(self, parent, usuario):
        # Inicializo el frame deslizante principal con fondo transparente
        super().__init__(parent, fg_color="transparent", corner_radius=0,
                         scrollbar_button_color=COLORS["border"])
        self.usuario = usuario
        self.grid_columnconfigure(0, weight=1)

        # Determino el rol y nivel de privilegios del usuario activo
        self.rol_nombre = get_user_role(self.usuario)
        self.id_rol = getattr(self.usuario, "ID_ROL", 1)
        self.es_admin = is_admin_role(self.rol_nombre, self.id_rol)
        self.es_encargado = is_warehouse_manager_role(self.rol_nombre, self.id_rol)
        self.es_consultas = is_consultas_role(self.rol_nombre, self.id_rol)

        # Cargo los catálogos maestros desde la base de datos SQL Server
        self.bodegas_data = obtener_bodegas() or []
        self.productos_data = obtener_productos() or []
        self.motivos_data = obtener_motivos() or []

        # Banner superior ilustrado con mensaje de trazabilidad y gobernanza de stock
        HeroBanner(
            self, "Trazabilidad Logística", "Gestión de Movimientos, Traslados y Ajustes",
            "Registra entradas, salidas, traslados entre bodegas y solicitudes de ajuste con auditoría completa.\n"
            "Sistema de validación de Stock Mínimo: Garantiza que ninguna operación comprometa la reserva obligatoria.",
            "Operaciones seguras,\nexistencias protegidas.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Construyo la interfaz del formulario y el monitor lateral
        self._build_content()

    def _build_content(self):
        """
        Aquí divido la vista en dos columnas equilibradas:
        - Columna Izquierda (68%): Formulario para captura de datos del movimiento o traslado.
        - Columna Derecha (32%): Monitor de Seguridad de Stock y Simulación en Vivo de reservas.
        """
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=7) # Formulario
        content.grid_columnconfigure(1, weight=4) # Monitor de stock y reservas

        # ---------------- COLUMNA IZQUIERDA: Formulario de Operación ----------------
        form = card(content)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form.grid_columnconfigure((0, 1), weight=1)

        # Encabezado visual del formulario
        ctk.CTkLabel(form, text="⇄", font=font(28, "bold"), text_color=COLORS["cyan"])\
            .grid(row=0, column=0, sticky="w", padx=(24, 0), pady=(18, 0))
        title = ctk.CTkFrame(form, fg_color="transparent")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=68, pady=(16, 14))
        ctk.CTkLabel(title, text="Datos de la Operación Logística", font=font(16, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title, text="Selecciona la transacción y completa los campos requeridos con validación automática.",
                     font=font(10), text_color=COLORS["muted"]).pack(anchor="w")

        # Fila 1: Tipo de Movimiento y Bodega de Origen / Afectada
        if self.es_admin:
            tipos = [
                "Entrada",
                "Salida",
                "Devolución",
                "Traslado entre Bodegas",
                "Ajuste Positivo (+)",
                "Ajuste Negativo (-)"
            ]
        elif self.es_encargado:
            tipos = [
                "Entrada",
                "Salida",
                "Devolución",
                "Solicitar Traslado entre Bodegas",
                "Ajuste Positivo (+)",
                "Ajuste Negativo (-)"
            ]
        else:
            tipos = ["Entrada", "Salida", "Traslado entre Bodegas"]

        self.box_tipo, self.cb_tipo = self._field_option(
            form, 1, 0, "Tipo de Transacción", tipos, self._on_tipo_changed
        )

        bodegas_opts = [f"{b['id']} - {b['nombre']}" for b in self.bodegas_data] or ["1 - Bodega Central"]
        self.box_bodega, self.lbl_bodega_origen, self.cb_bodega = self._field_option_with_lbl(
            form, 1, 1, "Bodega Afectada / Origen", bodegas_opts, self.actualizar_stock
        )

        # Fila 2: Bodega de Destino (para traslados) y Documento de Referencia
        bodegas_dest_opts = [f"{b['id']} - {b['nombre']}" for b in self.bodegas_data] or ["2 - Bodega Sucursal"]
        self.box_bodega_destino, self.lbl_bodega_destino, self.cb_bodega_destino = self._field_option_with_lbl(
            form, 2, 0, "Bodega Destino (Solo Traslados)", bodegas_dest_opts, self._validar_en_vivo
        )
        if len(bodegas_dest_opts) > 1:
            self.cb_bodega_destino.set(bodegas_dest_opts[1])
        # Por defecto, la bodega destino inicia deshabilitada hasta que se elija Traslado
        self.cb_bodega_destino.configure(state="disabled")

        self.box_doc, self.entry_doc = self._field_entry(
            form, 2, 1, "Documento de Referencia", "Factura, guía de remisión o acta"
        )

        # Fila 3: Producto Tecnológico y Costo Unitario
        productos_opts = [f"{p['id']} - {p['codigo']} · {p['nombre']}" for p in self.productos_data] or ["1 - Sin productos"]
        self.box_producto, self.cb_producto = self._field_option(
            form, 3, 0, "Producto Tecnológico", productos_opts, self.actualizar_stock
        )

        self.box_costo, self.entry_costo = self._field_entry(
            form, 3, 1, "Costo Unitario (Q)", "0.00"
        )

        # Fila 4: Cantidad a Operar y Motivo de Excepción / Traslado
        self.box_cant, self.entry_cant = self._field_entry(
            form, 4, 0, "Cantidad a Operar *", "0"
        )
        # Conecto eventos de teclado para validar en tiempo real mientras el usuario escribe la cantidad
        self.entry_cant.bind("<KeyRelease>", self._validar_en_vivo)
        self.entry_cant.bind("<FocusOut>", self._validar_en_vivo)

        motivos_opts = ["Sin motivo especial"] + [f"{m['id']} - {m['descripcion']}" for m in self.motivos_data]
        self.box_motivo, self.cb_motivo = self._field_option(
            form, 4, 1, "Motivo de Excepción / Ajuste / Traslado", motivos_opts
        )

        # Fila 5: Justificación Detallada (Obligatoria para Ajustes y Traslados)
        lbl_obs_frame = ctk.CTkFrame(form, fg_color="transparent")
        lbl_obs_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=24, pady=(12, 4))
        self.lbl_observaciones = ctk.CTkLabel(
            lbl_obs_frame, text="Observaciones / Justificación Detallada (Auditoría)",
            font=font(10, "bold"), text_color=COLORS["text"], anchor="w"
        )
        self.lbl_observaciones.pack(side="left")
        self.lbl_obs_help = ctk.CTkLabel(
            lbl_obs_frame, text="• Obligatoria al solicitar ajustes o traslados",
            font=font(9), text_color=COLORS["muted"], anchor="w"
        )
        self.lbl_obs_help.pack(side="left", padx=8)

        # Fila 6: Caja de texto para justificación
        self.observaciones = ctk.CTkTextbox(
            form, height=65, corner_radius=8, fg_color=COLORS["field"],
            border_width=1, border_color=COLORS["border"], font=font(11)
        )
        self.observaciones.grid(row=6, column=0, columnspan=2, sticky="ew", padx=24)

        # Fila 7: Barra de retroalimentación de simulación en vivo y resultados
        feedback_frame = ctk.CTkFrame(form, fg_color="transparent")
        feedback_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=24, pady=(8, 2))
        feedback_frame.grid_columnconfigure(0, weight=1)

        self.lbl_simulacion = ctk.CTkLabel(
            feedback_frame, text="", height=20, font=font(10, "bold"), anchor="w"
        )
        self.lbl_simulacion.pack(fill="x")

        self.lbl_mensaje = ctk.CTkLabel(
            feedback_frame, text="", height=22, font=font(10), anchor="w"
        )
        self.lbl_mensaje.pack(fill="x")

        # Fila 8: Botones de Acción (Limpiar y Guardar/Enviar)
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=8, column=0, columnspan=2, sticky="ew", padx=24, pady=(8, 20))
        actions.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            actions, text="✕  Limpiar Formulario", width=140, height=42,
            fg_color=COLORS["field"], hover_color=COLORS["card_alt"],
            border_width=1, border_color=COLORS["border"], font=font(10, "bold"),
            command=self.limpiar
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))

        self.btn_guardar = ctk.CTkButton(
            actions, text="＋  Guardar Movimiento", width=240, height=42,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"],
            font=font(11, "bold"), command=self.guardar
        )
        self.btn_guardar.grid(row=0, column=1)

        # ---------------- COLUMNA DERECHA: Monitor de Seguridad de Stock ----------------
        side = card(content)
        side.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Encabezado del monitor lateral
        mon_head = ctk.CTkFrame(side, fg_color="transparent")
        mon_head.pack(fill="x", padx=18, pady=(18, 10))

        icon_box = ctk.CTkLabel(
            mon_head, text="🛡️", width=42, height=42, corner_radius=10,
            fg_color=COLORS["field"], font=font(20)
        )
        icon_box.pack(side="left", padx=(0, 10))

        mon_title_box = ctk.CTkFrame(mon_head, fg_color="transparent")
        mon_title_box.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(mon_title_box, text="Control de Seguridad", font=font(13, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(mon_title_box, text="Regla de Stock Mínimo & Reserva", font=font(9),
                     text_color=COLORS["cyan"], anchor="w").pack(fill="x")

        # Nombre del producto y bodega analizada actualmente
        item_card = ctk.CTkFrame(side, fg_color=COLORS["field"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
        item_card.pack(fill="x", padx=16, pady=(0, 12))

        self.lbl_prod_nombre = ctk.CTkLabel(
            item_card, text="--", font=font(11, "bold"),
            text_color=COLORS["text"], anchor="w", wraplength=260
        )
        self.lbl_prod_nombre.pack(fill="x", padx=12, pady=(10, 2))

        self.lbl_prod_codigo = ctk.CTkLabel(
            item_card, text="SKU: --", font=font(9),
            text_color=COLORS["cyan"], anchor="w"
        )
        self.lbl_prod_codigo.pack(fill="x", padx=12, pady=(0, 10))

        # Indicador principal de Stock Físico Actual
        stock_metric_card = ctk.CTkFrame(side, fg_color=COLORS["card_alt"], corner_radius=12,
                                         border_width=1, border_color=COLORS["border"])
        stock_metric_card.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(stock_metric_card, text="EXISTENCIA FÍSICA EN BODEGA", font=font(9, "bold"),
                     text_color=COLORS["muted"]).pack(pady=(12, 0))

        self.lbl_stock_actual = ctk.CTkLabel(
            stock_metric_card, text="0.0", font=font(34, "bold"),
            text_color=COLORS["green"]
        )
        self.lbl_stock_actual.pack(pady=(2, 0))

        self.lbl_bodega_tag = ctk.CTkLabel(
            stock_metric_card, text="unidades en bodega seleccionada", font=font(9),
            text_color=COLORS["muted"]
        )
        self.lbl_bodega_tag.pack(pady=(0, 8))

        # Badge de Salud del Inventario
        self.lbl_badge_salud = ctk.CTkLabel(
            stock_metric_card, text="✓ STOCK ÓPTIMO", height=24, corner_radius=6,
            fg_color=COLORS["green_bg"], text_color=COLORS["green"], font=font(9, "bold")
        )
        self.lbl_badge_salud.pack(pady=(0, 12), padx=20, fill="x")

        # Sub-métricas: Stock Mínimo y Disponible para Retiro
        metrics_grid = ctk.CTkFrame(side, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=16, pady=(0, 12))
        metrics_grid.grid_columnconfigure((0, 1), weight=1)

        # Caja 1: Stock Mínimo de Seguridad
        m1 = ctk.CTkFrame(metrics_grid, fg_color=COLORS["field"], corner_radius=8,
                          border_width=1, border_color=COLORS["border"])
        m1.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ctk.CTkLabel(m1, text="🛡️ Stock Mínimo", font=font(9, "bold"),
                     text_color=COLORS["amber"]).pack(pady=(8, 2))
        self.lbl_stock_minimo = ctk.CTkLabel(
            m1, text="0.0 uds", font=font(13, "bold"), text_color=COLORS["text"]
        )
        self.lbl_stock_minimo.pack(pady=(0, 8))

        # Caja 2: Máximo Disponible para Retirar/Trasladar
        m2 = ctk.CTkFrame(metrics_grid, fg_color=COLORS["field"], corner_radius=8,
                          border_width=1, border_color=COLORS["border"])
        m2.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        ctk.CTkLabel(m2, text="✓ Máx Retirable", font=font(9, "bold"),
                     text_color=COLORS["cyan"]).pack(pady=(8, 2))
        self.lbl_disponible_retiro = ctk.CTkLabel(
            m2, text="0.0 uds", font=font(13, "bold"), text_color=COLORS["text"]
        )
        self.lbl_disponible_retiro.pack(pady=(0, 8))

        # Tarjeta de Proyección / Simulación tras la operación
        proj_card = ctk.CTkFrame(side, fg_color=COLORS["field"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
        proj_card.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(proj_card, text="Simulación de Balance Resultante", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=12, pady=(10, 4))

        self.lbl_proyeccion = ctk.CTkLabel(
            proj_card, text="Ingresa una cantidad para simular el impacto en el Kardex.",
            font=font(10), text_color=COLORS["muted"], justify="left", wraplength=260, anchor="w"
        )
        self.lbl_proyeccion.pack(fill="x", padx=12, pady=(0, 10))

        # Cuadro explicativo de las reglas de control de stock
        rules_box = ctk.CTkFrame(side, fg_color="transparent")
        rules_box.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(rules_box, text="Condiciones de Control Activas:", font=font(9, "bold"),
                     text_color=COLORS["muted"], anchor="w").pack(fill="x")
        ctk.CTkLabel(
            rules_box,
            text=(
                "1. Condición 1: No se permite operar si la cantidad solicitada supera las existencias físicas.\n"
                "2. Condición 2: Ningún retiro, traslado o ajuste negativo puede reducir el stock por debajo del mínimo de reserva."
            ),
            font=font(8), text_color=COLORS["muted"], justify="left", wraplength=270, anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # Configuración inicial del formulario y consulta de stock
        self._on_tipo_changed(self.cb_tipo.get())
        self.actualizar_stock()

    def _field_option(self, parent, row, col, label, values, command=None):
        """Construyo una celda de formulario con menú desplegable redondeado."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=(24 if col == 0 else 10, 10 if col == 0 else 24), pady=6)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        control = ctk.CTkOptionMenu(
            box, values=values, height=40, corner_radius=8,
            fg_color=COLORS["field"], button_color=COLORS["field"],
            button_hover_color=COLORS["card_alt"],
            font=font(10), dropdown_font=font(10), command=command
        )
        control.pack(fill="x")
        return box, control

    def _field_option_with_lbl(self, parent, row, col, label, values, command=None):
        """Construyo una celda con etiqueta accesible para modificar dinámicamente su texto."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=(24 if col == 0 else 10, 10 if col == 0 else 24), pady=6)
        lbl = ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"])
        lbl.pack(anchor="w", pady=(0, 4))
        control = ctk.CTkOptionMenu(
            box, values=values, height=40, corner_radius=8,
            fg_color=COLORS["field"], button_color=COLORS["field"],
            button_hover_color=COLORS["card_alt"],
            font=font(10), dropdown_font=font(10), command=command
        )
        control.pack(fill="x")
        return box, lbl, control

    def _field_entry(self, parent, row, col, label, placeholder):
        """Construyo una celda de formulario con su campo de texto estilizado."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=(24 if col == 0 else 10, 10 if col == 0 else 24), pady=6)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        control = ctk.CTkEntry(
            box, placeholder_text=placeholder, height=40,
            fg_color=COLORS["field"], border_color=COLORS["border"],
            font=font(10)
        )
        control.pack(fill="x")
        return box, control

    def _selected_ids(self):
        """Extraigo los IDs numéricos de la bodega de origen y producto seleccionados."""
        warehouse = self.cb_bodega.get()
        product = self.cb_producto.get()
        if " - " not in warehouse or " - " not in product:
            return None, None
        try:
            return int(warehouse.split(" - ", 1)[0]), int(product.split(" - ", 1)[0])
        except ValueError:
            return None, None

    def _selected_dest_id(self):
        """Extraigo el ID numérico de la bodega de destino seleccionada (para traslados)."""
        warehouse_dest = self.cb_bodega_destino.get()
        if " - " not in warehouse_dest:
            return None
        try:
            return int(warehouse_dest.split(" - ", 1)[0])
        except ValueError:
            return None

    def _on_tipo_changed(self, choice):
        """
        En este método adapto la vista y los controles según la operación seleccionada:
        1. Traslado entre bodegas: Habilito el selector de bodega destino, renombro etiquetas y cambio color.
        2. Ajustes de inventario: Marco el botón en púrpura para indicar circuito de revisión/auditoría.
        3. Entradas, Salidas y Devoluciones: Ajusto textos y colores temáticos.
        """
        es_traslado = "Traslado" in choice

        if es_traslado:
            # Habilito bodega de destino y cambio etiquetas
            self.lbl_bodega_origen.configure(text="Bodega de Origen (Salida de Mercadería) ★")
            self.lbl_bodega_destino.configure(text="Bodega de Destino (Recepción) ★")
            self.cb_bodega_destino.configure(state="normal")
            origen_id, _ = self._selected_ids()
            dest_id = self._selected_dest_id()
            if origen_id is not None and dest_id == origen_id and len(self.bodegas_data) > 1:
                for b in self.bodegas_data:
                    if b["id"] != origen_id:
                        self.cb_bodega_destino.set(f"{b['id']} - {b['nombre']}")
                        break
            if self.es_admin:
                self.btn_guardar.configure(text="⇄  Ejecutar Traslado entre Bodegas", fg_color=COLORS["cyan"],
                                           hover_color="#0891B2")
            else:
                self.btn_guardar.configure(text="⇄  Solicitar Traslado entre Bodegas", fg_color=COLORS["purple"],
                                           hover_color="#7C3AED")
        else:
            # Deshabilito bodega de destino para operaciones convencionales
            self.lbl_bodega_destino.configure(text="Bodega Destino (Solo Traslados)")
            self.cb_bodega_destino.configure(state="disabled")

            if "Ajuste" in choice:
                self.lbl_bodega_origen.configure(text="Bodega Afectada por Ajuste")
                if self.es_admin:
                    self.btn_guardar.configure(text="⚖  Guardar Ajuste Directo", fg_color=COLORS["blue"],
                                               hover_color=COLORS["blue_dark"])
                else:
                    self.btn_guardar.configure(text="⚖  Enviar Solicitud de Ajuste", fg_color=COLORS["purple"],
                                               hover_color="#7C3AED")
            elif choice == "Salida":
                self.lbl_bodega_origen.configure(text="Bodega de Salida (Despacho)")
                self.btn_guardar.configure(text="－  Guardar Salida de Stock", fg_color=COLORS["amber"],
                                           hover_color="#D97706")
            elif choice == "Entrada":
                self.lbl_bodega_origen.configure(text="Bodega Receptora (Ingreso)")
                self.btn_guardar.configure(text="＋  Guardar Entrada de Stock", fg_color=COLORS["green"],
                                           hover_color="#059669")
            else: # Devolución
                self.lbl_bodega_origen.configure(text="Bodega Receptora (Devolución)")
                self.btn_guardar.configure(text="↺  Guardar Devolución", fg_color=COLORS["blue"],
                                           hover_color=COLORS["blue_dark"])

        # Refresco el cálculo de existencias y la validación en vivo
        self.actualizar_stock()
        self._validar_en_vivo()

    def actualizar_stock(self, _choice=None):
        """
        En este método consulto la tríada de seguridad de stock:
        - Stock físico actual en la bodega seleccionada.
        - Stock mínimo de seguridad establecido en el catálogo.
        - Cantidad máxima disponible para retirar o trasladar sin violar la reserva.
        """
        warehouse_id, product_id = self._selected_ids()
        if warehouse_id is None or product_id is None:
            self.lbl_stock_actual.configure(text="--", text_color=COLORS["muted"])
            self.lbl_stock_minimo.configure(text="--")
            self.lbl_disponible_retiro.configure(text="--")
            self.lbl_badge_salud.configure(text="SIN DATOS", fg_color=COLORS["field"], text_color=COLORS["muted"])
            return

        if "Traslado" in self.cb_tipo.get():
            dest_id = self._selected_dest_id()
            if dest_id == warehouse_id and len(self.bodegas_data) > 1:
                for b in self.bodegas_data:
                    if b["id"] != warehouse_id:
                        self.cb_bodega_destino.set(f"{b['id']} - {b['nombre']}")
                        break

        # Consulto la función de seguridad del controlador Kardex
        sec = obtener_seguridad_stock(product_id, warehouse_id)

        # Actualizo etiquetas de producto
        self.lbl_prod_nombre.configure(text=sec.get("producto_nombre") or "Producto Seleccionado")
        self.lbl_prod_codigo.configure(text=f"SKU: {sec.get('producto_codigo') or '--'}")

        # Actualizo métricas numéricas
        actual = sec["stock_actual"]
        minimo = sec["stock_minimo"]
        disp = sec["disponible_retiro"]

        self.lbl_stock_actual.configure(
            text=f"{actual:.1f}",
            text_color=COLORS["red"] if actual <= 0 else (COLORS["amber"] if actual <= minimo else COLORS["green"])
        )
        self.lbl_stock_minimo.configure(text=f"{minimo:.1f} uds")
        self.lbl_disponible_retiro.configure(text=f"{disp:.1f} uds")

        # Insignia de salud del inventario
        estado = sec.get("estado", "OPTIMO")
        if estado == "OPTIMO":
            self.lbl_badge_salud.configure(
                text="✓ STOCK SALUDABLE (ÓPTIMO)",
                fg_color=COLORS["green_bg"], text_color=COLORS["green"]
            )
        elif estado == "MINIMO":
            self.lbl_badge_salud.configure(
                text="⚠ EN RESERVA MÍNIMA",
                fg_color=COLORS["yellow_bg"], text_color=COLORS["amber"]
            )
        else:
            self.lbl_badge_salud.configure(
                text="🚨 DÉFICIT CRÍTICO",
                fg_color=COLORS["red_bg"], text_color=COLORS["red"]
            )

        # Ejecuto la simulación en vivo con el valor actual ingresado en la cantidad
        self._validar_en_vivo()

    def _validar_en_vivo(self, _event=None):
        """
        En este método evalúo matemáticamente la transacción en tiempo real mientras el usuario escribe:
        - Condición 1: ¿La cantidad solicitada supera las existencias físicas? (Bloqueo por falta de stock).
        - Condición 2: ¿El saldo resultante es menor al stock mínimo de reserva? (Bloqueo por reserva de stock).
        """
        warehouse_id, product_id = self._selected_ids()
        if warehouse_id is None or product_id is None:
            self.lbl_simulacion.configure(text="")
            self.lbl_proyeccion.configure(text="Selecciona una bodega y un producto para simular.", text_color=COLORS["muted"])
            return

        cant_str = self.entry_cant.get().strip()
        if not cant_str:
            self.lbl_simulacion.configure(text="")
            self.lbl_proyeccion.configure(
                text="Ingresa una cantidad numérica para proyectar el saldo resultante.",
                text_color=COLORS["muted"]
            )
            return

        try:
            cantidad = float(cant_str)
            if cantidad <= 0:
                self.lbl_simulacion.configure(text="⚠ La cantidad debe ser mayor a 0", text_color=COLORS["amber"])
                self.lbl_proyeccion.configure(text="La cantidad debe ser estrictamente mayor a 0.", text_color=COLORS["amber"])
                return
        except ValueError:
            self.lbl_simulacion.configure(text="⚠ Cantidad inválida (debe ser número)", text_color=COLORS["red"])
            self.lbl_proyeccion.configure(text="Ingresa un valor numérico válido (ej. 5 o 10.5).", text_color=COLORS["red"])
            return

        sec = obtener_seguridad_stock(product_id, warehouse_id)
        stock_actual = sec["stock_actual"]
        stock_minimo = sec["stock_minimo"]
        disp_retiro = sec["disponible_retiro"]

        tipo = self.cb_tipo.get()
        resta_stock = ("Salida" in tipo or "Negativo" in tipo or "Traslado" in tipo)

        # ---------------- CASO A: OPERACIÓN QUE RESTA EXISTENCIAS ----------------
        if resta_stock:
            saldo_proyectado = stock_actual - cantidad

            # Validación de traslados: Bodega origen y destino no pueden coincidir
            if "Traslado" in tipo:
                dest_id = self._selected_dest_id()
                if dest_id and dest_id == warehouse_id:
                    msg_err = "⚠ La bodega de origen y la bodega de destino no pueden ser la misma."
                    self.lbl_simulacion.configure(text=msg_err, text_color=COLORS["red"])
                    self.lbl_proyeccion.configure(text=msg_err, text_color=COLORS["red"])
                    return

            # CONDICIÓN 1: Stock Físico Insuficiente
            if cantidad > stock_actual:
                msg_c1 = (
                    f"🚨 CONDICIÓN 1 BLOQUEADA: Stock insuficiente.\n"
                    f"Solo hay {stock_actual:.1f} uds disponibles y estás solicitando {cantidad:.1f} uds."
                )
                self.lbl_simulacion.configure(
                    text=f"🚨 Bloqueo: Stock insuficiente ({stock_actual:.1f} uds disponibles)",
                    text_color=COLORS["red"]
                )
                self.lbl_proyeccion.configure(text=msg_c1, text_color=COLORS["red"])
                return

            # CONDICIÓN 2: Violación de Reserva de Stock Mínimo
            if saldo_proyectado < stock_minimo:
                msg_c2 = (
                    f"⚠ CONDICIÓN 2 BLOQUEADA: Violación de Stock Mínimo.\n"
                    f"La bodega debe conservar al menos {stock_minimo:.1f} uds de reserva.\n"
                    f"Al retirar {cantidad:.1f} uds quedarían {saldo_proyectado:.1f} uds.\n"
                    f"Máximo permitido para retirar/trasladar: {disp_retiro:.1f} uds."
                )
                self.lbl_simulacion.configure(
                    text=f"⚠ Bloqueo: Quedarían {saldo_proyectado:.1f} uds (mínimo obligatorio: {stock_minimo:.1f} uds)",
                    text_color=COLORS["amber"]
                )
                self.lbl_proyeccion.configure(text=msg_c2, text_color=COLORS["amber"])
                return

            # Operación aprobable y segura
            self.lbl_simulacion.configure(
                text=f"✓ Operación válida: Quedarán {saldo_proyectado:.1f} uds (reserva de {stock_minimo:.1f} uds protegida)",
                text_color=COLORS["green"]
            )
            if "Traslado" in tipo:
                dest_id = self._selected_dest_id()
                sec_dest = obtener_seguridad_stock(product_id, dest_id) if dest_id else {"stock_actual": 0.0}
                stock_dest = sec_dest.get("stock_actual", 0.0)
                saldo_dest = stock_dest + cantidad
                msg_ok = (
                    f"✓ Traslado seguro entre bodegas:\n"
                    f"• Origen: {stock_actual:.1f} ➔ {saldo_proyectado:.1f} uds (reserva de {stock_minimo:.1f} uds protegida).\n"
                    f"• Destino: {stock_dest:.1f} ➔ {saldo_dest:.1f} uds."
                )
            else:
                msg_ok = (
                    f"✓ Transacción segura:\n"
                    f"El stock en bodega pasará de {stock_actual:.1f} ➔ {saldo_proyectado:.1f} uds.\n"
                    f"La reserva obligatoria ({stock_minimo:.1f} uds) queda 100% protegida."
                )
            self.lbl_proyeccion.configure(text=msg_ok, text_color=COLORS["green"])

        # ---------------- CASO B: OPERACIÓN QUE SUMA EXISTENCIAS ----------------
        else:
            saldo_proyectado = stock_actual + cantidad
            self.lbl_simulacion.configure(
                text=f"✓ Operación válida: El stock aumentará a {saldo_proyectado:.1f} uds",
                text_color=COLORS["green"]
            )
            msg_ok = (
                f"✓ Ingreso de inventario:\n"
                f"El stock en la bodega aumentará de {stock_actual:.1f} ➔ {saldo_proyectado:.1f} uds."
            )
            self.lbl_proyeccion.configure(text=msg_ok, text_color=COLORS["green"])

    def guardar(self):
        """
        Aquí proceso el guardado y ejecución de la transacción con validaciones estrictas:
        1. Verifico la selección de bodega(s) y producto.
        2. Convierto y valido la cantidad numérica y el costo unitario.
        3. Compruebo las dos condiciones de seguridad (Stock insuficiente y Stock mínimo).
        4. Verifico permisos de rol y obligatoriedad de justificación para ajustes y traslados.
        5. Llamo al controlador kardex_ctrl.registrar_movimiento para ejecución atómica en SQL Server.
        """
        warehouse_id, product_id = self._selected_ids()
        if warehouse_id is None or product_id is None:
            self._message("Debes seleccionar una bodega y un producto válidos.", False)
            return

        # Valido la cantidad numérica
        try:
            quantity = float(self.entry_cant.get().strip())
            cost = float(self.entry_costo.get().strip() or 0.0)
            if quantity <= 0 or cost < 0:
                raise ValueError
        except ValueError:
            self._message("La cantidad debe ser mayor a 0 y el costo un número no negativo.", False)
            return

        kind = self.cb_tipo.get()
        type_id_map = {
            "Entrada": 1,
            "Salida": 2,
            "Devolución": 3,
            "Ajuste Positivo (+)": 4,
            "Ajuste Negativo (-)": 5,
            "Traslado entre Bodegas": 6,
            "Solicitar Traslado entre Bodegas": 6,
        }
        type_id = type_id_map.get(kind, 1)
        es_traslado = (type_id == 6)

        # Configuro bodega origen y destino según el tipo de movimiento
        if es_traslado:
            dest_id = self._selected_dest_id()
            if not dest_id:
                self._message("Para un traslado entre bodegas debes seleccionar la Bodega de Destino.", False)
                return
            if dest_id == warehouse_id:
                self._message("La bodega de origen y la bodega de destino no pueden ser la misma.", False)
                return
            origin = warehouse_id
            destination = dest_id
        elif kind == "Salida" or "Negativo" in kind:
            origin = warehouse_id
            destination = None
        else:
            origin = None
            destination = warehouse_id

        # ---------------- VERIFICACIÓN PREVIA DE SEGURIDAD DE STOCK ----------------
        # Si la operación retira mercadería de la bodega de origen (Salida, Traslado o Ajuste Negativo)
        if type_id in (2, 5, 6):
            sec = obtener_seguridad_stock(product_id, origin)
            stock_actual = sec["stock_actual"]
            stock_minimo = sec["stock_minimo"]
            disp_retiro = sec["disponible_retiro"]

            # CONDICIÓN 1: Stock Insuficiente
            if quantity > stock_actual:
                self._message(
                    f"Operación bloqueada (Condición 1): Stock insuficiente. Hay {stock_actual:.1f} unidades disponibles y solicitas {quantity:.1f}.",
                    False
                )
                return

            # CONDICIÓN 2: Violación de Reserva de Stock Mínimo
            saldo_restante = stock_actual - quantity
            if saldo_restante < stock_minimo:
                self._message(
                    f"Operación bloqueada (Condición 2): Violación de Stock Mínimo. "
                    f"Debes conservar al menos {stock_minimo:.1f} unidades de reserva. "
                    f"Con {quantity:.1f} unidades solicitadas quedarían {saldo_restante:.1f}. "
                    f"Máximo permitido a retirar/trasladar: {disp_retiro:.1f} unidades.",
                    False
                )
                return

        # Valido permisos de usuario: El rol Consultas no puede realizar movimientos
        user_id = getattr(self.usuario, "ID_USUARIO", None)
        if user_id is None:
            self._message("No se pudo identificar al usuario de la sesión activa.", False)
            return

        if self.es_consultas:
            self._message("Tu perfil de usuario (Consultas) es de solo lectura y no puede registrar operaciones.", False)
            return

        # Parseo el ID del motivo de excepción
        motivo_str = self.cb_motivo.get()
        motivo_id = None
        if " - " in motivo_str:
            try:
                motivo_id = int(motivo_str.split(" - ", 1)[0])
            except ValueError:
                motivo_id = None

        # REGLA DE AUDITORÍA: Para Ajustes y Traslados de Encargado, la justificación es obligatoria
        justificacion = self.observaciones.get("1.0", "end").strip()
        if "Ajuste" in kind:
            if not motivo_id:
                self._message("Para solicitar un ajuste de inventario debes seleccionar un Motivo de Excepción específico.", False)
                return
            if len(justificacion) < 10:
                self._message("Es obligatoria la justificación detallada del porqué solicitas el ajuste (mínimo 10 caracteres).", False)
                return

        if es_traslado and not self.es_admin:
            if len(justificacion) < 10:
                self._message("Para solicitar un traslado entre bodegas debes escribir la justificación operativa (mínimo 10 caracteres).", False)
                return

        # Deshabilito temporalmente el botón para prevenir envíos dobles accidentales
        texto_original = self.btn_guardar.cget("text")
        self.btn_guardar.configure(state="disabled", text="Procesando transacción...")
        self.update_idletasks()

        # Ejecuto la transacción en la base de datos SQL Server
        doc_ref = self.entry_doc.get().strip() or ("TRASLADO-INTERNO" if es_traslado else "S/D")
        success, message = registrar_movimiento(
            usuario_id=user_id,
            tipo_movimiento_id=type_id,
            bodega_origen_id=origin,
            bodega_destino_id=destination,
            doc_referencia=doc_ref,
            detalles_productos=[{"id_producto": product_id, "cantidad": quantity, "costo_unitario": cost}],
            motivo_id=motivo_id,
            observaciones=justificacion,
        )

        # Restauro el botón
        self.btn_guardar.configure(state="normal", text=texto_original)
        self._message(message, success)

        if success:
            # Limpio campos transaccionales y refresco existencias en vivo
            self.entry_cant.delete(0, "end")
            self.observaciones.delete("1.0", "end")
            self.actualizar_stock()
            self._validar_en_vivo()

    def _message(self, message, success):
        """Muestro un mensaje de retroalimentación en verde si fue exitoso o rojo si fue bloqueado."""
        self.lbl_mensaje.configure(
            text=("✓  " if success else "⚠  ") + message,
            text_color=COLORS["green"] if success else COLORS["red"]
        )

    def limpiar(self):
        """Limpio todos los campos del formulario para un nuevo registro."""
        for entry in (self.entry_doc, self.entry_cant, self.entry_costo):
            entry.delete(0, "end")
        self.observaciones.delete("1.0", "end")
        self.lbl_mensaje.configure(text="")
        self.lbl_simulacion.configure(text="")
        self.actualizar_stock()
        self._validar_en_vivo()
