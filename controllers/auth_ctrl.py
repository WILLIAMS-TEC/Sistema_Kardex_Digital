"""
Controlador de Autenticación y Autorización de Roles.
Sistema Inventarios Kardex Digital.

En este controlador implemento la lógica de acceso al sistema:
- Búsqueda flexible de usuarios en SQL Server por correo institucional, nombre completo o primer nombre (ej. Allan, Ritha, Williams).
- Validación de contraseña contra la base de datos.
- Determinación de roles y permisos (Administrador, Encargado de Bodega, Consultas).
- Sesiones de contingencia offline con soporte para todos los roles del sistema.
"""

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from models.database import get_session
from models.entities import Usuario, Rol


class MockUserSession:
    """
    En esta clase defino un objeto de usuario simulado en memoria para contingencias,
    permitiendo ingresar y probar la aplicación con cualquier rol incluso sin SQL Server activo.
    """
    def __init__(self, id_usuario, nombre, correo, rol_nombre, id_rol=1):
        self.ID_USUARIO = id_usuario
        self.NOMBRE_COMPLETO = nombre
        self.CORREO = correo
        self.PASSW_ORD = "12345"
        self.ID_ROL = id_rol
        self.ESTADO = True
        self.rol_nombre = rol_nombre


# Cuentas preconfiguradas para contingencia offline (cuando SQL Server no esté conectado)
DEMO_OFFLINE_USERS = {
    "williams": {"id": 1, "nombre": "WILLIAMS SEQUEN", "correo": "SEQUENW7@GMAIL.COM", "rol": "ADMINISTRADOR", "id_rol": 1, "pass": ("12345", "admin123")},
    "alan": {"id": 2, "nombre": "ALLAN GEOVANI ITZOL", "correo": "ALANGEO@GMAIL.COM", "rol": "ENCARGADO DE BODEGA", "id_rol": 2, "pass": ("12345", "admin123")},
    "allan": {"id": 2, "nombre": "ALLAN GEOVANI ITZOL", "correo": "ALANGEO@GMAIL.COM", "rol": "ENCARGADO DE BODEGA", "id_rol": 2, "pass": ("12345", "admin123")},
    "ritha": {"id": 3, "nombre": "RITHA LUCIA CASTAÑEDA", "correo": "RITHA123@GMAIL.COM", "rol": "CONSULTA / SUPERVISION", "id_rol": 3, "pass": ("12345", "admin123")},
    "rita": {"id": 3, "nombre": "RITHA LUCIA CASTAÑEDA", "correo": "RITHA123@GMAIL.COM", "rol": "CONSULTA / SUPERVISION", "id_rol": 3, "pass": ("12345", "admin123")},
}


def _match_offline_user(clean_id, clean_pw):
    """Verifico si las credenciales coinciden con las cuentas de contingencia offline."""
    id_lower = clean_id.lower()
    for key, data in DEMO_OFFLINE_USERS.items():
        if (id_lower == key or id_lower == data["correo"].lower() or id_lower in data["nombre"].lower()):
            if clean_pw in data["pass"] or clean_pw == "12345":
                return MockUserSession(data["id"], data["nombre"], data["correo"], data["rol"], data["id_rol"]), "Login exitoso (Modo Autónomo)"
    return None, None


