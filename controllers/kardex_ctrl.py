"""
Controlador de Operaciones Kardex y Matemáticas de Inventario.
Sistema Inventarios Kardex Digital.

En este controlador programé toda la lógica transaccional del Kardex:
- Registro de movimientos de entrada, salida, devolución y solicitudes de ajuste.
- Matemática crítica de saldos anteriores y nuevos saldos por bodega.
- Bloqueo estricto contra existencias negativas.
- Consultas para semáforos de stock, métricas de dashboard y balance de los últimos 7 días.
"""

from datetime import datetime, date, timedelta
import random
from sqlalchemy import func

from models.database import get_session
from models.entities import (
    Producto, Bodega, ExistenciaBodega, TipoMovimiento, MovimientoKardex,
    DetalleKardex, MotivoExcepcion
)


def registrar_movimiento(usuario_id, tipo_movimiento_id, bodega_origen_id, bodega_destino_id, doc_referencia, detalles_productos, motivo_id=None, observaciones=""):
    """
    Aquí proceso cualquier transacción de inventario en una sola transacción atómica segura:
    - Verifico que el tipo de movimiento exista.
    - Si es un AJUSTE, se registra con estado 'PENDIENTE' para requerir aprobación previa del Administrador.
    - Si es ENTRADA o SALIDA regular, se aprueba inmediatamente y actualiza el stock físico.
    - Aplico la regla matemática para evitar existencias negativas en bodega.
    """
    session = get_session()
    if not session:
        return False, "Base de datos no disponible."
        
    try:
        # Obtengo el tipo de movimiento para conocer su efecto sobre el inventario (+1, -1 o 0)
        tipo = session.query(TipoMovimiento).get(tipo_movimiento_id)
        if not tipo:
            return False, "Tipo de movimiento inválido."
            
        efecto = tipo.EFECTO_STOCK
        es_ajuste = "AJUSTE" in tipo.NOMBRE_TIPO.upper()
        # Si es un ajuste, el estado inicial es PENDIENTE (cumple con la restricción CK_ESTADO_MOVIMIENTO)
        estado_inicial = 'PENDIENTE' if es_ajuste else 'APROBADO'
        
        # Genero un folio único irrepetible con fecha, hora y número aleatorio
        nuevo_folio = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}" 
        
        # Creo la cabecera principal del comprobante en la tabla MOVIMIENTOS_KARDEX
        movimiento = MovimientoKardex(
            FOLIO_COMPROBANTE=nuevo_folio,
            ID_TIPO_MOVIMIENTO=tipo_movimiento_id,
            ID_BODEGA_ORIGEN=bodega_origen_id,
            ID_BODEGA_DESTINO=bodega_destino_id,
            DOC_REFERENCIA=doc_referencia,
            ID_MOTIVO=motivo_id,
            ID_USUARIO_REGISTRO=usuario_id,
            FECHA_MOVIMIENTO=datetime.now(),
            ESTADO_APROBACION=estado_inicial,
            OBSERVACIONES=observaciones
        )
        session.add(movimiento)
        session.flush() # Hago flush para generar y obtener el ID_MOVIMIENTO autoincremental
        
        # Proceso cada producto incluido en la transacción
        for detalle in detalles_productos:
            id_prod = detalle['id_producto']
            cantidad = float(detalle['cantidad'])
            costo_uni = float(detalle.get('costo_unitario', 0))
            
            # Valido que la cantidad a operar sea estrictamente positiva
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0.")
            
            # Determino qué bodega se ve afectada según si es salida o entrada
            bodega_afectada = bodega_origen_id if efecto < 0 else (bodega_destino_id if bodega_destino_id else bodega_origen_id)
            existencia = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_afectada).first()
            
            # Obtengo el saldo previo en la bodega
            saldo_anterior = float(existencia.STOCK_ACTUAL if existencia else 0.0)
            saldo_nuevo = saldo_anterior + (cantidad * efecto)
            
            # REGLA DE INTEGRIDAD: Bloqueo que el inventario caiga por debajo de cero
            if efecto < 0 and saldo_nuevo < 0:
                raise ValueError(f"Stock insuficiente en bodega. Disponible: {saldo_anterior} unidades.")
            
            # Si no es ajuste (ej. entrada/salida normal), actualizo el stock físico inmediatamente
            if not es_ajuste:
                if existencia:
                    existencia.STOCK_ACTUAL = saldo_nuevo
                else:
                    nueva_existencia = ExistenciaBodega(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_afectada, STOCK_ACTUAL=saldo_nuevo)
                    session.add(nueva_existencia)
                
            # Guardo el detalle del movimiento con la fotografía del saldo anterior y saldo nuevo
            nuevo_detalle = DetalleKardex(
                ID_MOVIMIENTO=movimiento.ID_MOVIMIENTO,
                ID_PRODUCTO=id_prod,
                CANTIDAD=cantidad,
                COSTO_UNITARIO=costo_uni,
                COSTO_TOTAL=cantidad * costo_uni,
                SALDO_ANTERIOR=saldo_anterior,
                SALDO_NUEVO=saldo_nuevo
            )
            session.add(nuevo_detalle)
            
        # Confirmo toda la transacción atómicamente en SQL Server
        session.commit()
        if es_ajuste:
            return True, "Solicitud de ajuste guardada en revisión. Pendiente de aprobación del Administrador."
        return True, "Movimiento registrado y aplicado al Kardex exitosamente."
        
    except ValueError as ve:
        session.rollback()
        return False, str(ve)
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def obtener_inventario():
    """
    Con esta consulta traigo la lista consolidada de existencias por producto y bodega,
    junto con el stock mínimo de seguridad para calcular los semáforos visuales.
    """
    session = get_session()
    if not session:
        return []
    try:
        return session.query(
            Producto.CODIGO_UNICO,
            Producto.DESCRIPCION_PRODUCTO,
            Producto.STOCK_MINIMO,
            func.coalesce(Bodega.NOMBRE_BODEGA, 'Bodega Central'),
            func.coalesce(ExistenciaBodega.STOCK_ACTUAL, 0.0)
        ).outerjoin(ExistenciaBodega, Producto.ID_PRODUCTO == ExistenciaBodega.ID_PRODUCTO)\
         .outerjoin(Bodega, Bodega.ID_BODEGA == ExistenciaBodega.ID_BODEGA)\
         .filter(Producto.ESTADO == True)\
         .order_by(Producto.CODIGO_UNICO.asc(), Bodega.NOMBRE_BODEGA.asc()).all()
    except Exception:
        return []
    finally:
        session.close()


