
import customtkinter as ctk

# Aquí importo los componentes gráficos, paleta de colores y arte vectorial del tema visual
from views.ui_theme import (
    BrandLogo, COLORS, LibroKardexArt, VectorIcon, card, font, get_theme, set_theme,
)

# Configuro el modo de apariencia oscuro por defecto y el tema de color azul corporativo
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LoginWindow(ctk.CTk):

    def __init__(self):
        # Inicializo la ventana base de CustomTkinter
        
        super().__init__()
        
        # Configuro el título oficial de la aplicación y dimensiones mínimas de seguridad
        self.title("Sistema Inventarios Kardex Digital — Autenticación")
        self.minsize(1040, 680)
        
        # Asigno el color de fondo principal de la paleta oscura
        self.configure(fg_color=COLORS["app"])
        
        # Calculo y coloco la ventana centrada en la pantalla del usuario
        self._place_initial_window()

        # Variable booleana para alternar la visibilidad de la contraseña (oculta por defecto)
        self.show_password = False
        
        # Construyo la estructura de componentes visuales en pantalla
        self._build_window()
        
        # Vinculo la tecla Enter para que el usuario pueda presionar Enter y entrar directamente
        self.bind("<Return>", self.login_event)

    def _place_initial_window(self):

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(1360, max(1040, sw - 80))
        height = min(860, max(680, sh - 100))
        x, y = max(0, (sw - width) // 2), max(0, (sh - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_window(self):

        # Elimino widgets antiguos si estoy refrescando la interfaz
        for widget in self.winfo_children():
            widget.destroy()

        self.configure(fg_color=COLORS["app"])
        
        # Configuro la cuadrícula general: fila 0 (barra superior), fila 1 (tarjeta central expandible), fila 2 (pie)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # 1. Construyo la barra de encabezado superior con el logo institucional
        self._build_top_bar()

        # 2. Construyo la tarjeta central flotante con esquinas redondeadas y el formulario
        self._build_center_card()

        # 3. Construyo la barra inferior con información del sistema y selector de tema
        self._build_footer()

    def _build_top_bar(self):
        """
        Aquí creo la barra superior que contiene el logotipo del Kardex y la insignia de conexión segura.
        """
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=64)
        top_bar.grid(row=0, column=0, sticky="ew", padx=36, pady=(16, 0))
        top_bar.grid_columnconfigure(0, weight=1)

        # Muestro el logotipo oficial compacto a la izquierda
        BrandLogo(top_bar, compact=True).pack(side="left")

        # Insignia de seguridad en español con icono de candado
        sec_pill = ctk.CTkFrame(top_bar, fg_color=COLORS["panel"], corner_radius=16,
                                border_width=1, border_color=COLORS["border"])
        sec_pill.pack(side="right", pady=8)
        ctk.CTkLabel(sec_pill, text="🔒  Conexión Segura • Trazabilidad Kardex",
                     font=font(10, "bold"), text_color=COLORS["cyan"]).pack(padx=14, pady=5)

    def _build_center_card(self):
        """
        Aquí maquetado la tarjeta central dividida en 2 columnas:
        - Columna Izquierda: Ilustración vectorial del libro mayor de inventarios y ventajas.
        - Columna Derecha: Formulario interactivo de inicio de sesión con campos redondeados.
        """
        stage = ctk.CTkFrame(self, fg_color="transparent")
        stage.grid(row=1, column=0, sticky="nsew", padx=36, pady=16)
        stage.grid_columnconfigure(0, weight=1)
        stage.grid_rowconfigure(0, weight=1)

        # Tarjeta principal con bordes amplios curvados (corner_radius=22) y línea de borde fina
        master_card = ctk.CTkFrame(stage, fg_color=COLORS["card"], corner_radius=22,
                                   border_width=1, border_color=COLORS["border"])
        master_card.grid(row=0, column=0, sticky="nsew")
        master_card.grid_columnconfigure(0, weight=48, uniform="cols")  # Izquierda: 48% Arte
        master_card.grid_columnconfigure(1, weight=52, uniform="cols")  # Derecha: 52% Formulario

        # ---------------- COLUMNA IZQUIERDA: Libros e Inventario ----------------
        left_side = ctk.CTkFrame(master_card, fg_color=COLORS["sidebar"], corner_radius=20)
        left_side.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        left_side.grid_columnconfigure(0, weight=1)
        left_side.grid_rowconfigure(2, weight=1)

        # Título y encabezado informativo del lado izquierdo
        badge_row = ctk.CTkFrame(left_side, fg_color="transparent")
        badge_row.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(badge_row, text="✦  REGISTRO CONTABLE Y LOGÍSTICO",
                     font=font(10, "bold"), text_color=COLORS["cyan"]).pack(anchor="w")

        ctk.CTkLabel(left_side, text="Inventarios & Kardex", font=font(24, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=32)
        ctk.CTkLabel(left_side, text="Control Integral de Entradas, Salidas y Saldos",
                     font=font(12), text_color=COLORS["muted"], anchor="w").pack(fill="x", padx=32, pady=(2, 10))

        # Marco que contiene el dibujo vectorial del Libro Mayor de Inventarios
        art_box = ctk.CTkFrame(left_side, fg_color=COLORS["panel"], corner_radius=14,
                               border_width=1, border_color=COLORS["border_soft"])
        art_box.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        LibroKardexArt(art_box, bg=COLORS["panel"], height=200).pack(fill="both", expand=True, padx=8, pady=8)

        # Micro-tarjetas que resumen las 3 capacidades clave del software
        features_frame = ctk.CTkFrame(left_side, fg_color="transparent")
        features_frame.pack(fill="x", padx=28, pady=(0, 24))

        features = [
            ("📖", "Libro Mayor Kardex", "Valuación por PEPS y Promedio"),
            ("📦", "Control de Existencias", "Gestión multi-bodega con stock mínimo"),
            ("🛡️", "Auditoría Transaccional", "Aprobación de ajustes y trazabilidad"),
        ]
        for icon, title, desc in features:
            f_card = ctk.CTkFrame(features_frame, fg_color=COLORS["card_alt"], corner_radius=10, height=44)
            f_card.pack(fill="x", pady=3)
            f_card.pack_propagate(False)
            ctk.CTkLabel(f_card, text=icon, font=font(14), width=32).pack(side="left", padx=(8, 4))
            t_box = ctk.CTkFrame(f_card, fg_color="transparent")
            t_box.pack(side="left", fill="both", expand=True, pady=4)
            ctk.CTkLabel(t_box, text=title, font=font(10, "bold"), text_color=COLORS["text"], anchor="w").pack(fill="x")
            ctk.CTkLabel(t_box, text=desc, font=font(9), text_color=COLORS["muted"], anchor="w").pack(fill="x")

        # ---------------- COLUMNA DERECHA: Formulario de Acceso ----------------
        right_side = ctk.CTkFrame(master_card, fg_color="transparent")
        right_side.grid(row=0, column=1, sticky="nsew", padx=36, pady=28)
        right_side.grid_columnconfigure(0, weight=1)

        # Encabezado con tipografía clara y moderna
        ctk.CTkLabel(right_side, text="P O R T A L   D E   A C C E S O", font=font(11, "bold"),
                     text_color=COLORS["blue"]).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(right_side, text="Iniciar Sesión", font=font(30, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(right_side, text="Ingresa tus credenciales autorizadas para gestionar inventarios.",
                     font=font(12), text_color=COLORS["muted"], anchor="w").pack(fill="x", pady=(2, 22))

        # Campo para ingresar el usuario o correo
        ctk.CTkLabel(right_side, text="Usuario o Correo Electrónico", font=font(11, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(0, 4))
        self.entry_email = self._create_input_field(right_side, "user", "Ej. Williams o usuario@kardex.com")

        # Campo para ingresar la contraseña con icono de candado
        ctk.CTkLabel(right_side, text="Contraseña de Acceso", font=font(11, "bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", pady=(14, 4))
        self.entry_password = self._create_input_field(right_side, "lock", "Ingresa tu contraseña", password=True)

        # Etiqueta para mostrar mensajes de error si la contraseña o usuario no son válidos
        self.label_error = ctk.CTkLabel(right_side, text="", height=22, font=font(11), text_color=COLORS["red"], anchor="w")
        self.label_error.pack(fill="x", pady=(6, 8))

        # Botón principal de acceso con color azul zafiro y flecha interactiva
        self.button_login = ctk.CTkButton(
            right_side, text="Acceder al Kardex Digital                         →",
            height=52, corner_radius=12, fg_color=COLORS["blue"],
            hover_color=COLORS["blue_dark"], text_color="#FFFFFF", font=font(14, "bold"),
            command=self.login_event
        )
        self.button_login.pack(fill="x", pady=(0, 16))

        # Mensaje de ayuda para demostración rápida y evaluación académica
        demo_box = ctk.CTkFrame(right_side, fg_color=COLORS["field"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
        demo_box.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(demo_box, text="💡  Credencial por defecto: Usuario: Williams   •   Clave: admin123",
                     font=font(10), text_color=COLORS["muted"]).pack(padx=14, pady=8)

        # Separador estético de seguridad
        ctk.CTkFrame(right_side, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=(6, 10))
        ctk.CTkLabel(right_side, text="Sistema restringido a operadores autorizados • Auditoría activa",
                     font=font(10), text_color=COLORS["muted_2"]).pack(anchor="w")

    def _create_input_field(self, parent, icon_kind, placeholder, password=False):
        """
        En este método fabrico una celda de texto elegante y redondeada,
        con un icono vectorial a la izquierda y un botón de ver/ocultar contraseña a la derecha si aplica.
        """
        shell = ctk.CTkFrame(parent, height=52, corner_radius=12,
                             fg_color=COLORS["field"], border_width=1,
                             border_color=COLORS["border"])
        shell.pack(fill="x")
        shell.pack_propagate(False)

        # Coloco el icono vectorial correspondiente (usuario o candado)
        VectorIcon(shell, icon_kind, size=24, bg=COLORS["field"], fg=COLORS["muted"]).pack(side="left", padx=(14, 8))

        # Caja de texto sin bordes nativos para que adopte la forma del contenedor redondeado
        entry = ctk.CTkEntry(
            shell, placeholder_text=placeholder,
            show="" if password and self.show_password else ("●" if password else ""),
            height=46, corner_radius=0, fg_color="transparent",
            border_width=0, text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_2"], font=font(13)
        )
        entry.pack(side="left", fill="both", expand=True, pady=2)

        # Si es campo de contraseña, agrego el icono de ojito interactivo para alternar texto plano / oculto
        if password:
            VectorIcon(shell, "eye", size=24, bg=COLORS["field"], fg=COLORS["muted"],
                       command=self.toggle_password).pack(side="right", padx=(8, 14))

        return entry

    def _build_footer(self):
        """
        Aquí construyo el pie de página inferior con la versión del software y el selector de tema visual.
        """
        footer = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0, height=52,
                              border_width=1, border_color=COLORS["border_soft"])
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(footer, text="Sistema Inventarios Kardex Digital   •   Versión 3.2.0 Corporativa",
                     font=font(10, "bold"), text_color=COLORS["muted"]).pack(side="left", padx=36)

        theme_box = ctk.CTkFrame(footer, fg_color="transparent")
        theme_box.pack(side="right", padx=36)
        ctk.CTkLabel(theme_box, text="Tema Visual:", font=font(10), text_color=COLORS["muted"]).pack(side="left", padx=(0, 8))

        # Menú desplegable para alternar entre Dark y Light
        self.theme_selector = ctk.CTkOptionMenu(
            theme_box, values=["Dark", "Light"], width=94, height=28, corner_radius=8,
            fg_color=COLORS["card"], button_color=COLORS["card_alt"],
            button_hover_color=COLORS["border"], dropdown_fg_color=COLORS["card"],
            text_color=COLORS["text"], font=font(10, "bold"), command=self.change_theme
        )
        self.theme_selector.set(get_theme())
        self.theme_selector.pack(side="left")

    def toggle_password(self):
        """Alterno entre mostrar y ocultar los caracteres de la contraseña."""
        self.show_password = not self.show_password
        self.entry_password.configure(show="" if self.show_password else "●")

    def change_theme(self, selected):
        """Cambio dinámico del tema de color (Dark / Light) preservando lo que el usuario haya escrito."""
        email = self.entry_email.get() if hasattr(self, "entry_email") else ""
        password = self.entry_password.get() if hasattr(self, "entry_password") else ""
        set_theme(selected)
        self._build_window()
        self.entry_email.insert(0, email)
        self.entry_password.insert(0, password)

    def login_event(self, _event=None):
        """
        En este método proceso la autenticación:
        1. Leo y limpio los campos de usuario y contraseña.
        2. Valido que no vengan vacíos.
        3. Llamo al controlador de autenticación (auth_ctrl).
        4. Si es correcto, oculto la ventana de login y abro el Dashboard principal.
        """
        email = self.entry_email.get().strip()
        password = self.entry_password.get()
        if not email or not password:
            self.label_error.configure(text="Por favor ingresa tu usuario y contraseña.")
            return

        # Deshabilito temporalmente el botón para prevenir doble clic
        self.button_login.configure(state="disabled", text="Verificando en Kardex Digital...")
        self.label_error.configure(text="")
        self.update_idletasks()

        # Importo los controladores necesarios para validar contra la base de datos
        from controllers.auth_ctrl import authenticate_user, get_user_role
        from views.main_dashboard import MainDashboard

        usuario, mensaje = authenticate_user(email, password)
        if usuario:
            # Obtengo el rol (Administrador, Encargado de Bodega, Consultas)
            rol = get_user_role(usuario)
            try:
                # Oculto la ventana de login
                self.withdraw()
                # Lanzo la vista del Dashboard principal con la sesión activa
                MainDashboard(self, usuario, rol)
            except Exception as exc:
                self.deiconify()
                self.label_error.configure(text=f"Error iniciando sesión: {exc}")
                self.button_login.configure(state="normal", text="Acceder al Kardex Digital                         →")
        else:
            # Si falló la contraseña o el usuario, muestro el error en pantalla
            self.label_error.configure(text=mensaje)
            self.button_login.configure(state="normal", text="Acceder al Kardex Digital                         →")


# Punto de entrada principal cuando ejecuto python main.py
if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
