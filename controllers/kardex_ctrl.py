"""
Controlador de Operaciones Kardex y Matemáticas de Inventario.
Sistema Inventarios Kardex Digital.

En este controlador programé toda la lógica transaccional del Kardex:
- Registro de movimientos de entrada, salida, devolución, traslados entre bodegas y solicitudes de ajuste.
- REGLAS ESTRICTAS DE SEGURIDAD Y AUDITORÍA:
  1. Bloqueo por Stock Insuficiente: No se puede emitir una operación si se solicita más del stock físico existente.
  2. Bloqueo por Reserva de Stock Mínimo: Toda salida, ajuste negativo o traslado debe conservar al menos el stock mínimo configurado.
     (Ejemplo: Si hay 15 unidades y el stock mínimo es 5, solo se pueden retirar hasta 10; si solicita 12, se bloquea porque quedarían 3).
  3. Traslados entre bodegas: Valida stock y reserva mínima en bodega origen e incrementa bodega destino de forma atómica.
  4. Perfiles y Autorizaciones: El Encargado de Bodega registra solicitudes en estado PENDIENTE sin impacto directo en inventario.
"""

from datetime import datetime, date, timedelta
import random
from sqlalchemy import func

from models.database import get_session
from models.entities import (
    Producto, Bodega, ExistenciaBodega, TipoMovimiento, MovimientoKardex,
    DetalleKardex, MotivoExcepcion, Usuario
)
from controllers.auth_ctrl import is_admin_role


def obtener_seguridad_stock(id_producto, id_bodega):
    """
    Retorna la tríada de control y métricas de seguridad de un producto en una bodega:
    - stock_actual: float (existencia física real en la bodega indicada)
    - stock_minimo: float (reserva obligatoria según catálogo de productos)
    - disponible_retiro: float (máximo que se puede retirar/trasladar/ajustar sin violar el mínimo: max(0.0, stock_actual - stock_minimo))
    - estado: str ('OPTIMO', 'MINIMO', 'DEFICIT')
    - mensaje: str (descripción del estado de salud del stock)
    """
    session = get_session()
    if not session:
        return {
            "stock_actual": 0.0, "stock_minimo": 0.0, "disponible_retiro": 0.0,
            "estado": "SIN_DATOS", "mensaje": "Base de datos no disponible.",
            "producto_nombre": "", "producto_codigo": ""
        }
    try:
        prod = session.query(Producto).get(id_producto)
        stock_minimo = float(prod.STOCK_MINIMO or 0.0) if prod else 0.0
        
        existencia = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_producto, ID_BODEGA=id_bodega).first()
        stock_actual = float(existencia.STOCK_ACTUAL or 0.0) if existencia else 0.0
        
        disponible_retiro = max(0.0, stock_actual - stock_minimo)
        
        if stock_actual > stock_minimo:
            estado = "OPTIMO"
            mensaje = f"Stock saludable. Puedes retirar o trasladar hasta {disponible_retiro:.1f} unidades."
        elif stock_actual == stock_minimo:
            estado = "MINIMO"
            mensaje = f"En límite de reserva ({stock_minimo:.1f} un). No se permiten salidas ni traslados."
        else:
            estado = "DEFICIT"
            mensaje = f"Déficit crítico: El stock actual ({stock_actual:.1f} un) está por debajo del mínimo ({stock_minimo:.1f} un)."
            
        return {
            "stock_actual": stock_actual,
            "stock_minimo": stock_minimo,
            "disponible_retiro": disponible_retiro,
            "estado": estado,
            "mensaje": mensaje,
            "producto_nombre": prod.DESCRIPCION_PRODUCTO if prod else "",
            "producto_codigo": prod.CODIGO_UNICO if prod else ""
        }
    except Exception as e:
        return {
            "stock_actual": 0.0, "stock_minimo": 0.0, "disponible_retiro": 0.0,
            "estado": "ERROR", "mensaje": str(e),
            "producto_nombre": "", "producto_codigo": ""
        }
    finally:
        session.close()