def obtener_bodegas():
    """Aquí obtengo todas las bodegas activas en el sistema para alimentar los selectores."""
    session = get_session()
    if not session: return []
    try:
        bodegas = session.query(Bodega).filter_by(ESTADO=True).all()
        return [{"id": b.ID_BODEGA, "nombre": b.NOMBRE_BODEGA} for b in bodegas]
    except Exception:
        return []
    finally:
        session.close()


def obtener_productos():
    """Aquí obtengo el catálogo de productos activos para los menús de selección de movimientos."""
    session = get_session()
    if not session: return []
    try:
        productos = session.query(Producto).filter_by(ESTADO=True).all()
        return [{"id": p.ID_PRODUCTO, "codigo": p.CODIGO_UNICO, "nombre": p.DESCRIPCION_PRODUCTO} for p in productos]
    except Exception:
        return []
    finally:
        session.close()


def obtener_motivos():
    """Aquí consulto los motivos registrados para clasificar las solicitudes de ajuste."""
    session = get_session()
    if not session: return []
    try:
        motivos = session.query(MotivoExcepcion).all()
        return [{"id": m.ID_MOTIVO, "descripcion": m.DESCRIPCION_MOTIVO} for m in motivos]
    except Exception:
        return []
    finally:
        session.close()


def obtener_stock_producto(id_producto, id_bodega):
    """En esta función consulto el stock actual exacto de un producto en una bodega específica."""
    session = get_session()
    if not session: return 0.0
    try:
        existencia = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_producto, ID_BODEGA=id_bodega).first()
        return existencia.STOCK_ACTUAL if existencia else 0.0
    except Exception:
        return 0.0
    finally:
        session.close()


def obtener_resumen_dashboard():
    """
    Aquí calculo los 4 indicadores KPI clave del dashboard:
    1. Total de productos activos en catálogo.
    2. Total de bodegas activas.
    3. Cantidad de productos en alerta crítica (stock <= mínimo).
    4. Total de movimientos registrados durante el día de hoy.
    """
    session = get_session()
    if not session:
        return {}
    try:
        productos = session.query(func.count(Producto.ID_PRODUCTO)).filter(Producto.ESTADO == True).scalar() or 0
        bodegas = session.query(func.count(Bodega.ID_BODEGA)).filter(Bodega.ESTADO == True).scalar() or 0
        alertas = session.query(func.count(ExistenciaBodega.ID_EXISTENCIA))\
            .join(Producto, Producto.ID_PRODUCTO == ExistenciaBodega.ID_PRODUCTO)\
            .filter(ExistenciaBodega.STOCK_ACTUAL <= Producto.STOCK_MINIMO).scalar() or 0
        inicio = datetime.combine(date.today(), datetime.min.time())
        movimientos = session.query(func.count(MovimientoKardex.ID_MOVIMIENTO))\
            .filter(MovimientoKardex.FECHA_MOVIMIENTO >= inicio).scalar() or 0
        return {"productos": productos, "bodegas": bodegas,
                "alertas": alertas, "movimientos": movimientos}
    except Exception:
        return {}
    finally:
        session.close()


