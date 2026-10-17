"""
Configuración de la Base de Datos y Motor SQLAlchemy.
Sistema Inventarios Kardex Digital.

Aquí configuro la conexión con Microsoft SQL Server mediante ODBC,
la clase Base declarativa para el ORM y la fábrica de sesiones (SessionLocal).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------
# PARÁMETROS DE CONEXIÓN A SQL SERVER
# ---------------------------------------------------------
# Aquí defino el nombre de la instancia local de SQL Server y la base de datos oficial
SERVER = r'LOQ-WILLIAMS\SQLEXPRESS' # También compatible con 'localhost\\SQLEXPRESS'
DATABASE = 'KARDEX'

# Cadena de conexión utilizando el controlador oficial ODBC Driver 17 y autenticación integrada de Windows
CONNECTION_STRING = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

# Clase base declarativa que heredarán todas las entidades del modelo relacional
Base = declarative_base()

try:
    # Creo el motor de base de datos con SQLAlchemy (echo=False para mantener limpia la consola)
    engine = create_engine(CONNECTION_STRING, echo=False)
    # Fábrica de sesiones configurada con autocommit=False para garantizar transacciones ACID
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    # Si no se logra conectar con SQL Server, guardo None para activar el modo offline
    print(f"Error inicializando el motor de BD: {e}")
    SessionLocal = None


def get_session():
    """
    En esta función creo y retorno una nueva sesión transaccional de base de datos.
    Si el motor no se pudo inicializar, retorno None para permitir el modo demostrativo.
    """
    if SessionLocal:
        return SessionLocal()
    return None
