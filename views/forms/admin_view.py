"""
Sistema Inventarios Kardex Digital — Módulo de Administración, Catálogo y Aprobaciones.
Rediseño completo con arquitectura de paneles divididos (Split-Pane Studio),
fichas de especificación técnica, tarjetas interactivas de usuarios y
panel de justificación detallada para la aprobación de ajustes de inventario.
"""

from tkinter import messagebox
import tkinter as tk
import customtkinter as ctk

# Controladores de negocio para conectar con la base de datos SQL
from controllers.admin_ctrl import (
    actualizar_producto, actualizar_usuario, crear_producto, crear_usuario,
    obtener_catalogo, obtener_categorias, obtener_roles, obtener_unidades,
    obtener_usuarios, toggle_estado_producto, toggle_estado_usuario,
    obtener_ajustes_pendientes, aprobar_ajuste, rechazar_ajuste,
    obtener_solicitudes_ajuste
)
from controllers.auth_ctrl import is_admin_role
from views.ui_theme import COLORS, HeroBanner, VectorIcon, card, font, status_style


class AdminView(ctk.CTkScrollableFrame):
    """
    Vista de Administración Central y Control de Catálogo.
    Aquí organizo la gestión de usuarios, el catálogo maestro de existencias y
    la mesa de aprobación de ajustes con justificación de bodega.
    """

    def __init__(self, parent, usuario=None, initial_tab=None, es_admin=True, rol=None):
        # Inicializo el frame desplazable principal con fondo transparente y scrollbar personalizado
        super().__init__(parent, fg_color="transparent", corner_radius=0,
                         scrollbar_button_color=COLORS["border"],
                         scrollbar_button_hover_color=COLORS["blue"])
        
        # Guardo la referencia del usuario autenticado y su rol
        self.usuario = usuario
        role_id = getattr(self.usuario, "ID_ROL", None)
        user_role_str = str(rol or "")
        if not user_role_str:
            user_role_str = getattr(self.usuario, "rol_nombre", "")
        if not user_role_str:
            try:
                user_role_str = getattr(getattr(self.usuario, "rol", None), "NOMBRE_ROL", "")
            except Exception:
                user_role_str = ""
        
        # Verifico si el usuario tiene permisos de Administrador para habilitar todas las pestañas
        self.es_admin = es_admin and (is_admin_role(user_role_str, role_id) if role_id else True)

        self.grid_columnconfigure(0, weight=1)
        self.current_tab = initial_tab or ("users" if self.es_admin else "products")
        
        # Variables para controlar qué elemento estoy editando actualmente (None = creación nueva)
        self.id_usuario_editando = None
        self.id_producto_editando = None
        
        # Registro en sesión de solicitudes de ajuste autorizadas o rechazadas para removerlas en vivo
        self.solicitudes_procesadas = set()

        # Configuro los textos del encabezado según los permisos del usuario
        if self.es_admin:
            banner_title = "Control Maestro y Catálogo Kardex"
            banner_sub = ("Gestión de usuarios autorizados, administración del catálogo oficial de existencias\n"
                          "y circuito de autorización de ajustes para el Sistema Inventarios Kardex Digital.")
            banner_badge = "Auditoría\nKardex Digital"
        else:
            banner_title = "Catálogo Oficial y Operación de Bodega"
            banner_sub = ("Consulta y actualiza especificaciones en el catálogo oficial de existencias.\n"
                          "Supervisa el estado y resolución de tus solicitudes de ajuste de inventario.")
            banner_badge = "Operación de\nBodega"

        # Coloco el banner superior con el arte vectorial de libros de inventario
        HeroBanner(
            self, "Administración & Auditoría Maestra", banner_title,
            banner_sub, banner_badge,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Construyo la barra de pestañas de navegación
        self._build_tabs()

        # Contenedor dinámico donde se monta el contenido de la pestaña seleccionada
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=2, column=0, sticky="nsew", pady=(12, 14))
        self.content.grid_columnconfigure(0, weight=1)

        # Muestro la pestaña inicial
        self.show_tab(self.current_tab)

    # -------------------------------------------------------------------------
    # NAVEGACIÓN Y SELECTOR DE PESTAÑAS
    # -------------------------------------------------------------------------
    def _build_tabs(self):
        """Aquí construyo la barra de botones redondeados para alternar entre apartados."""
        nav = card(self, height=62, corner_radius=14)
        nav.grid(row=1, column=0, sticky="ew")
        nav.grid_propagate(False)
        self.tab_buttons = {}
        
        # Si es admin tiene acceso a Usuarios, Catálogo y Aprobaciones
        if self.es_admin:
            items = (
                ("users", "👥   Gestión de Usuarios"),
                ("products", "📦   Catálogo de Productos"),
                ("approvals", "⚖   Aprobar Ajustes de Bodega")
            )
            nav.grid_columnconfigure((0, 1, 2), weight=1, uniform="tabs")
        else:
            # Si es operador de bodega, solo accede a catálogo y al estado de sus solicitudes
            items = (
                ("products", "📦   Catálogo de Productos"),
                ("requests", "📋   Mis Solicitudes de Ajuste")
            )
            nav.grid_columnconfigure((0, 1), weight=1, uniform="tabs")

        for col, (key, text) in enumerate(items):
            btn = ctk.CTkButton(
                nav, text=text, height=50, corner_radius=10,
                fg_color="transparent", hover_color=COLORS["card_alt"],
                font=font(12, "bold"), text_color=COLORS["muted"],
                command=lambda k=key: self.show_tab(k)
            )
            btn.grid(row=0, column=col, sticky="nsew", padx=4, pady=5)
            self.tab_buttons[key] = btn

    def show_tab(self, key):
        """Cambio de pestaña activa: limpio el contenedor y construyo la vista solicitada."""
        if not self.es_admin and key in ("users", "approvals"):
            key = "products"
        self.current_tab = key

        # Actualizo el aspecto de los botones (el activo se ilumina en azul zafiro)
        for name, btn in self.tab_buttons.items():
            is_active = (name == key)
            btn.configure(
                fg_color=COLORS["blue"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else COLORS["muted"]
            )

        # Destruyo los widgets anteriores para que no se sobrepongan
        for widget in self.content.winfo_children():
            widget.destroy()

        # Reseteo las configuraciones de columnas y filas previas para evitar colapso de dimensiones
        for col_i in range(10):
            self.content.grid_columnconfigure(col_i, weight=0, uniform="")
        for row_i in range(10):
            self.content.grid_rowconfigure(row_i, weight=0, uniform="")

        # Invoco el constructor del apartado correspondiente
        if key == "users":
            self._build_users()
        elif key == "products":
            self._build_products()
        elif key == "approvals":
            self._build_approvals()
        elif key == "requests":
            self._build_requests()

    # =========================================================================
    # APARTADO 1: GESTIÓN DE USUARIOS (DISEÑO TIPO CREDENCIAL & DIRECTORIO)
    # =========================================================================
    def _build_users(self):
        """
        Aquí construyo el apartado de usuarios con un diseño asimétrico completamente nuevo:
        - Columna Izquierda (38%): Formulario tipo credencial digital interactiva.
        - Columna Derecha (62%): Directorio de usuarios en tarjetas interactivas con buscador.
        """
        self.content.grid_columnconfigure(0, weight=38, uniform="user_cols")
        self.content.grid_columnconfigure(1, weight=62, uniform="user_cols")
        self.content.grid_rowconfigure(0, weight=1)

        # 1. Cargo los roles de usuario desde la base de datos
        db_roles = obtener_roles()
        self.roles = db_roles if db_roles else [
            {"id": 1, "nombre": "Administrador"},
            {"id": 2, "nombre": "Encargado de bodega"},
            {"id": 3, "nombre": "Consulta / supervisión"},
        ]
        self.role_values = []
        for r in self.roles:
            r_id = r["id"]
            r_nom = r["nombre"]
            if r_id == 1:
                desc = "Administrador (Control Total)"
            elif r_id == 2:
                desc = "Encargado de Bodega (Operativo)"
            elif r_id == 3:
                desc = "Consultas (Solo Descargas)"
            else:
                desc = r_nom
            self.role_values.append(f"{r_id} - {desc}")

        # ---------------- COLUMNA IZQUIERDA: Formulario Credencial ----------------
        left_panel = card(self.content, corner_radius=16)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        left_panel.grid_columnconfigure(0, weight=1)

        # Encabezado visual de la credencial
        badge_top = ctk.CTkFrame(left_panel, fg_color="transparent")
        badge_top.pack(fill="x", padx=20, pady=(18, 4))
        ctk.CTkLabel(badge_top, text="✦  CREDENCIAL DE ACCESO", font=font(10, "bold"),
                     text_color=COLORS["cyan"]).pack(anchor="w")

        self.user_form_title = ctk.CTkLabel(left_panel, text="Registrar Nuevo Usuario",
                                           font=font(18, "bold"), text_color=COLORS["text"], anchor="w")
        self.user_form_title.pack(fill="x", padx=20)
        ctk.CTkLabel(left_panel, text="Crea o edita cuentas autorizadas para operar en Kardex Digital.",
                     font=font(10), text_color=COLORS["muted"], anchor="w").pack(fill="x", padx=20, pady=(2, 14))

        # Avatar digital con iniciales que se actualizan
        avatar_box = ctk.CTkFrame(left_panel, fg_color=COLORS["field"], corner_radius=12,
                                  border_width=1, border_color=COLORS["border"])
        avatar_box.pack(fill="x", padx=20, pady=(0, 16))
        self.user_avatar_label = ctk.CTkLabel(
            avatar_box, text="👤  US", width=48, height=48, corner_radius=24,
            fg_color=COLORS["blue_dark"], text_color="#FFFFFF", font=font(14, "bold")
        )
        self.user_avatar_label.pack(side="left", padx=12, pady=10)
        
        avatar_info = ctk.CTkFrame(avatar_box, fg_color="transparent")
        avatar_info.pack(side="left", fill="both", expand=True, pady=10)
        self.user_preview_name = ctk.CTkLabel(avatar_info, text="Nombre de Usuario", font=font(11, "bold"),
                                             text_color=COLORS["text"], anchor="w")
        self.user_preview_name.pack(fill="x")
        self.user_preview_role = ctk.CTkLabel(avatar_info, text="Rol asignado en el sistema", font=font(9),
                                             text_color=COLORS["cyan"], anchor="w")
        self.user_preview_role.pack(fill="x")

        # Campos de entrada con etiquetas claras
        ctk.CTkLabel(left_panel, text="Nombre Completo", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=20, pady=(0, 3))
        self.u_nombre = self._modern_entry(left_panel, "Ej. Juan Pérez García", on_change=self._on_user_name_typing)

        ctk.CTkLabel(left_panel, text="Correo Electrónico Institucional", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        self.u_correo = self._modern_entry(left_panel, "usuario@kardex.com")

        ctk.CTkLabel(left_panel, text="Contraseña de Acceso", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        self.u_pass = self._modern_entry(left_panel, "Ingresa una contraseña segura", show="●")

        ctk.CTkLabel(left_panel, text="Rol y Nivel de Permisos", font=font(10, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=20, pady=(10, 3))
        self.u_rol = ctk.CTkOptionMenu(
            left_panel, values=self.role_values, height=40, corner_radius=10,
            fg_color=COLORS["field"], button_color=COLORS["card_alt"],
            button_hover_color=COLORS["border"], dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"], font=font(11), command=self._on_user_role_changed
        )
        self.u_rol.pack(fill="x", padx=20)
        if self.role_values:
            self.u_rol.set(self.role_values[0])

        # Mensaje de retroalimentación (éxito o error)
        self.user_message = ctk.CTkLabel(left_panel, text="", height=20, font=font(10, "bold"), anchor="w")
        self.user_message.pack(fill="x", padx=20, pady=(8, 4))

        # Botón de guardar / actualizar de alto contraste
        self.user_save = ctk.CTkButton(
            left_panel, text="💾   Guardar Usuario en el Sistema", height=44, corner_radius=10,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"],
            font=font(12, "bold"), command=self.save_user
        )
        self.user_save.pack(fill="x", padx=20, pady=(2, 6))

        # Botón para limpiar o cancelar edición
        self.user_clear_btn = ctk.CTkButton(
            left_panel, text="✕   Limpiar Formulario", height=34, corner_radius=8,
            fg_color=COLORS["field"], hover_color=COLORS["card_alt"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["muted"], font=font(10), command=self.clear_user_form
        )
        self.user_clear_btn.pack(fill="x", padx=20, pady=(0, 18))

        # ---------------- COLUMNA DERECHA: Directorio Interactivo ----------------
        right_panel = card(self.content, corner_radius=16)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        right_panel.grid_rowconfigure(2, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Encabezado del directorio con buscador
        head = ctk.CTkFrame(right_panel, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))
        head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(head, text="Directorio de Cuentas Autorizadas", font=font(16, "bold"),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        self.user_count = ctk.CTkLabel(head, text="Cargando usuarios...", font=font(10),
                                      text_color=COLORS["muted"])
        self.user_count.grid(row=1, column=0, sticky="w")

        # Campo de búsqueda en vivo
        self.user_search = ctk.CTkEntry(
            head, width=280, height=38, corner_radius=10,
            placeholder_text="⌕  Buscar por nombre, correo o rol...",
            fg_color=COLORS["field"], border_color=COLORS["border"], font=font(10)
        )
        self.user_search.grid(row=0, column=1, rowspan=2, sticky="e")
        self.user_search.bind("<KeyRelease>", lambda _e: self.render_users())

        # Cabecera de la tabla de usuarios
        self._table_header(
            right_panel, 1,
            (("#", 6), ("Usuario y Correo", 34), ("Rol Asignado", 26),
             ("Estado", 14), ("Acciones", 20))
        )

        # Lista deslizable donde renderizo las tarjetas de usuario
        self.users_body = ctk.CTkScrollableFrame(
            right_panel, height=360, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["border"]
        )
        self.users_body.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.users_body.grid_columnconfigure(0, weight=1)

        # Renderizo los usuarios en la lista
        self.render_users()

    def _on_user_name_typing(self, _event=None):
        """Actualizo en vivo el nombre y las iniciales en el avatar mientras el usuario escribe."""
        name = self.u_nombre.get().strip() or "Nombre de Usuario"
        self.user_preview_name.configure(text=name)
        parts = name.split()
        initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "US"
        self.user_avatar_label.configure(text=f"👤  {initials}")

    def _on_user_role_changed(self, choice):
        """Muestro en la tarjeta previa la descripción del rol seleccionado."""
        self.user_preview_role.configure(text=choice.split(" - ", 1)[-1] if " - " in choice else choice)

    def render_users(self):
        """Consulto y dibujo cada fila de usuario como una tarjeta limpia."""
        for widget in self.users_body.winfo_children():
            widget.destroy()

        users = obtener_usuarios()
        if not users:
            # Datos de respaldo representativos si no hay base de datos conectada
            users = [
                {"id": 1, "nombre": "Williams", "correo": "SEQUENW7@GMAIL.COM", "id_rol": 1, "rol": "Administrador", "estado": True},
                {"id": 2, "nombre": "Carlos Almacén", "correo": "bodega@kardex.com", "id_rol": 2, "rol": "Encargado de bodega", "estado": True},
                {"id": 3, "nombre": "Auditor Consultas", "correo": "auditoria@kardex.com", "id_rol": 3, "rol": "Consulta / supervisión", "estado": True},
            ]

        # Filtro según el texto del buscador
        query = self.user_search.get().strip().casefold()
        if query:
            users = [u for u in users if query in f"{u['nombre']} {u['correo']} {u['rol']}".casefold()]

        for idx, user in enumerate(users):
            row = ctk.CTkFrame(self.users_body, fg_color=COLORS["card_alt"], height=52, corner_radius=10)
            row.grid(row=idx*2, column=0, sticky="ew", pady=3)
            row.grid_propagate(False)

            for col, weight in enumerate((6, 34, 26, 14, 20)):
                row.grid_columnconfigure(col, weight=weight, uniform="users_table")

            # ID de usuario
            ctk.CTkLabel(row, text=f"#{user['id']}", anchor="w", font=font(10, "bold"),
                         text_color=COLORS["muted"]).grid(row=0, column=0, sticky="ew", padx=(12, 4))

            # Nombre y Correo
            u_box = ctk.CTkFrame(row, fg_color="transparent")
            u_box.grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(u_box, text=user["nombre"], anchor="w", font=font(11, "bold"),
                         text_color=COLORS["text"]).pack(fill="x")
            ctk.CTkLabel(u_box, text=user["correo"], anchor="w", font=font(9),
                         text_color=COLORS["muted"]).pack(fill="x")

            # Rol con píldora
            role_color = COLORS["cyan"] if user["id_rol"] == 1 else (COLORS["green"] if user["id_rol"] == 2 else COLORS["purple"])
            ctk.CTkLabel(row, text=f"◈  {user['rol']}", anchor="w", font=font(10, "bold"),
                         text_color=role_color).grid(row=0, column=2, sticky="ew", padx=6)

            # Estado (Activo / Inactivo)
            state_text = "●  Activo" if user["estado"] else "○  Inactivo"
            state_color = COLORS["green"] if user["estado"] else COLORS["red"]
            state_bg = COLORS["green_bg"] if user["estado"] else COLORS["red_bg"]
            ctk.CTkLabel(row, text=state_text, height=26, corner_radius=13,
                         fg_color=state_bg, text_color=state_color, font=font(9, "bold"))\
                .grid(row=0, column=3, sticky="w", padx=6)

            # Botones de Acción
            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=4, sticky="ew", padx=(4, 12))
            ctk.CTkButton(
                actions, text="✎ Editar", width=68, height=30, corner_radius=7,
                fg_color=COLORS["field"], hover_color=COLORS["border"],
                text_color=COLORS["cyan"], font=font(9, "bold"),
                command=lambda u=user: self.edit_user(u)
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                actions, text="Desactivar" if user["estado"] else "Activar",
                width=76, height=30, corner_radius=7,
                fg_color=COLORS["red_bg"] if user["estado"] else COLORS["green_bg"],
                hover_color="#5C1622" if user["estado"] else "#083C2B",
                text_color=COLORS["red"] if user["estado"] else COLORS["green"],
                font=font(9, "bold"),
                command=lambda uid=user["id"]: self.toggle_user(uid)
            ).pack(side="left")

        self.user_count.configure(text=f"Total: {len(users)} cuentas registradas en el sistema")

    def edit_user(self, user):
        """Cargo los datos del usuario seleccionado en el formulario para editarlo."""
        self.id_usuario_editando = user["id"]
        self.u_nombre.delete(0, "end")
        self.u_nombre.insert(0, user["nombre"])
        self.u_correo.delete(0, "end")
        self.u_correo.insert(0, user["correo"])
        self.u_pass.delete(0, "end")

        for role_str in self.role_values:
            if role_str.startswith(f"{user['id_rol']} -"):
                self.u_rol.set(role_str)
                break

        self._on_user_name_typing()
        self.user_form_title.configure(text=f"Editar Usuario #{user['id']}")
        self.user_save.configure(text="✓   Actualizar Credenciales", fg_color=COLORS["green"], hover_color="#059669")
        self.user_clear_btn.configure(text="✕   Cancelar Edición")
        self.user_message.configure(text="Modificando usuario. Deja contraseña en blanco para mantener la actual.", text_color=COLORS["cyan"])

    def save_user(self):
        """Valido y guardo el usuario nuevo o editado a través del controlador."""
        name = self.u_nombre.get().strip()
        email = self.u_correo.get().strip()
        password = self.u_pass.get()
        role_choice = self.u_rol.get()

        if not name or not email or "@" not in email:
            self.user_message.configure(text="⚠ Ingresa un nombre y correo electrónico válidos.", text_color=COLORS["red"])
            return

        if not self.id_usuario_editando and not password:
            self.user_message.configure(text="⚠ La contraseña es obligatoria para nuevos usuarios.", text_color=COLORS["red"])
            return

        role_id = int(role_choice.split(" - ")[0]) if " - " in role_choice else 1

        if self.id_usuario_editando:
            res = actualizar_usuario(self.id_usuario_editando, name, email, password, role_id)
            if isinstance(res, tuple):
                success, msg = res
            else:
                success = bool(res)
                msg = "Usuario actualizado correctamente." if success else "No fue posible actualizar el usuario."
        else:
            res = crear_usuario(name, email, password, role_id)
            if isinstance(res, tuple):
                success, msg = res
            else:
                success = bool(res)
                msg = "Usuario creado exitosamente." if success else "No fue posible crear el usuario en la BD."

        self.user_message.configure(text=("✓ " if success else "⚠ ") + msg,
                                    text_color=COLORS["green"] if success else COLORS["red"])
        if success:
            self.clear_user_form()
            self.render_users()

    def clear_user_form(self):
        """Limpio el formulario para volver al modo de creación."""
        self.id_usuario_editando = None
        self.u_nombre.delete(0, "end")
        self.u_correo.delete(0, "end")
        self.u_pass.delete(0, "end")
        self.user_form_title.configure(text="Registrar Nuevo Usuario")
        self.user_save.configure(text="💾   Guardar Usuario en el Sistema", fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"])
        self.user_clear_btn.configure(text="✕   Limpiar Formulario")
        self.user_message.configure(text="")
        self.user_preview_name.configure(text="Nombre de Usuario")
        self.user_avatar_label.configure(text="👤  US")

    def toggle_user(self, user_id):
        """Activo o desactivo el acceso del usuario."""
        toggle_estado_usuario(user_id)
        self.render_users()

    # =========================================================================
    # APARTADO 2: CATÁLOGO DE PRODUCTOS (FICHA TÉCNICA KARDEX & FILTROS)
    # =========================================================================
    def _build_products(self):
        """
        Aquí construyo el catálogo de productos con un formato de Ficha Técnica Kardex:
        - Bloque Superior: Ficha técnica de especificación de producto (SKU, nombre, categoría, unidad, stock mín, costo).
        - Bloque Inferior: Catálogo interactivo con buscador y semáforos de stock.
        """
        self.content.grid_columnconfigure(0, weight=1, uniform="")
        self.content.grid_columnconfigure(1, weight=0, uniform="")
        self.content.grid_rowconfigure(0, weight=0)
        self.content.grid_rowconfigure(1, weight=1)

        categories = obtener_categorias() or [{"id": 1, "nombre": "Electrónica"}, {"id": 2, "nombre": "Mobiliario"}, {"id": 3, "nombre": "Papelería"}]
        units = obtener_unidades() or [{"id": 1, "nombre": "Unidad (Un)"}, {"id": 2, "nombre": "Caja (Cj)"}]
        self.category_values = [f"{x['id']} - {x['nombre']}" for x in categories]
        self.unit_values = [f"{x['id']} - {x['nombre']}" for x in units]

        # ---------------- 1. FICHA TÉCNICA (FORMULARIO) ----------------
        ficha_card = card(self.content, corner_radius=16)
        ficha_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ficha_card.grid_columnconfigure((0, 1, 2), weight=1)

        # Encabezado de la Ficha
        f_head = ctk.CTkFrame(ficha_card, fg_color="transparent")
        f_head.grid(row=0, column=0, columnspan=3, sticky="ew", padx=22, pady=(16, 12))
        f_head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f_head, text="📦   Ficha Técnica de Especificación de Producto",
                     font=font(16, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(f_head, text="Define los parámetros de identificación, clasificación y stock de seguridad para el Kardex.",
                     font=font(10), text_color=COLORS["muted"]).grid(row=1, column=0, sticky="w")

        # Fila 1 de Campos: Código, Descripción, Categoría
        self.p_sku = self._labeled_entry(ficha_card, 1, 0, "Código Único (SKU)", "Ej. ELEC-001")
        self.p_desc = self._labeled_entry(ficha_card, 1, 1, "Nombre o Descripción Comercial", "Ej. Laptop Dell Latitude 3420")
        self.p_cat = self._labeled_option(ficha_card, 1, 2, "Categoría Tecnológica", self.category_values)

        # Fila 2 de Campos: Unidad, Stock Mínimo, Costo
        self.p_uni = self._labeled_option(ficha_card, 2, 0, "Unidad de Medida", self.unit_values)
        self.p_min = self._labeled_entry(ficha_card, 2, 1, "Stock Mínimo de Seguridad (Alerta)", "5")
        self.p_cost = self._labeled_entry(ficha_card, 2, 2, "Costo Unitario Promedio (Q)", "1250.00")

        # Fila 3: Botones de Acción y Mensajes
        action_strip = ctk.CTkFrame(ficha_card, fg_color="transparent")
        action_strip.grid(row=3, column=0, columnspan=3, sticky="ew", padx=22, pady=(12, 16))
        action_strip.grid_columnconfigure(0, weight=1)

        self.product_message = ctk.CTkLabel(action_strip, text="", font=font(10, "bold"), anchor="w")
        self.product_message.grid(row=0, column=0, sticky="w")

        btn_group = ctk.CTkFrame(action_strip, fg_color="transparent")
        btn_group.grid(row=0, column=1, sticky="e")

        self.product_clear_btn = ctk.CTkButton(
            btn_group, text="✕   Limpiar Ficha", width=130, height=38, corner_radius=9,
            fg_color=COLORS["field"], hover_color=COLORS["card_alt"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["muted"], font=font(10, "bold"),
            command=self.clear_product_form
        )
        self.product_clear_btn.pack(side="left", padx=(0, 8))

        self.product_save = ctk.CTkButton(
            btn_group, text="＋   Guardar Producto en Catálogo", width=220, height=38, corner_radius=9,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"],
            font=font(11, "bold"), command=self.save_product
        )
        self.product_save.pack(side="left")

        # ---------------- 2. DIRECTORIO DEL CATÁLOGO ----------------
        cat_card = card(self.content, corner_radius=16)
        cat_card.grid(row=1, column=0, sticky="nsew")
        cat_card.grid_rowconfigure(2, weight=1)
        cat_card.grid_columnconfigure(0, weight=1)

        # Encabezado del Catálogo con Buscador
        cat_head = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_head.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 10))
        cat_head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cat_head, text="Catálogo Oficial de Existencias", font=font(16, "bold"),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        self.product_count_lbl = ctk.CTkLabel(cat_head, text="Cargando productos...", font=font(10),
                                              text_color=COLORS["muted"])
        self.product_count_lbl.grid(row=1, column=0, sticky="w")

        self.product_search = ctk.CTkEntry(
            cat_head, width=320, height=38, corner_radius=10,
            placeholder_text="⌕  Buscar por código o descripción...",
            fg_color=COLORS["field"], border_color=COLORS["border"], font=font(10)
        )
        self.product_search.grid(row=0, column=1, rowspan=2, sticky="e")
        self.product_search.bind("<KeyRelease>", lambda _e: self.render_products())

        # Cabecera de la tabla de productos
        self._table_header(
            cat_card, 1,
            (("Código SKU", 14), ("Descripción del Producto", 34), ("Stock Mínimo", 14),
             ("Costo Unitario", 14), ("Estado", 10), ("Acciones", 14))
        )

        # Contenedor con scroll para los productos
        self.products_body = ctk.CTkScrollableFrame(
            cat_card, height=300, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["border"]
        )
        self.products_body.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.products_body.grid_columnconfigure(0, weight=1)

        self.render_products()

    def render_products(self):
        """Renderizo cada producto en el catálogo con diseño de tarjeta y semáforo."""
        for widget in self.products_body.winfo_children():
            widget.destroy()

        products = obtener_catalogo()
        if not products:
            products = [
                {"id": 1, "codigo": "ELEC-001", "desc": "Laptop Dell Latitude 3420", "id_cat": 1, "id_uni": 1, "stock_min": 5, "costo": 5500, "estado": True},
                {"id": 2, "codigo": "ELEC-002", "desc": "Monitor LG 24 Pulgadas", "id_cat": 1, "id_uni": 1, "stock_min": 10, "costo": 1200, "estado": True},
                {"id": 3, "codigo": "MOB-001", "desc": "Silla Ergonómica Ejecutiva", "id_cat": 2, "id_uni": 1, "stock_min": 4, "costo": 850, "estado": True},
                {"id": 4, "codigo": "PAP-001", "desc": "Resma Papel Carta 75g", "id_cat": 3, "id_uni": 2, "stock_min": 20, "costo": 38, "estado": True},
            ]

        query = self.product_search.get().strip().casefold() if hasattr(self, "product_search") else ""
        if query:
            products = [p for p in products if query in f"{p['codigo']} {p['desc']}".casefold()]

        for idx, product in enumerate(products):
            row = ctk.CTkFrame(self.products_body, fg_color=COLORS["card_alt"], height=50, corner_radius=10)
            row.grid(row=idx*2, column=0, sticky="ew", pady=3)
            row.grid_propagate(False)

            for col, weight in enumerate((14, 34, 14, 14, 10, 14)):
                row.grid_columnconfigure(col, weight=weight, uniform="prod_table")

            # Código SKU con insignia
            ctk.CTkLabel(row, text=f"🏷  {product['codigo']}", anchor="w", font=font(10, "bold"),
                         text_color=COLORS["cyan"]).grid(row=0, column=0, sticky="ew", padx=(12, 4))

            # Descripción
            ctk.CTkLabel(row, text=product["desc"], anchor="w", font=font(11, "bold"),
                         text_color=COLORS["text"]).grid(row=0, column=1, sticky="ew", padx=6)

            # Stock Mínimo
            ctk.CTkLabel(row, text=f"{product.get('stock_min', 0)} unidades", anchor="w", font=font(10),
                         text_color=COLORS["muted"]).grid(row=0, column=2, sticky="ew", padx=6)

            # Costo
            ctk.CTkLabel(row, text=f"Q {float(product.get('costo', 0)):,.2f}", anchor="w", font=font(10, "bold"),
                         text_color=COLORS["mint"]).grid(row=0, column=3, sticky="ew", padx=6)

            # Estado
            state_color = COLORS["green"] if product["estado"] else COLORS["red"]
            ctk.CTkLabel(row, text="● Activo" if product["estado"] else "○ Inactivo",
                         font=font(9, "bold"), text_color=state_color).grid(row=0, column=4, sticky="w", padx=6)

            # Acciones
            acts = ctk.CTkFrame(row, fg_color="transparent")
            acts.grid(row=0, column=5, sticky="ew", padx=(4, 12))
            ctk.CTkButton(
                acts, text="✎ Editar", width=64, height=30, corner_radius=7,
                fg_color=COLORS["field"], hover_color=COLORS["border"],
                text_color=COLORS["cyan"], font=font(9, "bold"),
                command=lambda p=product: self.edit_product(p)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                acts, text="⊘" if product["estado"] else "✓", width=32, height=30, corner_radius=7,
                fg_color=COLORS["red_bg"] if product["estado"] else COLORS["green_bg"],
                text_color=COLORS["red"] if product["estado"] else COLORS["green"],
                font=font(10, "bold"),
                command=lambda pid=product["id"]: self.toggle_product(pid)
            ).pack(side="left")

        self.product_count_lbl.configure(text=f"Total: {len(products)} productos registrados en catálogo")

    def edit_product(self, product):
        """Cargo el producto en el formulario para modificar sus especificaciones."""
        self.id_producto_editando = product["id"]
        self.p_sku.delete(0, "end")
        self.p_sku.insert(0, product["codigo"])
        self.p_desc.delete(0, "end")
        self.p_desc.insert(0, product["desc"])
        self.p_min.delete(0, "end")
        self.p_min.insert(0, str(product.get("stock_min", 0)))
        self.p_cost.delete(0, "end")
        self.p_cost.insert(0, str(product.get("costo", 0)))

        for cat_str in self.category_values:
            if cat_str.startswith(f"{product.get('id_cat')} -"):
                self.p_cat.set(cat_str)
                break

        for uni_str in self.unit_values:
            if uni_str.startswith(f"{product.get('id_uni')} -"):
                self.p_uni.set(uni_str)
                break

        self.product_save.configure(text="✓   Actualizar Ficha de Producto", fg_color=COLORS["green"], hover_color="#059669")
        self.product_clear_btn.configure(text="✕   Cancelar Edición")
        self.product_message.configure(text=f"Modificando producto #{product['id']} ({product['codigo']}).", text_color=COLORS["cyan"])

    def save_product(self):
        """Valido y guardo el producto en la base de datos."""
        sku = self.p_sku.get().strip()
        desc = self.p_desc.get().strip()
        try:
            min_stock = float(self.p_min.get().strip())
            cost = float(self.p_cost.get().strip())
        except ValueError:
            self.product_message.configure(text="⚠ El stock mínimo y el costo deben ser números válidos.", text_color=COLORS["red"])
            return

        if not sku or not desc:
            self.product_message.configure(text="⚠ Ingresa un código SKU y una descripción para el producto.", text_color=COLORS["red"])
            return

        id_cat = int(self.p_cat.get().split(" - ")[0]) if " - " in self.p_cat.get() else 1
        id_uni = int(self.p_uni.get().split(" - ")[0]) if " - " in self.p_uni.get() else 1

        if self.id_producto_editando:
            success = actualizar_producto(self.id_producto_editando, sku, desc, id_cat, id_uni, min_stock, cost)
            msg = "Producto actualizado con éxito." if success else "Error al actualizar producto."
        else:
            success = crear_producto(sku, desc, id_cat, id_uni, min_stock, cost)
            msg = "Producto registrado en catálogo con éxito." if success else "Error al guardar producto en BD."

        self.product_message.configure(text=("✓ " if success else "⚠ ") + msg,
                                       text_color=COLORS["green"] if success else COLORS["red"])
        if success:
            self.clear_product_form()
            self.render_products()

    def clear_product_form(self):
        """Limpio los campos de la ficha técnica."""
        self.id_producto_editando = None
        self.p_sku.delete(0, "end")
        self.p_desc.delete(0, "end")
        self.p_min.delete(0, "end")
        self.p_min.insert(0, "5")
        self.p_cost.delete(0, "end")
        self.p_cost.insert(0, "0.00")
        self.product_save.configure(text="＋   Guardar Producto en Catálogo", fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"])
        self.product_clear_btn.configure(text="✕   Limpiar Ficha")
        self.product_message.configure(text="")

    def toggle_product(self, product_id):
        """Alterno el estado de habilitado/deshabilitado del producto."""
        toggle_estado_producto(product_id)
        self.render_products()

    # =========================================================================
    # APARTADO 3: APROBACIÓN DE AJUSTES CON JUSTIFICACIÓN DETALLADA (IMAGEN 3)
    # =========================================================================
    def _build_approvals(self):
        """
        Aquí construyo la mesa de autorización de ajustes de inventario.
        Se diseñó especialmente para mostrar:
        1. Indicadores clave de auditoría arriba.
        2. Tarjetas detalladas de solicitud con LA DESCRIPCIÓN DEL PORQUÉ LO ESTÁN SOLICITANDO.
        3. Botones directos para aprobar y aplicar al stock, o rechazar con motivo.
        """
        self.content.grid_columnconfigure(0, weight=1, uniform="")
        self.content.grid_columnconfigure(1, weight=0, uniform="")
        self.content.grid_rowconfigure(0, weight=0)
        self.content.grid_rowconfigure(1, weight=1)

        db_pendientes = obtener_ajustes_pendientes() or []
        # Excluyo las solicitudes que ya autoricé o rechacé en la sesión activa para que no se queden en pantalla
        pendientes = [p for p in db_pendientes if p["id_movimiento"] not in self.solicitudes_procesadas]

        # 1. BARRA SUPERIOR DE INDICADORES DE AUDITORÍA
        kpi_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        kpi_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        kpi_bar.grid_columnconfigure((0, 1, 2), weight=1)

        kpis = [
            (str(len(pendientes)), "Solicitudes Pendientes", "Requieren tu autorización o rechazo", COLORS["amber"] if pendientes else COLORS["green"]),
            ("100%", "Estatus de Auditoría", "Trazabilidad de justificaciones al día", COLORS["cyan"]),
            ("ACTIVO", "Circuito de Control", "Políticas oficiales de Kardex Digital", COLORS["blue"]),
        ]
        for col_idx, (num, title_kpi, sub_kpi, color_kpi) in enumerate(kpis):
            k_card = card(kpi_bar, height=72, corner_radius=14)
            k_card.grid(row=0, column=col_idx, sticky="ew", padx=6 if col_idx == 1 else 0)
            k_card.grid_propagate(False)
            ctk.CTkLabel(k_card, text=num, font=font(22, "bold"), text_color=color_kpi).pack(side="left", padx=(18, 12))
            t_box = ctk.CTkFrame(k_card, fg_color="transparent")
            t_box.pack(side="left", fill="both", expand=True, pady=12)
            ctk.CTkLabel(t_box, text=title_kpi, font=font(11, "bold"), text_color=COLORS["text"], anchor="w").pack(fill="x")
            ctk.CTkLabel(t_box, text=sub_kpi, font=font(9), text_color=COLORS["muted"], anchor="w").pack(fill="x")

        # 2. CONTENEDOR PRINCIPAL DE TARJETAS DE SOLICITUD
        main_box = card(self.content, corner_radius=16)
        main_box.grid(row=1, column=0, sticky="nsew")
        main_box.grid_rowconfigure(1, weight=1)
        main_box.grid_columnconfigure(0, weight=1)

        # Encabezado con título y botón de refrescar
        head = ctk.CTkFrame(main_box, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 12))
        head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(head, text="⚖   Bandeja de Autorización de Ajustes con Justificación",
                     font=font(16, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(head, text="Examina el motivo y la explicación detallada enviada por el encargado de bodega antes de autorizar el cambio en el Kardex.",
                     font=font(10), text_color=COLORS["muted"]).grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            head, text="⟳   Actualizar Bandeja", width=140, height=36, corner_radius=9,
            fg_color=COLORS["card_alt"], hover_color=COLORS["border"],
            border_width=1, border_color=COLORS["border"], font=font(10, "bold"),
            text_color=COLORS["text"], command=lambda: self.show_tab("approvals")
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        # Lista deslizable donde renderizo cada solicitud con su tarjeta completa
        scroll_area = ctk.CTkScrollableFrame(
            main_box, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["border"]
        )
        scroll_area.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        scroll_area.grid_columnconfigure(0, weight=1)

        if not pendientes:
            # Estado vacío elegante cuando no quedan solicitudes pendientes
            empty_box = ctk.CTkFrame(scroll_area, fg_color="transparent")
            empty_box.pack(fill="both", expand=True, pady=40)

            ctk.CTkLabel(empty_box, text="✓", font=font(40, "bold"), text_color=COLORS["mint"]).pack(pady=(0, 4))
            ctk.CTkLabel(empty_box, text="Bandeja de Auditoría al Día", font=font(18, "bold"),
                         text_color=COLORS["text"]).pack(pady=(0, 6))
            ctk.CTkLabel(empty_box,
                         text="No hay solicitudes de ajuste pendientes de revisión.\n"
                              "Todos los movimientos de inventario han sido auditados, justificados y aplicados con éxito al Kardex.",
                         font=font(11), text_color=COLORS["muted"], justify="center").pack(pady=(0, 16))
        else:
            # Dibujo cada solicitud como una tarjeta ejecutiva
            for item in pendientes:
                self._render_approval_card(scroll_area, item)

    def _render_approval_card(self, parent, item):
        """
        Aquí renderizo la tarjeta completa de solicitud de ajuste.
        Muestra la información de quién lo solicita, en qué bodega, qué producto y,
        lo más importante, LA JUSTIFICACIÓN DETALLADA DEL POR QUÉ LO SOLICITAN.
        """
        card_item = ctk.CTkFrame(parent, fg_color=COLORS["card_alt"], corner_radius=14,
                                 border_width=1, border_color=COLORS["border"])
        card_item.pack(fill="x", pady=8, padx=4)
        card_item.grid_columnconfigure(0, weight=70) # Información y justificación
        card_item.grid_columnconfigure(1, weight=30) # Decisión y botones

        # ---------------- PARTE IZQUIERDA: Metadatos y Justificación ----------------
        left_info = ctk.CTkFrame(card_item, fg_color="transparent")
        left_info.grid(row=0, column=0, sticky="nsew", padx=18, pady=16)

        # Fila superior de metadatos (Folio, Fecha, Bodega, Solicitante)
        top_meta = ctk.CTkFrame(left_info, fg_color="transparent")
        top_meta.pack(fill="x", pady=(0, 6))

        es_traslado = "TRASLADO" in str(item.get("tipo", "")).upper() or item.get("efecto") == 0
        if es_traslado:
            tipo_badge_color = COLORS["cyan"]
            tipo_badge_bg = COLORS["field"]
            tipo_sign = "⇄"
            cant_label = f" • Cantidad a trasladar: ⇄ {item['cantidad']:.1f} unidades"
        else:
            is_positive = item.get("efecto", 1) > 0
            tipo_badge_color = COLORS["green"] if is_positive else COLORS["red"]
            tipo_badge_bg = COLORS["green_bg"] if is_positive else COLORS["red_bg"]
            tipo_sign = "+" if is_positive else "-"
            cant_label = f" • Cantidad a ajustar: {tipo_sign}{item['cantidad']:.1f} unidades"

        ctk.CTkLabel(top_meta, text=f"  {tipo_sign}  {item['tipo'].upper()}  ", height=24,
                     corner_radius=6, fg_color=tipo_badge_bg, text_color=tipo_badge_color,
                     font=font(9, "bold")).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(top_meta, text=f"Folio: {item['folio']}", font=font(11, "bold"),
                     text_color=COLORS["cyan"]).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(top_meta, text=f"📅 {item['fecha']}", font=font(10),
                     text_color=COLORS["muted"]).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(top_meta, text=f"📍 {item['bodega']}", font=font(10, "bold"),
                     text_color=COLORS["text"]).pack(side="left")

        # Nombre del Producto y Cantidad Solicitada
        prod_title = ctk.CTkFrame(left_info, fg_color="transparent")
        prod_title.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(prod_title, text=f"Producto: {item['producto']} ({item['codigo']})",
                     font=font(13, "bold"), text_color=COLORS["text"], anchor="w").pack(side="left")

        ctk.CTkLabel(prod_title, text=cant_label,
                     font=font(12, "bold"), text_color=tipo_badge_color).pack(side="left", padx=8)

        # ---------------- CAJA DESTACADA: DESCRIPCIÓN DEL PORQUÉ LO SOLICITAN ----------------
        justif_box = ctk.CTkFrame(left_info, fg_color=COLORS["field"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
        justif_box.pack(fill="x", pady=(4, 0))

        # Encabezado del motivo
        justif_header = ctk.CTkFrame(justif_box, fg_color="transparent")
        justif_header.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(justif_header, text="📌  Motivo Registrado:", font=font(10, "bold"),
                     text_color=COLORS["cyan"]).pack(side="left")
        ctk.CTkLabel(justif_header, text=item["motivo"], font=font(10, "bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=6)
        ctk.CTkLabel(justif_header, text=f"|  Solicitado por: {item['solicitante']}",
                     font=font(9), text_color=COLORS["muted"]).pack(side="right")

        # Explicación detallada
        obs_text = item.get("observaciones") or "Sin justificación adicional registrada."
        ctk.CTkLabel(justif_box, text=f'"{obs_text}"', justify="left", wraplength=520,
                     font=font(10, slant="italic"), text_color=COLORS["text"], anchor="w")\
            .pack(fill="x", padx=12, pady=(2, 10))

        # ---------------- PARTE DERECHA: Botones de Decisión ----------------
        right_actions = ctk.CTkFrame(card_item, fg_color="transparent")
        right_actions.grid(row=0, column=1, sticky="nsew", padx=18, pady=16)

        ctk.CTkLabel(right_actions, text="Decisión de Auditoría", font=font(11, "bold"),
                     text_color=COLORS["muted"]).pack(pady=(0, 10))

        # Botón para Aprobar
        btn_aprobar = ctk.CTkButton(
            right_actions, text="✓   Aprobar Ajuste", height=38, corner_radius=9,
            fg_color=COLORS["green"], hover_color="#059669", text_color="#FFFFFF",
            font=font(11, "bold"),
            command=lambda it=item: self.aprobar_solicitud(it)
        )
        btn_aprobar.pack(fill="x", pady=(0, 6))

        # Botón para Rechazar
        btn_rechazar = ctk.CTkButton(
            right_actions, text="✕   Rechazar Ajuste", height=36, corner_radius=9,
            fg_color=COLORS["red"], hover_color="#DC2626", text_color="#FFFFFF",
            font=font(11, "bold"),
            command=lambda it=item: self.rechazar_solicitud(it)
        )
        btn_rechazar.pack(fill="x", pady=(0, 6))

        # Botón para ver el expediente completo
        btn_ver = ctk.CTkButton(
            right_actions, text="🔍  Ver Expediente", height=30, corner_radius=8,
            fg_color=COLORS["field"], hover_color=COLORS["border"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["cyan"], font=font(9, "bold"),
            command=lambda it=item: self.mostrar_detalle_ajuste(it)
        )
        btn_ver.pack(fill="x")

    def aprobar_solicitud(self, item):
        """Aquí ejecuto la aprobación del ajuste, impactando el stock de forma segura."""
        confirm = messagebox.askyesno(
            "Confirmar Aprobación de Ajuste",
            f"¿Deseas autorizar formalmente el ajuste '{item['folio']}'?\n\n"
            f"Producto: {item['producto']}\n"
            f"Cantidad: {item['cantidad']} unidades\n"
            f"Bodega: {item['bodega']}\n\n"
            f"Justificación: \"{item.get('observaciones')}\"\n\n"
            "Esta operación actualizará las existencias en el inventario Kardex de forma definitiva."
        )
        if not confirm:
            return

        admin_id = getattr(self.usuario, "ID_USUARIO", 1)
        ok, msg = aprobar_ajuste(item["id_movimiento"], admin_id)
        
        if ok:
            # Agrego el ID a las solicitudes procesadas para que se remueva de inmediato de la vista
            self.solicitudes_procesadas.add(item["id_movimiento"])
            messagebox.showinfo("Solicitud Aprobada", f"Operación {item['folio']} aprobada con éxito.\n{msg}\nLas existencias físicas han sido actualizadas en la base de datos.")
            self.show_tab("approvals")
        else:
            messagebox.showerror("Error al Aprobar Solicitud", f"No fue posible aprobar la solicitud {item['folio']}:\n{msg}")

    def rechazar_solicitud(self, item):
        """Aquí ejecuto el rechazo del ajuste, pidiendo el motivo del rechazo."""
        dialog = ctk.CTkInputDialog(
            title="Rechazar Solicitud",
            text=f"Ingresa el motivo del rechazo para la solicitud {item['folio']}:"
        )
        motivo = dialog.get_input()

        if motivo is None:
            return

        admin_id = getattr(self.usuario, "ID_USUARIO", 1)
        ok, msg = rechazar_ajuste(item["id_movimiento"], admin_id, motivo)
        
        if ok:
            # Agrego el ID a las solicitudes procesadas para que se remueva de inmediato de la vista
            self.solicitudes_procesadas.add(item["id_movimiento"])
            messagebox.showinfo("Solicitud Rechazada",
                                f"La solicitud {item['folio']} ha sido rechazada formalmente.\n"
                                f"Motivo asentado: {motivo or 'Rechazado por Administrador sin observaciones.'}")
            self.show_tab("approvals")
        else:
            messagebox.showerror("Error al Rechazar Ajuste", f"No fue posible procesar el rechazo:\n{msg}")

    def mostrar_detalle_ajuste(self, item):
        """Muestra una ventana modal flotante con todo el expediente del ajuste."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Expediente de Solicitud de Ajuste - {item['folio']}")
        dialog.geometry("560x520")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["app"])

        box = card(dialog, corner_radius=16)
        box.pack(fill="both", expand=True, padx=20, pady=20)

        # Título del diálogo
        ctk.CTkLabel(box, text=f"Expediente Oficial: {item['folio']}", font=font(18, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(box, text=f"Registrado el {item['fecha']} en {item['bodega']}",
                     font=font(10), text_color=COLORS["muted"]).pack(anchor="w", padx=20, pady=(0, 14))

        # Cuadro de datos técnicos
        info = ctk.CTkFrame(box, fg_color=COLORS["field"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        info.pack(fill="x", padx=20, pady=(0, 14))

        datos = [
            ("Producto Afectado", f"{item['producto']} ({item['codigo']})"),
            ("Solicitante", item["solicitante"]),
            ("Tipo de Movimiento", item["tipo"]),
            ("Cantidad Solicitada", f"{item['cantidad']} unidades"),
            ("Costo Unitario", f"Q {item.get('costo', 0):,.2f}"),
            ("Motivo Principal", item["motivo"]),
        ]
        for k, v in datos:
            f = ctk.CTkFrame(info, fg_color="transparent")
            f.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(f, text=k, font=font(9, "bold"), text_color=COLORS["muted"]).pack(side="left")
            ctk.CTkLabel(f, text=v, font=font(10, "bold"), text_color=COLORS["text"]).pack(side="right")

        # Justificación completa
        ctk.CTkLabel(box, text="Justificación del Encargado de Bodega:", font=font(11, "bold"),
                     text_color=COLORS["cyan"]).pack(anchor="w", padx=20, pady=(0, 4))

        j_box = ctk.CTkFrame(box, fg_color=COLORS["field"], corner_radius=10)
        j_box.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        ctk.CTkLabel(j_box, text=item.get("observaciones", "Sin observaciones adicionales."),
                     wraplength=480, justify="left", font=font(10, slant="italic"),
                     text_color=COLORS["text"]).pack(padx=14, pady=12, anchor="w")

        # Botón de cerrar modal
        ctk.CTkButton(
            box, text="Cerrar Expediente", height=38, corner_radius=10,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_dark"],
            font=font(11, "bold"), command=dialog.destroy
        ).pack(fill="x", padx=20, pady=(0, 18))

    # =========================================================================
    # APARTADO 4: SEGUIMIENTO DE SOLICITUDES (PARA ENCARGADOS DE BODEGA)
    # =========================================================================
    def _build_requests(self):
        """Muestra a los encargados de bodega el historial y estado de sus solicitudes."""
        self.content.grid_columnconfigure(0, weight=1, uniform="")
        self.content.grid_columnconfigure(1, weight=0, uniform="")
        self.content.grid_rowconfigure(0, weight=1)

        box = card(self.content, corner_radius=16)
        box.grid(row=0, column=0, sticky="nsew")
        box.grid_rowconfigure(2, weight=1)
        box.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(box, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 12))
        ctk.CTkLabel(head, text="📋   Seguimiento de Mis Solicitudes de Ajuste",
                     font=font(16, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(head, text="Consulta si tus solicitudes han sido autorizadas o rechazadas por el Administrador.",
                     font=font(10), text_color=COLORS["muted"]).pack(anchor="w")

        uid = getattr(self.usuario, "ID_USUARIO", None)
        historial = obtener_solicitudes_ajuste(uid)

        self._table_header(
            box, 1,
            (("Folio", 12), ("Fecha", 14), ("Bodega", 14), ("Producto", 24),
             ("Cantidad", 12), ("Motivo", 14), ("Estado", 10))
        )

        body = ctk.CTkScrollableFrame(box, fg_color="transparent", corner_radius=0,
                                      scrollbar_button_color=COLORS["border"])
        body.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        body.grid_columnconfigure(0, weight=1)

        if not historial:
            empty = ctk.CTkFrame(body, fg_color="transparent")
            empty.pack(pady=40)
            ctk.CTkLabel(empty, text="No tienes solicitudes de ajuste registradas.",
                         font=font(12), text_color=COLORS["muted"]).pack()
            return

        for idx, item in enumerate(historial):
            row = ctk.CTkFrame(body, fg_color=COLORS["card_alt"], height=48, corner_radius=10)
            row.grid(row=idx, column=0, sticky="ew", pady=3)
            row.grid_propagate(False)

            for col, weight in enumerate((12, 14, 14, 24, 12, 14, 10)):
                row.grid_columnconfigure(col, weight=weight, uniform="req_table")

            ctk.CTkLabel(row, text=item["folio"], anchor="w", font=font(10, "bold"),
                         text_color=COLORS["cyan"]).grid(row=0, column=0, sticky="ew", padx=8)
            ctk.CTkLabel(row, text=item["fecha"], anchor="w", font=font(9),
                         text_color=COLORS["muted"]).grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=item["bodega"], anchor="w", font=font(10),
                         text_color=COLORS["text"]).grid(row=0, column=2, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=item["producto"], anchor="w", font=font(10),
                         text_color=COLORS["text"]).grid(row=0, column=3, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=f"{item['cantidad']:.1f}", anchor="w", font=font(10, "bold"),
                         text_color=COLORS["text"]).grid(row=0, column=4, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=item["motivo"], anchor="w", font=font(9),
                         text_color=COLORS["muted"]).grid(row=0, column=5, sticky="ew", padx=6)

            st = item.get("estado", "EN REVISION")
            st_color = COLORS["green"] if st == "APROBADO" else (COLORS["red"] if st == "RECHAZADO" else COLORS["amber"])
            ctk.CTkLabel(row, text=st, font=font(9, "bold"), text_color=st_color).grid(row=0, column=6, sticky="w", padx=6)

    # =========================================================================
    # HELPERS Y GENERADORES DE COMPONENTES REUTILIZABLES
    # =========================================================================
    def _modern_entry(self, parent, placeholder, show="", on_change=None):
        """Crea un campo de texto moderno con bordes redondeados."""
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, show=show, height=40,
            corner_radius=10, fg_color=COLORS["field"], border_color=COLORS["border"],
            text_color=COLORS["text"], placeholder_text_color=COLORS["muted_2"], font=font(11)
        )
        entry.pack(fill="x", padx=20)
        if on_change:
            entry.bind("<KeyRelease>", on_change)
        return entry

    def _labeled_entry(self, parent, row, col, label, placeholder, show=""):
        """Crea una celda de formulario con su etiqueta y campo de texto."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=16, pady=8)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(0, 4))
        entry = ctk.CTkEntry(
            box, placeholder_text=placeholder, show=show, height=38,
            corner_radius=9, fg_color=COLORS["field"], border_color=COLORS["border"],
            text_color=COLORS["text"], font=font(11)
        )
        entry.pack(fill="x")
        return entry

    def _labeled_option(self, parent, row, col, label, values):
        """Crea un menú desplegable con su etiqueta."""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=16, pady=8)
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(0, 4))
        opt = ctk.CTkOptionMenu(
            box, values=values, height=38, corner_radius=9,
            fg_color=COLORS["field"], button_color=COLORS["card_alt"],
            button_hover_color=COLORS["border"], dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"], font=font(11)
        )
        opt.pack(fill="x")
        if values:
            opt.set(values[0])
        return opt

    def _table_header(self, parent, row, columns):
        """Genera la cabecera estilizada de las tablas de datos."""
        header = ctk.CTkFrame(parent, height=36, fg_color=COLORS["panel"], corner_radius=8)
        header.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 6))
        header.grid_propagate(False)
        for col, (title, weight) in enumerate(columns):
            header.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(header, text=title.upper(), font=font(9, "bold"),
                         text_color=COLORS["cyan"], anchor="w").grid(row=0, column=col, sticky="ew", padx=8)