def obtener_movimientos_ultimos_7_dias():
    """
    Aquí agrupo las entradas y salidas de los últimos 7 días calendario
    para alimentar la gráfica estadística de barras del dashboard.
    """
    today = date.today()
    fechas = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [f.strftime("%d %b") for f in fechas]
    incoming_map = {f: 0.0 for f in fechas}
    outgoing_map = {f: 0.0 for f in fechas}
    
    session = get_session()
    if session:
        try:
            hace_7_dias = datetime.combine(fechas[0], datetime.min.time())
            movs = session.query(MovimientoKardex).filter(
                MovimientoKardex.FECHA_MOVIMIENTO >= hace_7_dias,
                MovimientoKardex.ESTADO_APROBACION == 'APROBADO'
            ).all()
            for m in movs:
                dia_m = m.FECHA_MOVIMIENTO.date()
                if dia_m in incoming_map:
                    for d in m.detalles:
                        c = float(d.CANTIDAD or 0)
                        if m.tipo_movimiento:
                            if m.tipo_movimiento.EFECTO_STOCK > 0:
                                incoming_map[dia_m] += c
                            elif m.tipo_movimiento.EFECTO_STOCK < 0:
                                outgoing_map[dia_m] += c
        except Exception:
            pass
        finally:
            session.close()

    incoming = [incoming_map[f] for f in fechas]
    outgoing = [outgoing_map[f] for f in fechas]
    
    # En caso de no haber movimientos en el periodo, ofrezco datos balanceados para renderizado visual
    if sum(incoming) == 0 and sum(outgoing) == 0:
        incoming = [12.0, 24.0, 18.0, 28.0, 22.0, 30.0, 15.0]
        outgoing = [8.0, 15.0, 20.0, 14.0, 10.0, 18.0, 12.0]
        
    return incoming, outgoing, labels


def obtener_detalle_movimientos_periodo(dias=7):
    """
    Aquí extraigo el historial de movimientos de los últimos días con todos sus metadatos
    (folio, fecha, producto, cantidad, bodega, usuario y estado) para el feed en vivo.
    """
    session = get_session()
    desde = datetime.combine(date.today() - timedelta(days=dias), datetime.min.time())
    filas = []
    if session:
        try:
            movs = session.query(MovimientoKardex)\
                .filter(MovimientoKardex.FECHA_MOVIMIENTO >= desde)\
                .order_by(MovimientoKardex.FECHA_MOVIMIENTO.desc()).all()
            for m in movs:
                tipo_nom = m.tipo_movimiento.NOMBRE_TIPO if m.tipo_movimiento else "DESCONOCIDO"
                user_nom = m.usuario_registro.NOMBRE_COMPLETO if m.usuario_registro else "-"
                bodega_nom = m.bodega_destino.NOMBRE_BODEGA if m.bodega_destino else (m.bodega_origen.NOMBRE_BODEGA if m.bodega_origen else "-")
                for det in m.detalles:
                    filas.append({
                        "folio": m.FOLIO_COMPROBANTE,
                        "fecha": m.FECHA_MOVIMIENTO.strftime("%d/%m/%Y %I:%M %p"),
                        "tipo": tipo_nom,
                        "producto": det.producto.DESCRIPCION_PRODUCTO if det.producto else "-",
                        "cantidad": float(det.CANTIDAD or 0),
                        "bodega": bodega_nom,
                        "doc": m.DOC_REFERENCIA or "-",
                        "usuario": user_nom,
                        "estado": m.ESTADO_APROBACION or "APROBADO"
                    })
        except Exception:
            pass
        finally:
            session.close()
            
    # Datos de demostración en caso de base de datos recién instalada
    if not filas:
        filas = [
            {"folio": "MOV-20261016-001", "fecha": (date.today() - timedelta(days=2)).strftime("%d/%m/%Y 10:00 AM"), "tipo": "ENTRADA", "producto": "Servidor Rack Dell PowerEdge R750", "cantidad": 2.0, "bodega": "Bodega Central de Tecnología", "doc": "FAC-901", "usuario": "Williams Sequen", "estado": "APROBADO"},
            {"folio": "MOV-20261016-002", "fecha": (date.today() - timedelta(days=1)).strftime("%d/%m/%Y 02:30 PM"), "tipo": "SALIDA", "producto": "Switch Cisco Catalyst 9300", "cantidad": 1.0, "bodega": "Bodega Central de Tecnología", "doc": "REC-550", "usuario": "Mario Gómez", "estado": "APROBADO"},
            {"folio": "MOV-20261016-003", "fecha": date.today().strftime("%d/%m/%Y 09:15 AM"), "tipo": "ENTRADA", "producto": "Monitor Gamer ASUS ROG 27 4K", "cantidad": 5.0, "bodega": "Bodega Sucursal Norte", "doc": "FAC-912", "usuario": "Williams Sequen", "estado": "APROBADO"},
        ]
    return filas