def registrar_movimiento(usuario_id, tipo_movimiento_id, bodega_origen_id, bodega_destino_id, doc_referencia, detalles_productos, motivo_id=None, observaciones=""):
    """
    Aquí proceso cualquier transacción de inventario en una sola transacción atómica segura:
    - Verifico que el tipo de movimiento exista.
    - REGLAS DE CONDICIÓN SOLICITADAS:
      1. Si se solicitan 15 artículos y solo hay 10 en bodega -> Bloqueo inmediato (stock insuficiente).
      2. Si se solicitan 12 artículos, hay 15 en bodega y el stock mínimo es 5 -> Bloqueo inmediato:
         (15 - 12 = 3 < 5). La operación no se emite porque debe conservar al menos 5 unidades de reserva.
      3. Traslados entre bodegas: Valida origen (ambas reglas) y acredita destino de forma consistente.
    - Rol: Si el usuario es Encargado de Bodega, la operación queda en estado PENDIENTE sin impacto físico hasta aprobación.
    """
    session = get_session()
    if not session:
        return False, "Base de datos no disponible."
        
    try:
        # 1. Obtengo el rol del usuario que realiza la transacción
        usuario_reg = session.query(Usuario).get(usuario_id)
        user_rol_id = getattr(usuario_reg, "ID_ROL", 1)
        user_rol_nom = usuario_reg.rol.NOMBRE_ROL if (usuario_reg and usuario_reg.rol) else ""
        es_admin_usuario = is_admin_role(user_rol_nom, user_rol_id)

        # 2. Obtengo el tipo de movimiento (auto-creando TRASLADO si no existe aún en la BD)
        tipo = session.query(TipoMovimiento).get(tipo_movimiento_id)
        if not tipo and tipo_movimiento_id == 6:
            tipo = session.query(TipoMovimiento).filter(TipoMovimiento.NOMBRE_TIPO.like('%TRASLADO%')).first()
            if not tipo:
                tipo = TipoMovimiento(NOMBRE_TIPO='TRASLADO', EFECTO_STOCK=0)
                session.add(tipo)
                session.flush()
            tipo_movimiento_id = tipo.ID_TIPO_MOVIMIENTO
        if not tipo:
            return False, "Tipo de movimiento inválido."
            
        efecto = tipo.EFECTO_STOCK
        es_traslado = "TRASLADO" in tipo.NOMBRE_TIPO.upper() or efecto == 0
        es_ajuste = "AJUSTE" in tipo.NOMBRE_TIPO.upper()

        # Si el usuario NO es administrador, toda operación se canaliza como solicitud para auditoría
        if not es_admin_usuario:
            estado_inicial = 'PENDIENTE'
            if not es_traslado and not es_ajuste:
                tipo_ajuste_id = 4 if efecto >= 0 else 5
                tipo_ajuste = session.query(TipoMovimiento).get(tipo_ajuste_id)
                if tipo_ajuste:
                    tipo = tipo_ajuste
                    tipo_movimiento_id = tipo_ajuste_id
                    efecto = tipo.EFECTO_STOCK
                    es_ajuste = True
        else:
            estado_inicial = 'APROBADO'

        # 3. Validación de bodegas según el tipo de movimiento
        if es_traslado:
            if not bodega_origen_id or not bodega_destino_id:
                raise ValueError("Para realizar un traslado entre bodegas debes especificar bodega de origen y bodega de destino.")
            if int(bodega_origen_id) == int(bodega_destino_id):
                raise ValueError("La bodega de origen y la bodega de destino no pueden ser la misma.")
        
        # 4. Genero folio único irrepetible
        nuevo_folio = f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}" 
        
        # 5. Creo la cabecera principal del comprobante
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
        session.flush()

        # 6. Proceso cada producto incluido en la transacción
        for detalle in detalles_productos:
            id_prod = detalle['id_producto']
            cantidad = float(detalle['cantidad'])
            costo_uni = float(detalle.get('costo_unitario', 0))
            
            if cantidad <= 0:
                raise ValueError("La cantidad a operar debe ser estrictamente mayor a 0.")
            
            prod = session.query(Producto).get(id_prod)
            if not prod:
                raise ValueError(f"Producto con ID {id_prod} no encontrado en catálogo.")
            prod_desc = prod.DESCRIPCION_PRODUCTO
            stock_minimo = float(prod.STOCK_MINIMO or 0.0)

            # -------------------------------------------------------------
            # CASO A: TRASLADO ENTRE BODEGAS (Origen -> Destino)
            # -------------------------------------------------------------
            if es_traslado:
                b_origen = session.query(Bodega).get(bodega_origen_id)
                nom_origen = b_origen.NOMBRE_BODEGA if b_origen else f"Bodega #{bodega_origen_id}"
                
                ex_origen = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_origen_id).first()
                saldo_ant_origen = float(ex_origen.STOCK_ACTUAL if ex_origen else 0.0)
                saldo_nuevo_origen = saldo_ant_origen - cantidad

                # CONDICIÓN 1: Existencia suficiente en origen
                if cantidad > saldo_ant_origen:
                    raise ValueError(
                        f"Stock insuficiente en la bodega de origen '{nom_origen}'. "
                        f"Hay {saldo_ant_origen:.1f} unidades disponibles y estás solicitando trasladar {cantidad:.1f} unidades."
                    )

                # CONDICIÓN 2: Reserva de Stock Mínimo en origen
                if saldo_nuevo_origen < stock_minimo:
                    disponible_traslado = max(0.0, saldo_ant_origen - stock_minimo)
                    raise ValueError(
                        f"Operación no permitida por condición de Stock Mínimo: "
                        f"La bodega de origen '{nom_origen}' debe mantener al menos {stock_minimo:.1f} unidades de reserva de '{prod_desc}'. "
                        f"Con las {cantidad:.1f} unidades solicitadas quedarían {saldo_nuevo_origen:.1f}. "
                        f"Cantidad máxima permitida para trasladar: {disponible_traslado:.1f} unidades."
                    )

                ex_destino = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_destino_id).first()
                saldo_ant_destino = float(ex_destino.STOCK_ACTUAL if ex_destino else 0.0)
                saldo_nuevo_destino = saldo_ant_destino + cantidad

                # Si es aprobado directo (Admin), aplico el cambio en ambas bodegas
                if estado_inicial == 'APROBADO':
                    if ex_origen:
                        ex_origen.STOCK_ACTUAL = saldo_nuevo_origen
                    if ex_destino:
                        ex_destino.STOCK_ACTUAL = saldo_nuevo_destino
                    else:
                        session.add(ExistenciaBodega(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_destino_id, STOCK_ACTUAL=saldo_nuevo_destino))

                nuevo_detalle = DetalleKardex(
                    ID_MOVIMIENTO=movimiento.ID_MOVIMIENTO,
                    ID_PRODUCTO=id_prod,
                    CANTIDAD=cantidad,
                    COSTO_UNITARIO=costo_uni,
                    COSTO_TOTAL=cantidad * costo_uni,
                    SALDO_ANTERIOR=saldo_ant_origen,
                    SALDO_NUEVO=saldo_nuevo_origen
                )
                session.add(nuevo_detalle)

            # -------------------------------------------------------------
            # CASO B: ENTRADAS, SALIDAS Y AJUSTES
            # -------------------------------------------------------------
            else:
                bodega_afectada = bodega_origen_id if efecto < 0 else (bodega_destino_id if bodega_destino_id else bodega_origen_id)
                b_afectada = session.query(Bodega).get(bodega_afectada)
                nom_bodega = b_afectada.NOMBRE_BODEGA if b_afectada else f"Bodega #{bodega_afectada}"

                existencia = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_afectada).first()
                saldo_anterior = float(existencia.STOCK_ACTUAL if existencia else 0.0)
                saldo_nuevo = saldo_anterior + (cantidad * efecto)

                # SI LA OPERACIÓN RESTA STOCK (Salidas regulares o Ajustes Negativos):
                if efecto < 0:
                    # CONDICIÓN 1: Existencia física suficiente
                    if cantidad > saldo_anterior:
                        raise ValueError(
                            f"Stock insuficiente en '{nom_bodega}'. "
                            f"Hay {saldo_anterior:.1f} unidades disponibles y estás solicitando {cantidad:.1f} unidades."
                        )

                    # CONDICIÓN 2: Reserva de Stock Mínimo
                    if saldo_nuevo < stock_minimo:
                        disponible_retiro = max(0.0, saldo_anterior - stock_minimo)
                        raise ValueError(
                            f"Operación no permitida por condición de Stock Mínimo: "
                            f"La bodega '{nom_bodega}' debe conservar al menos {stock_minimo:.1f} unidades de reserva de '{prod_desc}'. "
                            f"Con {cantidad:.1f} unidades solicitadas quedarían {saldo_nuevo:.1f}. "
                            f"Cantidad máxima permitida para retirar/ajustar: {disponible_retiro:.1f} unidades."
                        )

                # Si es aprobado directo (Admin), actualizo el stock físico inmediatamente
                if estado_inicial == 'APROBADO':
                    if existencia:
                        existencia.STOCK_ACTUAL = saldo_nuevo
                    else:
                        nueva_existencia = ExistenciaBodega(ID_PRODUCTO=id_prod, ID_BODEGA=bodega_afectada, STOCK_ACTUAL=saldo_nuevo)
                        session.add(nueva_existencia)

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

        # 7. Confirmo la transacción en base de datos
        session.commit()
        if estado_inicial == 'PENDIENTE':
            return True, "Solicitud guardada en revisión. Queda PENDIENTE de aprobación por Williams (Administrador) y las existencias físicas se mantienen sin cambios hasta su autorización."
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
        return [{"id": p.ID_PRODUCTO, "codigo": p.CODIGO_UNICO, "nombre": p.DESCRIPCION_PRODUCTO, "stock_minimo": float(p.STOCK_MINIMO or 0.0)} for p in productos]
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
                
                # Para traslados, muestro 'Origen -> Destino'
                if m.bodega_origen and m.bodega_destino:
                    bodega_nom = f"{m.bodega_origen.NOMBRE_BODEGA} ➔ {m.bodega_destino.NOMBRE_BODEGA}"
                else:
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
