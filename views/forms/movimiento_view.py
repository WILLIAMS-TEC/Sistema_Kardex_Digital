"""
Vista de Captura y Registro de Movimientos de Inventario.
Sistema Inventarios Kardex Digital.

En esta vista programé el formulario interactivo para registrar transacciones:
- Entradas de mercadería y compras.
- Despachos y salidas con validación de existencia en bodega.
- Devoluciones de mercadería.
- Envío de solicitudes de ajuste justificadas al Administrador.
- Indicador visual en vivo del stock disponible en la bodega seleccionada.
"""

import customtkinter as ctk

# Controladores de negocio para conectar con el motor de inventarios
from controllers.kardex_ctrl import (
    obtener_bodegas, obtener_productos, obtener_stock_producto, registrar_movimiento,
    obtener_motivos,
)
from views.ui_theme import COLORS, HeroBanner, card, font


class RegistroMovimientoView(ctk.CTkScrollableFrame):
    """
    Clase principal del formulario de movimientos y solicitudes de ajuste de inventario.
    """

    def __init__(self, parent, usuario):
        # Inicializo el frame deslizable con estética transparente
        super().__init__(parent, fg_color="transparent", corner_radius=0,
                         scrollbar_button_color=COLORS["border"])
        self.usuario = usuario
        self.grid_columnconfigure(0, weight=1)

        # Cargo las listas de bodegas, productos y motivos registrados en la base de datos
        self.bodegas_data = obtener_bodegas()
        self.productos_data = obtener_productos()
        self.motivos_data = obtener_motivos()

        # Banner superior ilustrado con mensaje sobre la trazabilidad y circuito de auditoría
        HeroBanner(
            self, "Trazabilidad Logística", "Gestión de Movimientos y Ajustes",
            "Registra entradas, salidas, devoluciones y solicitudes de ajuste con auditoría completa.\n"
            "Los ajustes de inventario pasan por el circuito de revisión y autorización administrativa.",
            "Cada movimiento,\nregistrado y justificado.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Construyo el cuerpo principal del formulario
        self._build_content()

    def _build_content(self):
        """
        Aquí divido la vista en dos columnas:
        - Columna Izquierda (75%): Formulario para captura de datos del movimiento.
        - Columna Derecha (25%): Tarjeta de consulta en vivo del stock físico disponible.
        """
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3) # Formulario
        content.grid_columnconfigure(1, weight=1) # Tarjeta de stock en vivo

        # Tarjeta principal del formulario con bordes redondeados
        form = card(content)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        form.grid_columnconfigure((0, 1), weight=1)

        # Icono y encabezado del formulario
        ctk.CTkLabel(form, text="⇄", font=font(28, "bold"), text_color=COLORS["blue"])\
            .grid(row=0, column=0, sticky="w", padx=(24, 0), pady=(20, 0))
        title = ctk.CTkFrame(form, fg_color="transparent")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=68, pady=(18, 16))
        ctk.CTkLabel(title, text="Datos del Movimiento o Solicitud", font=font(17, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title, text="Completa los datos para registrar movimientos o solicitar ajustes de stock.",
                     font=font(10), text_color=COLORS["muted"]).pack(anchor="w")

        # Fila 1: Selector de tipo de movimiento y selector de bodega
        tipos = ["Entrada", "Salida", "Devolución", "Ajuste Positivo (+)", "Ajuste Negativo (-)"]
        self.cb_tipo = self._field_option(form, 1, 0, "Tipo de Movimiento", tipos, self._on_tipo_changed)
        bodegas = [f"{b['id']} - {b['nombre']}" for b in self.bodegas_data] or ["No hay bodegas disponibles"]
        self.cb_bodega = self._field_option(form, 1, 1, "Bodega Afectada", bodegas, self.actualizar_stock)

        # Fila 2: Selector de producto tecnológico y documento de referencia (factura, remisión, folio)
        productos = [f"{p['id']} - {p['codigo']} · {p['nombre']}" for p in self.productos_data] or ["No hay productos disponibles"]
        self.cb_producto = self._field_option(form, 2, 0, "Producto Tecnológico", productos, self.actualizar_stock)
        self.entry_doc = self._field_entry(form, 2, 1, "Documento de Referencia", "Factura, remisión o folio de conteo")

        # Fila 3: Cantidad numérica y costo unitario en Quetzales
        self.entry_cant = self._field_entry(form, 3, 0, "Cantidad a Operar", "0")
        self.entry_costo = self._field_entry(form, 3, 1, "Costo Unitario (Q)", "0.00")

        # Fila 4: Motivo de excepción para justificar ajustes
        motivos_opts = ["Sin motivo especial"] + [f"{m['id']} - {m['descripcion']}" for m in self.motivos_data]
        self.cb_motivo = self._field_option(form, 4, 0, "Motivo de Excepción / Ajuste", motivos_opts)

        # Fila 5 y 6: Cuadro de observaciones / justificación detallada obligatoria
        ctk.CTkLabel(form, text="Observaciones / Justificación Detallada", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w")\
            .grid(row=5, column=0, columnspan=2, sticky="ew", padx=24, pady=(12, 4))
        self.observaciones = ctk.CTkTextbox(form, height=75, corner_radius=8,
                                            fg_color=COLORS["field"], border_width=1,
                                            border_color=COLORS["border"], font=font(11))
        self.observaciones.grid(row=6, column=0, columnspan=2, sticky="ew", padx=24)

        # Fila 7: Etiqueta para mensajes de validación y retroalimentación
        self.lbl_mensaje = ctk.CTkLabel(form, text="", height=26, font=font(10), anchor="w")
        self.lbl_mensaje.grid(row=7, column=0, columnspan=2, sticky="ew", padx=24, pady=(8, 0))

        # Fila 8: Botones de acción (Limpiar y Guardar/Enviar)
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=8, column=0, columnspan=2, sticky="ew", padx=24, pady=(8, 22))
        actions.grid_columnconfigure(0, weight=1)

        # Botón para limpiar todos los campos
        ctk.CTkButton(actions, text="✕  Limpiar", width=120, height=44,
                      fg_color=COLORS["field"], hover_color=COLORS["card_alt"],
                      border_width=1, border_color=COLORS["border"],
                      command=self.limpiar).grid(row=0, column=0, sticky="e", padx=(0, 8))

        # Botón dinámico que cambia de nombre y color si es movimiento directo o ajuste
        self.btn_guardar = ctk.CTkButton(actions, text="＋  Guardar Movimiento", width=220,
                                         height=44, fg_color=COLORS["blue"],
                                         hover_color=COLORS["blue_dark"],
                                         font=font(11, "bold"), command=self.guardar)
        self.btn_guardar.grid(row=0, column=1)

        # ---------------- COLUMNA DERECHA: Indicador de Stock Físico en Vivo ----------------
        side = card(content)
        side.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(side, text="◇", width=68, height=68, corner_radius=12,
                     fg_color="#123F72", font=font(30), text_color="#C9E1FF")\
            .pack(pady=(36, 12))
        ctk.CTkLabel(side, text="Stock Disponible", font=font(16, "bold"),
                     text_color=COLORS["text"]).pack()

        # Etiqueta que muestra en números grandes las existencias actuales
        self.lbl_stock_actual = ctk.CTkLabel(side, text="--", font=font(38, "bold"),
                                             text_color=COLORS["green"])
        self.lbl_stock_actual.pack(pady=(10, 0))
        ctk.CTkLabel(side, text="unidades en la bodega seleccionada", font=font(10),
                     wraplength=210, text_color=COLORS["muted"]).pack(padx=20)

        ctk.CTkFrame(side, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=24, pady=28)
        ctk.CTkLabel(side, text="Validación de Seguridad", font=font(11, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=24)
        ctk.CTkLabel(side, text="Las salidas que superen las existencias físicas disponibles serán bloqueadas automáticamente.",
                     font=font(10), wraplength=230, justify="left",
                     text_color=COLORS["muted"]).pack(anchor="w", padx=24, pady=(6, 0))

        # Actualizo el stock del primer producto seleccionado
        self.actualizar_stock()

    def _field_option(self, parent, row, col, label, values, command=None):
        """Aquí construyo una celda de formulario con su título y menú desplegable redondeado."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=(24 if col == 0 else 10, 10 if col == 0 else 24), pady=8)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        control = ctk.CTkOptionMenu(box, values=values, height=42, corner_radius=8,
                                    fg_color=COLORS["field"], button_color=COLORS["field"],
                                    button_hover_color=COLORS["card_alt"],
                                    font=font(10), dropdown_font=font(10), command=command)
        control.pack(fill="x")
        return control

    def _field_entry(self, parent, row, col, label, placeholder):
        """Aquí construyo una celda de formulario con su título y campo de texto estilizado."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=(24 if col == 0 else 10, 10 if col == 0 else 24), pady=8)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        control = ctk.CTkEntry(box, placeholder_text=placeholder, height=42,
                               fg_color=COLORS["field"], border_color=COLORS["border"],
                               font=font(10))
        control.pack(fill="x")
        return control

    def _selected_ids(self):
        """Aquí parseo y extraigo los IDs numéricos de la bodega y producto seleccionados en los OptionMenu."""
        warehouse = self.cb_bodega.get()
        product = self.cb_producto.get()
        if " - " not in warehouse or " - " not in product:
            return None, None
        try:
            return int(warehouse.split(" - ", 1)[0]), int(product.split(" - ", 1)[0])
        except ValueError:
            return None, None

    def actualizar_stock(self, _choice=None):
        """
        En este método consulto el stock actual del producto en la bodega elegida
        y actualizo la tarjeta lateral: verde si hay existencias, rojo si está agotado.
        """
        warehouse_id, product_id = self._selected_ids()
        if warehouse_id is None:
            self.lbl_stock_actual.configure(text="--", text_color=COLORS["muted"])
            return
        stock = obtener_stock_producto(product_id, warehouse_id)
        self.lbl_stock_actual.configure(text=f"{float(stock):.1f}",
                                        text_color=COLORS["red"] if float(stock) <= 0 else COLORS["green"])

    def _on_tipo_changed(self, choice):
        """
        Aquí adapto visualmente el botón según el tipo de movimiento:
        - Si es un Ajuste: El botón cambia a púrpura y dice 'Enviar Solicitud de Ajuste' (va a revisión).
        - Si es Entrada/Salida: El botón se mantiene azul y dice 'Guardar Movimiento' (impacto directo).
        """
        if "Ajuste" in choice:
            self.btn_guardar.configure(text="＋  Enviar Solicitud de Ajuste", fg_color=COLORS["purple"])
        else:
            self.btn_guardar.configure(text="＋  Guardar Movimiento", fg_color=COLORS["blue"])

    def guardar(self):
        """
        Aquí proceso el guardado del movimiento:
        1. Valido que se haya seleccionado bodega y producto válidos.
        2. Convierto y verifico que la cantidad sea positiva y el costo sea numérico.
        3. Identifico el tipo de movimiento (Entrada=1, Salida=2, Devolución=3, Ajuste+=4, Ajuste-=5).
        4. Llamo a registrar_movimiento en kardex_ctrl.
        5. Notifico al usuario del resultado y refresco el stock en pantalla.
        """
        warehouse_id, product_id = self._selected_ids()
        if warehouse_id is None:
            self._message("No hay una bodega y un producto válidos.", False)
            return
        try:
            quantity = float(self.entry_cant.get())
            cost = float(self.entry_costo.get() or 0)
            if quantity <= 0 or cost < 0:
                raise ValueError
        except ValueError:
            self._message("Cantidad y costo deben ser números válidos mayores a cero.", False)
            return
            
        kind = self.cb_tipo.get()
        type_id_map = {
            "Entrada": 1,
            "Salida": 2,
            "Devolución": 3,
            "Ajuste Positivo (+)": 4,
            "Ajuste Negativo (-)": 5,
        }
        type_id = type_id_map.get(kind, 1)
        
        # Asigno bodegas según si la mercadería entra o sale
        if kind == "Salida" or "Negativo" in kind:
            origin = warehouse_id
            destination = None
        else:
            origin = None
            destination = warehouse_id
            
        user_id = getattr(self.usuario, "ID_USUARIO", None)
        if user_id is None:
            self._message("No se pudo identificar al usuario de la sesión.", False)
            return

        # Valido permisos: El rol de Consultas no tiene permiso para operar transacciones
        from controllers.auth_ctrl import is_consultas_role
        role_id = getattr(self.usuario, "ID_ROL", None)
        role_name = getattr(self.usuario, "rol_nombre", "")
        if is_consultas_role(role_name, role_id):
            self._message("Tu perfil de usuario (Consultas) es de solo lectura y no puede registrar movimientos.", False)
            return
            
        # Parseo el ID del motivo de ajuste si fue seleccionado
        motivo_str = self.cb_motivo.get()
        motivo_id = None
        if " - " in motivo_str:
            try:
                motivo_id = int(motivo_str.split(" - ", 1)[0])
            except ValueError:
                motivo_id = None

        # REGLA ESTRICTA DE AUDITORÍA: Para solicitar ajustes, el motivo y la justificación descriptiva son OBLIGATORIOS
        justificacion = self.observaciones.get("1.0", "end").strip()
        if "Ajuste" in kind:
            if not motivo_id:
                self._message("Para solicitar un ajuste debes seleccionar un Motivo de Excepción específico.", False)
                return
            if len(justificacion) < 10:
                self._message("Es obligatoria la justificación detallada del porqué solicitas el ajuste (mínimo 10 caracteres).", False)
                return
                
        # Deshabilito el botón para prevenir envíos duplicados
        self.btn_guardar.configure(state="disabled", text="Procesando transacción...")
        self.update_idletasks()
        
        # Ejecuto la transacción en la base de datos
        success, message = registrar_movimiento(
            user_id, type_id, origin, destination, self.entry_doc.get().strip(),
            [{"id_producto": product_id, "cantidad": quantity, "costo_unitario": cost}],
            motivo_id=motivo_id,
            observaciones=justificacion,
        )
        
        # Restauro el estado del botón
        self.btn_guardar.configure(
            state="normal",
            text="＋  Enviar Solicitud de Ajuste" if "Ajuste" in kind else "＋  Guardar Movimiento"
        )
        self._message(message, success)
        if success:
            # Limpio la cantidad, observaciones y refresco las existencias en vivo
            self.entry_cant.delete(0, "end")
            self.observaciones.delete("1.0", "end")
            self.actualizar_stock()
            self.actualizar_stock()

    def _message(self, message, success):
        """Muestro un mensaje de retroalimentación en verde si fue exitoso o rojo si hubo error."""
        self.lbl_mensaje.configure(text=("✓  " if success else "⚠  ") + message,
                                   text_color=COLORS["green"] if success else COLORS["red"])

    def limpiar(self):
        """Limpio todos los campos del formulario para un nuevo registro."""
        for entry in (self.entry_doc, self.entry_cant, self.entry_costo):
            entry.delete(0, "end")
        self.observaciones.delete("1.0", "end")
        self.lbl_mensaje.configure(text="")
        self.actualizar_stock()