def authenticate_user(identifier, password):
    """
    Con esta función autentico al usuario contra la base de datos SQL Server:
    - Búsqueda flexible: Correo exacto, Nombre completo, primer nombre o nombre de usuario.
    - Soporte para nombres con variaciones (ej. 'alan' encuentra a 'ALLAN GEOVANI ITZOL', 'ritha' a 'RITHA LUCIA CASTAÑEDA').
    - Verifico que el usuario esté ACTIVO (ESTADO == True).
    - Comparo la contraseña ingresada.
    - En caso de falla de base de datos, recurro a la sesión de contingencia por roles.
    """
    clean_id = (identifier or "").strip()
    clean_pw = (password or "").strip()
    id_lower = clean_id.lower()

    if not clean_id or not clean_pw:
        return None, "Por favor ingresa usuario y contraseña."

    session = get_session()

    # Si la base de datos no está disponible, verifico el modo de contingencia offline
    if not session:
        mock_usr, mock_msg = _match_offline_user(clean_id, clean_pw)
        if mock_usr:
            return mock_usr, mock_msg
        return None, "Servidor de base de datos no disponible. Puede usar Williams, Alan o Ritha con clave 12345."

    try:
        # Traigo todos los usuarios activos de la base de datos con su rol cargado
        usuarios_activos = session.query(Usuario).options(joinedload(Usuario.rol)).filter(
            Usuario.ESTADO == True
        ).all()

        usuario_encontrado = None

        # 1. Búsqueda por coincidencia exacta de correo o nombre completo
        for u in usuarios_activos:
            u_correo = (u.CORREO or "").strip().lower()
            u_nombre = (u.NOMBRE_COMPLETO or "").strip().lower()
            if id_lower == u_correo or id_lower == u_nombre:
                usuario_encontrado = u
                break

        # 2. Si no hubo coincidencia exacta, busco por primer nombre o parte del correo
        if not usuario_encontrado:
            # Diccionario de alias comunes para facilitar el acceso
            aliases = {
                "alan": "allan",
                "allan": "allan",
                "ritha": "ritha",
                "rita": "ritha",
                "williams": "williams",
                "william": "williams",
            }
            target_key = aliases.get(id_lower, id_lower)

            for u in usuarios_activos:
                u_correo = (u.CORREO or "").strip().lower()
                u_nombre = (u.NOMBRE_COMPLETO or "").strip().lower()
                u_first = u_nombre.split()[0] if u_nombre else ""
                u_email_user = u_correo.split("@")[0] if "@" in u_correo else u_correo

                # Coincidencia con el primer nombre (o su alias) o con el prefijo del correo
                if (target_key == u_first or 
                    target_key == u_email_user or 
                    u_first.startswith(target_key) or 
                    target_key in u_nombre or
                    id_lower in u_correo):
                    usuario_encontrado = u
                    break

        # Si no lo encuentro en la base de datos activa, verifico contingencia offline
        if not usuario_encontrado:
            mock_usr, mock_msg = _match_offline_user(clean_id, clean_pw)
            if mock_usr:
                return mock_usr, mock_msg
            return None, "Usuario no encontrado o inactivo en el sistema."

        # Verifico si la contraseña coincide exactamente
        if (usuario_encontrado.PASSW_ORD == clean_pw) or (usuario_encontrado.PASSW_ORD == password):
            usuario_encontrado.rol_nombre = usuario_encontrado.rol.NOMBRE_ROL.upper() if usuario_encontrado.rol else "ADMINISTRADOR"
            return usuario_encontrado, "Login exitoso"
        else:
            return None, "Contraseña incorrecta."

    except Exception as exc:
        # En caso de error inesperado en la consulta SQL, activo el fallback
        mock_usr, mock_msg = _match_offline_user(clean_id, clean_pw)
        if mock_usr:
            return mock_usr, "Login exitoso (Modo Contingencia)"
        return None, f"Error en la autenticación: {str(exc)}"
    finally:
        session.close()


def get_user_role(usuario):
    """
    Aquí determino el nombre del rol del usuario para configurar
    los accesos y permisos correspondientes en el dashboard.
    """
    if not usuario:
        return "DESCONOCIDO"

    # Si ya lo tengo en memoria, lo retorno directamente
    cached = getattr(usuario, "rol_nombre", None)
    if cached:
        return cached

    session = get_session()
    if not session:
        role_id = getattr(usuario, "ID_ROL", 1)
        if role_id == 1: return "ADMINISTRADOR"
        elif role_id == 2: return "ENCARGADO DE BODEGA"
        elif role_id == 3: return "CONSULTA / SUPERVISION"
        return "ADMINISTRADOR"

    try:
        rol = session.query(Rol).filter(Rol.ID_ROL == usuario.ID_ROL).first()
        nombre = rol.NOMBRE_ROL.upper() if rol else "ADMINISTRADOR"
        usuario.rol_nombre = nombre
        return nombre
    except Exception:
        return "ADMINISTRADOR"
    finally:
        session.close()


def is_admin_role(role_name, role_id=None):
    """Valido si el usuario tiene privilegios de Administrador (ID_ROL == 1)."""
    if role_id == 1:
        return True
    name = (role_name or "").upper().strip()
    return "ADMIN" in name and "SUB" not in name and "ENCARGADO" not in name


def is_warehouse_manager_role(role_name, role_id=None):
    """Valido si el usuario es Encargado de Bodega (ID_ROL == 2)."""
    if role_id == 2:
        return True
    name = (role_name or "").upper().strip()
    return any(k in name for k in ("BODEGA", "JEFE", "ENCARGADO", "SUPERVISOR", "OPERADOR"))


def is_consultas_role(role_name, role_id=None):
    """Valido si el usuario tiene rol de Consultas / Solo Lectura (ID_ROL == 3)."""
    if role_id == 3:
        return True
    name = (role_name or "").upper().strip()
    return any(k in name for k in ("CONSULTA", "SUPERVISION", "LECTURA", "VIEWER", "AUDITOR"))
