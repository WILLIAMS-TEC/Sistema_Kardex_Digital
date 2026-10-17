"""
Entidades y Modelos Relacionales del ORM SQLAlchemy.
Sistema Inventarios Kardex Digital.

En este archivo defino todas las tablas de la base de datos SQL Server:
- Control de Usuarios, Roles y Permisos.
- Catálogo Tecnológico: Productos, Categorías y Unidades de Medida.
- Almacenamiento Multi-Bodega: Bodegas y Existencias Físicas.
- Trazabilidad Transaccional: Tipos de Movimiento, Comprobantes Kardex y Detalle con Saldos.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base


class Rol(Base):
    """
    Aquí defino la tabla ROLES para categorizar los niveles de acceso al sistema:
    1 = Administrador (Control Total y Aprobaciones)
    2 = Encargado de Bodega (Operativo de Almacén y Solicitud de Ajustes)
    3 = Consultas / Supervisión (Solo Lectura y Reportes PDF)
    """
    __tablename__ = 'ROLES'
    ID_ROL = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_ROL = Column(String(50), nullable=False)
    DESCRIPCION = Column(String(200))
    
    # Relaciones ORM para navegar hacia los usuarios y sus permisos
    usuarios = relationship("Usuario", back_populates="rol")
    roles_permisos = relationship("RolPermiso", back_populates="rol")


class Usuario(Base):
    """
    Aquí defino la tabla USUARIOS donde guardo las cuentas autorizadas para operar en el Kardex.
    Incluye relaciones tanto para los movimientos que el usuario registra como para los que autoriza.
    """
    __tablename__ = 'USUARIOS'
    ID_USUARIO = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_COMPLETO = Column(String(100), nullable=False)
    CORREO = Column(String(100), unique=True, nullable=False)
    PASSW_ORD = Column(String(255), nullable=False)
    ID_ROL = Column(Integer, ForeignKey('ROLES.ID_ROL'), nullable=False)
    ESTADO = Column(Boolean, nullable=False, default=True) # 1 = ACTIVO, 0 = INACTIVO
    
    # Relaciones con roles y trazabilidad de movimientos
    rol = relationship("Rol", back_populates="usuarios")
    movimientos_registrados = relationship("MovimientoKardex", foreign_keys="[MovimientoKardex.ID_USUARIO_REGISTRO]", back_populates="usuario_registro")
    movimientos_autorizados = relationship("MovimientoKardex", foreign_keys="[MovimientoKardex.ID_USUARIO_AUTORIZA]", back_populates="usuario_autoriza")


class Permiso(Base):
    """Aquí defino la tabla PERMISOS para asignaciones granulares a nivel de función."""
    __tablename__ = 'PERMISOS'
    ID_PERMISO = Column(Integer, primary_key=True, autoincrement=True)
    CODIGO_PERMISO = Column(String(50), unique=True, nullable=False)
    NOMBRE_PERMISO = Column(String(100), nullable=False)
    
    roles_permisos = relationship("RolPermiso", back_populates="permiso")


class RolPermiso(Base):
    """Tabla asociativa para la relación muchos a muchos entre Roles y Permisos."""
    __tablename__ = 'ROLES_PERMISOS'
    ID_ROL = Column(Integer, ForeignKey('ROLES.ID_ROL'), primary_key=True)
    ID_PERMISO = Column(Integer, ForeignKey('PERMISOS.ID_PERMISO'), primary_key=True)
    
    rol = relationship("Rol", back_populates="roles_permisos")
    permiso = relationship("Permiso", back_populates="roles_permisos")


class Categoria(Base):
    """
    Aquí defino la tabla CATEGORIAS para agrupar los productos tecnológicos
    (ej. Servidores y Redes, Dispositivos y Cómputo, Periféricos y Accesorios).
    """
    __tablename__ = 'CATEGORIAS'
    ID_CATEGORIA = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_CATEGORIA = Column(String(100), nullable=False)
    DESCRIPCION = Column(String(255))
    
    productos = relationship("Producto", back_populates="categoria")


class UnidadMedida(Base):
    """
    Aquí defino la tabla UNIDADES_MEDIDA para estandarizar las magnitudes
    (ej. Unidad UN, Caja CJ, Paquete PQ).
    """
    __tablename__ = 'UNIDADES_MEDIDA'
    ID_UNIDAD = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_UNIDAD = Column(String(50), nullable=False)
    SIMBOLO = Column(String(10), nullable=False)
    
    productos = relationship("Producto", back_populates="unidad")


class Producto(Base):
    """
    Aquí defino la tabla PRODUCTOS que representa el catálogo maestro:
    - CODIGO_UNICO: Código SKU identificador único (ej. TEC-001).
    - STOCK_MINIMO: Existencia mínima de seguridad que detona alertas amarillas.
    - COSTO_PROMEDIO: Valuación monetaria del producto en Quetzales (Q).
    """
    __tablename__ = 'PRODUCTOS'
    ID_PRODUCTO = Column(Integer, primary_key=True, autoincrement=True)
    CODIGO_UNICO = Column(String(50), unique=True, nullable=False)
    DESCRIPCION_PRODUCTO = Column(String(200), nullable=False)
    ID_CATEGORIA = Column(Integer, ForeignKey('CATEGORIAS.ID_CATEGORIA'), nullable=False)
    ID_UNIDAD = Column(Integer, ForeignKey('UNIDADES_MEDIDA.ID_UNIDAD'), nullable=False)
    STOCK_MINIMO = Column(Float, nullable=False, default=0.0)
    COSTO_PROMEDIO = Column(Float, nullable=False, default=0.0)
    ESTADO = Column(Boolean, nullable=False, default=True)
    
    categoria = relationship("Categoria", back_populates="productos")
    unidad = relationship("UnidadMedida", back_populates="productos")
    existencias = relationship("ExistenciaBodega", back_populates="producto")
    detalles_kardex = relationship("DetalleKardex", back_populates="producto")


class Bodega(Base):
    """
    Aquí defino la tabla BODEGAS para gestionar múltiples almacenes
    (ej. Bodega Central de Tecnología, Bodega Sucursal Norte).
    """
    __tablename__ = 'BODEGAS'
    ID_BODEGA = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_BODEGA = Column(String(100), nullable=False)
    UBICACION = Column(String(200))
    ESTADO = Column(Boolean, nullable=False, default=True)
    
    existencias = relationship("ExistenciaBodega", back_populates="bodega")


class ExistenciaBodega(Base):
    """
    Aquí defino la tabla EXISTENCIAS_BODEGAS que vincula cada Producto con cada Bodega
    almacenando el STOCK_ACTUAL físico disponible en tiempo real.
    """
    __tablename__ = 'EXISTENCIAS_BODEGAS'
    ID_EXISTENCIA = Column(Integer, primary_key=True, autoincrement=True)
    ID_PRODUCTO = Column(Integer, ForeignKey('PRODUCTOS.ID_PRODUCTO'), nullable=False)
    ID_BODEGA = Column(Integer, ForeignKey('BODEGAS.ID_BODEGA'), nullable=False)
    STOCK_ACTUAL = Column(Float, nullable=False, default=0.0)
    
    producto = relationship("Producto", back_populates="existencias")
    bodega = relationship("Bodega", back_populates="existencias")


class TipoMovimiento(Base):
    """
    Aquí defino los TIPOS_MOVIMIENTOS y su impacto algebraico en el stock:
    - EFECTO_STOCK = 1 (Suma existencias: ENTRADA, DEVOLUCION, AJUSTE_POSITIVO)
    - EFECTO_STOCK = -1 (Resta existencias: SALIDA, AJUSTE_NEGATIVO)
    """
    __tablename__ = 'TIPOS_MOVIMIENTOS'
    ID_TIPO_MOVIMIENTO = Column(Integer, primary_key=True, autoincrement=True)
    NOMBRE_TIPO = Column(String(50), nullable=False)
    EFECTO_STOCK = Column(Integer, nullable=False)
    
    movimientos = relationship("MovimientoKardex", back_populates="tipo_movimiento")


class MotivoExcepcion(Base):
    """
    Aquí defino los MOTIVOS_EXCEPCIONES que justifican las solicitudes de ajuste
    (ej. Producto Dañado, Diferencia en Conteo Físico, Obsolescencia Tecnológica).
    """
    __tablename__ = 'MOTIVOS_EXCEPCIONES'
    ID_MOTIVO = Column(Integer, primary_key=True, autoincrement=True)
    DESCRIPCION_MOTIVO = Column(String(200), nullable=False)
    
    movimientos = relationship("MovimientoKardex", back_populates="motivo")


class MovimientoKardex(Base):
    """
    Aquí defino la cabecera del comprobante en MOVIMIENTOS_KARDEX:
    - FOLIO_COMPROBANTE: Código oficial único (ej. MOV-20261016-123).
    - ESTADO_APROBACION: 'APROBADO', 'PENDIENTE', 'RECHAZADO' o 'ANULADO'.
    - Trazabilidad completa con usuario que registra y usuario administrador que autoriza.
    """
    __tablename__ = 'MOVIMIENTOS_KARDEX'
    ID_MOVIMIENTO = Column(Integer, primary_key=True, autoincrement=True)
    FOLIO_COMPROBANTE = Column(String(50), nullable=False)
    ID_TIPO_MOVIMIENTO = Column(Integer, ForeignKey('TIPOS_MOVIMIENTOS.ID_TIPO_MOVIMIENTO'), nullable=False)
    ID_BODEGA_ORIGEN = Column(Integer, ForeignKey('BODEGAS.ID_BODEGA'), nullable=True)
    ID_BODEGA_DESTINO = Column(Integer, ForeignKey('BODEGAS.ID_BODEGA'), nullable=True)
    DOC_REFERENCIA = Column(String(100))
    ID_MOTIVO = Column(Integer, ForeignKey('MOTIVOS_EXCEPCIONES.ID_MOTIVO'), nullable=True)
    ID_USUARIO_REGISTRO = Column(Integer, ForeignKey('USUARIOS.ID_USUARIO'), nullable=False)
    FECHA_MOVIMIENTO = Column(DateTime, nullable=False)
    ESTADO_APROBACION = Column(String(20), default='APROBADO')
    ID_USUARIO_AUTORIZA = Column(Integer, ForeignKey('USUARIOS.ID_USUARIO'), nullable=True)
    FECHA_AUTORIZACION = Column(DateTime, nullable=True)
    OBSERVACIONES = Column(Text)
    
    tipo_movimiento = relationship("TipoMovimiento", back_populates="movimientos")
    bodega_origen = relationship("Bodega", foreign_keys=[ID_BODEGA_ORIGEN])
    bodega_destino = relationship("Bodega", foreign_keys=[ID_BODEGA_DESTINO])
    motivo = relationship("MotivoExcepcion", back_populates="movimientos")
    usuario_registro = relationship("Usuario", foreign_keys=[ID_USUARIO_REGISTRO], back_populates="movimientos_registrados")
    usuario_autoriza = relationship("Usuario", foreign_keys=[ID_USUARIO_AUTORIZA], back_populates="movimientos_autorizados")
    detalles = relationship("DetalleKardex", back_populates="movimiento")


class DetalleKardex(Base):
    """
    Aquí defino DETALLE_KARDEX con las partidas operadas en cada comprobante:
    Almacena la fotografía histórica del SALDO_ANTERIOR y SALDO_NUEVO
    para garantizar la auditoría y reconstrucción matemática del Kardex.
    """
    __tablename__ = 'DETALLE_KARDEX'
    ID_DETALLE = Column(Integer, primary_key=True, autoincrement=True)
    ID_MOVIMIENTO = Column(Integer, ForeignKey('MOVIMIENTOS_KARDEX.ID_MOVIMIENTO'), nullable=False)
    ID_PRODUCTO = Column(Integer, ForeignKey('PRODUCTOS.ID_PRODUCTO'), nullable=False)
    CANTIDAD = Column(Float, nullable=False)
    COSTO_UNITARIO = Column(Float, nullable=False)
    COSTO_TOTAL = Column(Float, nullable=False)
    SALDO_ANTERIOR = Column(Float, nullable=False)
    SALDO_NUEVO = Column(Float, nullable=False)
    
    movimiento = relationship("MovimientoKardex", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_kardex")
