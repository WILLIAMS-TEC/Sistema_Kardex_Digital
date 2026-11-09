"""
Controlador de Administración, Catálogo Maestro y Circuito de Ajustes.
Sistema Inventarios Kardex Digital.

En este archivo programé las operaciones administrativas de la plataforma:
- CRUD de usuarios y activación/desactivación de accesos al sistema.
- Catálogo maestro de productos (creación, edición y auto-inicialización de existencias en bodegas).
- Bandeja de solicitudes de ajuste y traslados: consulta, autorización atómica con impacto físico en el Kardex y rechazo con justificación.
- Regla de Stock Mínimo y Stock Insuficiente en autorizaciones.
"""

from datetime import datetime
from models.database import get_session
from models.entities import Categoria, UnidadMedida, Usuario, Rol, Producto, Bodega, ExistenciaBodega


def obtener_categorias():
    """Aquí consulto todas las categorías registradas en la base de datos (Laptops, Redes, etc.)."""
    session = get_session()
    if not session: return []
    try:
        categorias = session.query(Categoria).all()
        return [{"id": c.ID_CATEGORIA, "nombre": c.NOMBRE_CATEGORIA} for c in categorias]
    except Exception:
        return []
    finally:
        session.close()


def obtener_unidades():
    """Aquí consulto las unidades de medida oficiales (Unidad, Caja, Paquete, etc.) con sus símbolos."""
    session = get_session()
    if not session: return []
    try:
        unidades = session.query(UnidadMedida).all()
        return [{"id": u.ID_UNIDAD, "nombre": f"{u.NOMBRE_UNIDAD} ({u.SIMBOLO})"} for u in unidades]
    except Exception:
        return []
    finally:
        session.close()


def obtener_roles():
    """Aquí traigo los roles disponibles en el sistema (Administrador, Encargado de bodega, Consultas)."""
    session = get_session()
    if not session: return []
    try:
        roles = session.query(Rol).all()
        return [{"id": r.ID_ROL, "nombre": r.NOMBRE_ROL} for r in roles]
    except Exception:
        return []
    finally:
        session.close()


def obtener_usuarios():
    """
    Con esta función traigo todos los usuarios registrados, haciendo un join con su Rol
    para presentar sus datos en el directorio de credenciales.
    """
    session = get_session()
    if not session: return []
    try:
        usuarios = session.query(Usuario).join(Rol).all()
        return [{
            "id": u.ID_USUARIO,
            "nombre": u.NOMBRE_COMPLETO,
            "correo": u.CORREO,
            "id_rol": u.ID_ROL,
            "rol": u.rol.NOMBRE_ROL,
            "estado": u.ESTADO
        } for u in usuarios]
    except Exception:
        return []
    finally:
        session.close()


def crear_usuario(nombre, correo, password, id_rol):
    """
    En este método registro una nueva cuenta en la base de datos con estado ACTIVO por defecto.
    Valido campos obligatorios y evito correos duplicados.
    """
    nombre_clean = (nombre or "").strip()
    correo_clean = (correo or "").strip().lower()
    pass_clean = (password or "").strip()

    if not nombre_clean or not correo_clean or not pass_clean:
        return False, "Todos los campos (nombre, correo y contraseña) son obligatorios."

    session = get_session()
    if not session:
        return False, "Base de datos no disponible para crear el usuario."

    try:
        from sqlalchemy import func
        # Verifico si ya existe un usuario con el mismo correo electrónico
        existente = session.query(Usuario).filter(
            func.lower(Usuario.CORREO) == correo_clean
        ).first()
        if existente:
            return False, f"El correo '{correo_clean}' ya está registrado con otro usuario."

        nuevo = Usuario(
            NOMBRE_COMPLETO=nombre_clean,
            CORREO=correo_clean,
            PASSW_ORD=pass_clean,
            ID_ROL=int(id_rol),
            ESTADO=True
        )
        session.add(nuevo)
        session.commit()
        return True, "Usuario creado exitosamente en la base de datos."
    except Exception as e:
        session.rollback()
        return False, f"Error al guardar el usuario en la BD: {str(e)}"
    finally:
        session.close()


def actualizar_usuario(id_usr, nombre, correo, password, id_rol):
    """
    Aquí modifico los datos de un usuario existente. Si la contraseña viene en blanco,
    conservo la contraseña que ya tenía sin alterarla.
    """
    nombre_clean = (nombre or "").strip()
    correo_clean = (correo or "").strip().lower()

    if not nombre_clean or not correo_clean:
        return False, "El nombre y el correo electrónico son obligatorios."

    session = get_session()
    if not session:
        return False, "Base de datos no disponible."

    try:
        from sqlalchemy import func
        # Valido que el correo no esté ocupado por otro usuario distinto
        duplicado = session.query(Usuario).filter(
            func.lower(Usuario.CORREO) == correo_clean,
            Usuario.ID_USUARIO != id_usr
        ).first()
        if duplicado:
            return False, f"El correo '{correo_clean}' ya está en uso por otro usuario."

        u = session.query(Usuario).get(id_usr)
        if u:
            u.NOMBRE_COMPLETO = nombre_clean
            u.CORREO = correo_clean
            if password and password.strip():
                u.PASSW_ORD = password.strip()
            u.ID_ROL = int(id_rol)
            session.commit()
            return True, "Usuario actualizado correctamente."
        return False, "Usuario no encontrado en la base de datos."
    except Exception as e:
        session.rollback()
        return False, f"Error al actualizar usuario: {str(e)}"
    finally:
        session.close()


def toggle_estado_usuario(id_usuario):
    """Aquí invierto el estado del usuario (de Activo a Inactivo o viceversa) con un solo clic."""
    session = get_session()
    if not session: return
    try:
        u = session.query(Usuario).get(id_usuario)
        if u:
            u.ESTADO = not u.ESTADO
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def obtener_catalogo():
    """
    Con esta función consulto el catálogo maestro completo de productos con sus parámetros Kardex
    (código SKU, descripción, categoría, unidad, stock mínimo, costo promedio y estado).
    """
    session = get_session()
    if not session: return []
    try:
        productos = session.query(Producto).all()
        return [{
            "id": p.ID_PRODUCTO,
            "codigo": p.CODIGO_UNICO,
            "desc": p.DESCRIPCION_PRODUCTO,
            "id_cat": p.ID_CATEGORIA,
            "id_uni": p.ID_UNIDAD,
            "stock_min": p.STOCK_MINIMO,
            "costo": p.COSTO_PROMEDIO,
            "estado": p.ESTADO
        } for p in productos]
    except Exception:
        return []
    finally:
        session.close()


def crear_producto(codigo, desc, id_categoria, id_unidad, stock_min, costo):
    """
    Aquí registro un nuevo producto en el catálogo oficial.
    REGLA DE NEGOCIO CLAVE: Automáticamente le inicializo una fila de existencia con stock 0.0
    en cada una de las bodegas activas para que esté listo para recibir entradas de inventario.
    """
    session = get_session()
    if not session: return False
    try:
        nuevo = Producto(
            CODIGO_UNICO=codigo,
            DESCRIPCION_PRODUCTO=desc,
            ID_CATEGORIA=id_categoria,
            ID_UNIDAD=id_unidad,
            STOCK_MINIMO=stock_min,
            COSTO_PROMEDIO=costo,
            ESTADO=True
        )
        session.add(nuevo)
        session.flush() # Hago flush para generar el ID_PRODUCTO

        # Inicializo el registro de existencias en cada bodega activa
        bodegas = session.query(Bodega).filter_by(ESTADO=True).all()
        for b in bodegas:
            session.add(ExistenciaBodega(ID_PRODUCTO=nuevo.ID_PRODUCTO, ID_BODEGA=b.ID_BODEGA, STOCK_ACTUAL=0.0))

        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def actualizar_producto(id_prod, codigo, desc, id_categoria, id_unidad, stock_min, costo):
    """Aquí actualizo la ficha técnica y parámetros de un producto en el catálogo."""
    session = get_session()
    if not session: return False
    try:
        p = session.query(Producto).get(id_prod)
        if p:
            p.CODIGO_UNICO = codigo
            p.DESCRIPCION_PRODUCTO = desc
            p.ID_CATEGORIA = id_categoria
            p.ID_UNIDAD = id_unidad
            p.STOCK_MINIMO = stock_min
            p.COSTO_PROMEDIO = costo
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def toggle_estado_producto(id_producto):
    """Aquí activo o desactivo un producto en el catálogo para controlar su disponibilidad."""
    session = get_session()
    if not session: return
    try:
        p = session.query(Producto).get(id_producto)
        if p:
            p.ESTADO = not p.ESTADO
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def obtener_ajustes_pendientes():
    """
    Aquí traigo todos los movimientos que están esperando resolución administrativa
    (estados 'PENDIENTE' o 'EN REVISION'), incluyendo la justificación descriptiva y solicitante.
    Soporta tanto ajustes como traslados entre bodegas.
    """
    session = get_session()
    if not session: return []
    try:
        from models.entities import MovimientoKardex
        movs = session.query(MovimientoKardex)\
            .filter(MovimientoKardex.ESTADO_APROBACION.in_(['EN REVISION', 'PENDIENTE']))\
            .order_by(MovimientoKardex.FECHA_MOVIMIENTO.asc()).all()
            
        resultado = []
        for m in movs:
            for det in m.detalles:
                es_traslado = "TRASLADO" in (m.tipo_movimiento.NOMBRE_TIPO.upper() if m.tipo_movimiento else "")
                if es_traslado and m.bodega_origen and m.bodega_destino:
                    bodega_str = f"{m.bodega_origen.NOMBRE_BODEGA} ➔ {m.bodega_destino.NOMBRE_BODEGA}"
                else:
                    bodega_str = (m.bodega_destino.NOMBRE_BODEGA if m.bodega_destino else (m.bodega_origen.NOMBRE_BODEGA if m.bodega_origen else "-"))

                resultado.append({
                    "id_movimiento": m.ID_MOVIMIENTO,
                    "folio": m.FOLIO_COMPROBANTE,
                    "fecha": m.FECHA_MOVIMIENTO.strftime("%d/%m/%Y %I:%M %p"),
                    "tipo": m.tipo_movimiento.NOMBRE_TIPO if m.tipo_movimiento else "AJUSTE",
                    "solicitante": m.usuario_registro.NOMBRE_COMPLETO if m.usuario_registro else "-",
                    "bodega": bodega_str,
                    "id_bodega": m.ID_BODEGA_DESTINO or m.ID_BODEGA_ORIGEN,
                    "id_bodega_origen": m.ID_BODEGA_ORIGEN,
                    "id_bodega_destino": m.ID_BODEGA_DESTINO,
                    "id_producto": det.ID_PRODUCTO,
                    "producto": det.producto.DESCRIPCION_PRODUCTO if det.producto else "-",
                    "codigo": det.producto.CODIGO_UNICO if det.producto else "-",
                    "cantidad": float(det.CANTIDAD or 0),
                    "costo": float(det.COSTO_UNITARIO or 0),
                    "motivo": m.motivo.DESCRIPCION_MOTIVO if m.motivo else ("Traslado de Inventario" if es_traslado else "Ajuste de inventario"),
                    "observaciones": m.OBSERVACIONES or "-",
                    "efecto": m.tipo_movimiento.EFECTO_STOCK if m.tipo_movimiento else 1
                })
        return resultado
    except Exception:
        return []
    finally:
        session.close()


def aprobar_ajuste(id_movimiento, id_usuario_admin):
    """
    CIRCUITO DE AUDITORÍA: Aquí ejecuto la aprobación formal de un ajuste o traslado:
    1. Valido estrictamente que el usuario autorizador sea Administrador.
    2. Verifico que el movimiento exista y siga en estado PENDIENTE.
    3. REGLAS ESTRICTAS DE SEGURIDAD SOLICITADAS:
       - Condición 1: Stock suficiente en la bodega de retiro.
       - Condición 2: Conservación inquebrantable del Stock Mínimo obligatorio.
         (Ej. si hay 15 y el mínimo es 5, no permite retirar 12 porque quedarían 3 < 5).
    4. Aplica el impacto en existencias físicas (sumas, restas o traslados).
    5. Asienta la auditoría con usuario autorizador y fecha exacta.
    """
    session = get_session()
    if not session:
        return False, "Base de datos no disponible."
    try:
        from controllers.auth_ctrl import is_admin_role
        from models.entities import MovimientoKardex, ExistenciaBodega, Usuario, Producto, Bodega

        # Valido permisos de Administrador
        admin_user = session.query(Usuario).get(id_usuario_admin)
        rol_nombre = admin_user.rol.NOMBRE_ROL if (admin_user and admin_user.rol) else ""
        if not admin_user or not is_admin_role(rol_nombre, admin_user.ID_ROL):
            return False, "Acceso denegado: Solo el Administrador tiene autorización para aprobar ajustes."

        mov = session.query(MovimientoKardex).get(id_movimiento)
        if not mov or mov.ESTADO_APROBACION not in ('EN REVISION', 'PENDIENTE'):
            return False, "El movimiento no existe o ya fue procesado."
            
        efecto = mov.tipo_movimiento.EFECTO_STOCK if mov.tipo_movimiento else 1
        es_traslado = "TRASLADO" in (mov.tipo_movimiento.NOMBRE_TIPO.upper() if mov.tipo_movimiento else "") or efecto == 0

        # CASO 1: TRASLADO ENTRE BODEGAS
        if es_traslado:
            for det in mov.detalles:
                prod = session.query(Producto).get(det.ID_PRODUCTO)
                stock_minimo = float(prod.STOCK_MINIMO or 0.0) if prod else 0.0
                cant = float(det.CANTIDAD or 0.0)

                ex_origen = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=det.ID_PRODUCTO, ID_BODEGA=mov.ID_BODEGA_ORIGEN).first()
                saldo_ant_origen = float(ex_origen.STOCK_ACTUAL if ex_origen else 0.0)
                saldo_nuevo_origen = saldo_ant_origen - cant

                b_origen = session.query(Bodega).get(mov.ID_BODEGA_ORIGEN)
                nom_origen = b_origen.NOMBRE_BODEGA if b_origen else "Bodega de Origen"

                # Condición 1: Stock suficiente
                if cant > saldo_ant_origen:
                    raise ValueError(f"No se puede aprobar el traslado: Stock insuficiente en '{nom_origen}'. Disponible: {saldo_ant_origen:.1f}, solicitado: {cant:.1f}.")

                # Condición 2: Stock Mínimo
                if saldo_nuevo_origen < stock_minimo:
                    disp = max(0.0, saldo_ant_origen - stock_minimo)
                    raise ValueError(f"No se puede aprobar el traslado por condición de Stock Mínimo: La bodega '{nom_origen}' debe conservar al menos {stock_minimo:.1f} unidades de '{prod.DESCRIPCION_PRODUCTO}'. Con este traslado quedarían {saldo_nuevo_origen:.1f}. Máximo a trasladar: {disp:.1f} unidades.")

                ex_destino = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=det.ID_PRODUCTO, ID_BODEGA=mov.ID_BODEGA_DESTINO).first()
                saldo_ant_destino = float(ex_destino.STOCK_ACTUAL if ex_destino else 0.0)
                saldo_nuevo_destino = saldo_ant_destino + cant

                ex_origen.STOCK_ACTUAL = saldo_nuevo_origen
                if ex_destino:
                    ex_destino.STOCK_ACTUAL = saldo_nuevo_destino
                else:
                    session.add(ExistenciaBodega(ID_PRODUCTO=det.ID_PRODUCTO, ID_BODEGA=mov.ID_BODEGA_DESTINO, STOCK_ACTUAL=saldo_nuevo_destino))

                det.SALDO_ANTERIOR = saldo_ant_origen
                det.SALDO_NUEVO = saldo_nuevo_origen

        # CASO 2: AJUSTE POSITIVO O NEGATIVO
        else:
            bodega_id = mov.ID_BODEGA_DESTINO if efecto > 0 else (mov.ID_BODEGA_ORIGEN or mov.ID_BODEGA_DESTINO)
            b_afectada = session.query(Bodega).get(bodega_id)
            nom_bodega = b_afectada.NOMBRE_BODEGA if b_afectada else "Bodega"

            for det in mov.detalles:
                prod = session.query(Producto).get(det.ID_PRODUCTO)
                stock_minimo = float(prod.STOCK_MINIMO or 0.0) if prod else 0.0
                cant = float(det.CANTIDAD or 0.0)

                existencia = session.query(ExistenciaBodega).filter_by(ID_PRODUCTO=det.ID_PRODUCTO, ID_BODEGA=bodega_id).first()
                saldo_anterior = float(existencia.STOCK_ACTUAL if existencia else 0.0)
                saldo_nuevo = saldo_anterior + (cant * efecto)

                # Si es un ajuste negativo (disminución):
                if efecto < 0:
                    # Condición 1: Stock suficiente
                    if cant > saldo_anterior:
                        raise ValueError(f"No se puede aprobar el ajuste: Stock insuficiente en '{nom_bodega}'. Disponible: {saldo_anterior:.1f}, solicitado: {cant:.1f}.")

                    # Condición 2: Stock Mínimo
                    if saldo_nuevo < stock_minimo:
                        disp = max(0.0, saldo_anterior - stock_minimo)
                        raise ValueError(f"No se puede aprobar el ajuste por condición de Stock Mínimo: La bodega '{nom_bodega}' debe conservar al menos {stock_minimo:.1f} unidades de reserva de '{prod.DESCRIPCION_PRODUCTO}'. Con este ajuste quedarían {saldo_nuevo:.1f}. Máximo permitido a retirar: {disp:.1f} unidades.")

                if existencia:
                    existencia.STOCK_ACTUAL = saldo_nuevo
                else:
                    session.add(ExistenciaBodega(ID_PRODUCTO=det.ID_PRODUCTO, ID_BODEGA=bodega_id, STOCK_ACTUAL=saldo_nuevo))

                det.SALDO_ANTERIOR = saldo_anterior
                det.SALDO_NUEVO = saldo_nuevo

        # Asiento la auditoría formal en la cabecera del comprobante
        mov.ESTADO_APROBACION = 'APROBADO'
        mov.ID_USUARIO_AUTORIZA = id_usuario_admin
        mov.FECHA_AUTORIZACION = datetime.now()

        session.commit()
        return True, "Ajuste/traslado aprobado y aplicado al inventario exitosamente."
    except ValueError as ve:
        session.rollback()
        return False, str(ve)
    except Exception as e:
        session.rollback()
        return False, f"Error al aprobar ajuste: {str(e)}"
    finally:
        session.close()


def rechazar_ajuste(id_movimiento, id_usuario_admin, motivo_rechazo=""):
    """
    Aquí ejecuto el rechazo formal de una solicitud de ajuste:
    - No altero el stock físico de ninguna bodega.
    - Cambio el estado a 'RECHAZADO' en el historial.
    - Adjunto el motivo de rechazo en las observaciones para que el solicitante lo vea.
    """
    session = get_session()
    if not session:
        return False, "Base de datos no disponible."
    try:
        from controllers.auth_ctrl import is_admin_role
        from models.entities import MovimientoKardex, Usuario

        # Valido permisos de Administrador
        admin_user = session.query(Usuario).get(id_usuario_admin)
        rol_nombre = admin_user.rol.NOMBRE_ROL if (admin_user and admin_user.rol) else ""
        if not admin_user or not is_admin_role(rol_nombre, admin_user.ID_ROL):
            return False, "Acceso denegado: Solo el Administrador tiene autorización para rechazar ajustes."

        mov = session.query(MovimientoKardex).get(id_movimiento)
        if not mov or mov.ESTADO_APROBACION not in ('EN REVISION', 'PENDIENTE'):
            return False, "El movimiento no existe o ya fue procesado."
            
        mov.ESTADO_APROBACION = 'RECHAZADO'
        mov.ID_USUARIO_AUTORIZA = id_usuario_admin
        mov.FECHA_AUTORIZACION = datetime.now()
        if motivo_rechazo:
            mov.OBSERVACIONES = (mov.OBSERVACIONES or "") + f" [Rechazado por Admin: {motivo_rechazo}]"
            
        session.commit()
        return True, "Solicitud de ajuste rechazada."
    except Exception as e:
        session.rollback()
        return False, f"Error al rechazar ajuste: {str(e)}"
    finally:
        session.close()


def obtener_solicitudes_ajuste(usuario_id=None):
    """
    Con esta consulta traigo el historial de solicitudes de ajuste y traslados,
    permitiendo a los encargados de bodega supervisar la resolución de sus solicitudes.
    """
    session = get_session()
    if not session: return []
    try:
        from models.entities import MovimientoKardex, TipoMovimiento
        query = session.query(MovimientoKardex)\
            .join(TipoMovimiento, MovimientoKardex.ID_TIPO_MOVIMIENTO == TipoMovimiento.ID_TIPO_MOVIMIENTO)
        if usuario_id:
            query = query.filter(
                (MovimientoKardex.ID_USUARIO_REGISTRO == usuario_id) &
                (
                    (TipoMovimiento.NOMBRE_TIPO.like('%AJUSTE%')) |
                    (TipoMovimiento.NOMBRE_TIPO.like('%TRASLADO%')) |
                    (MovimientoKardex.ESTADO_APROBACION.in_(['PENDIENTE', 'EN REVISION', 'RECHAZADO']))
                )
            )
        else:
            query = query.filter(
                (TipoMovimiento.NOMBRE_TIPO.like('%AJUSTE%')) |
                (TipoMovimiento.NOMBRE_TIPO.like('%TRASLADO%')) |
                (MovimientoKardex.ESTADO_APROBACION.in_(['PENDIENTE', 'EN REVISION', 'RECHAZADO']))
            )
        movs = query.order_by(MovimientoKardex.FECHA_MOVIMIENTO.desc()).all()
        
        resultado = []
        for m in movs:
            for det in m.detalles:
                es_traslado = "TRASLADO" in (m.tipo_movimiento.NOMBRE_TIPO.upper() if m.tipo_movimiento else "")
                if es_traslado and m.bodega_origen and m.bodega_destino:
                    bodega_str = f"{m.bodega_origen.NOMBRE_BODEGA} ➔ {m.bodega_destino.NOMBRE_BODEGA}"
                else:
                    bodega_str = (m.bodega_destino.NOMBRE_BODEGA if m.bodega_destino else (m.bodega_origen.NOMBRE_BODEGA if m.bodega_origen else "-"))

                resultado.append({
                    "id_movimiento": m.ID_MOVIMIENTO,
                    "folio": m.FOLIO_COMPROBANTE,
                    "fecha": m.FECHA_MOVIMIENTO.strftime("%d/%m/%Y %I:%M %p"),
                    "tipo": m.tipo_movimiento.NOMBRE_TIPO if m.tipo_movimiento else "AJUSTE",
                    "solicitante": m.usuario_registro.NOMBRE_COMPLETO if m.usuario_registro else "-",
                    "bodega": bodega_str,
                    "producto": det.producto.DESCRIPCION_PRODUCTO if det.producto else "-",
                    "codigo": det.producto.CODIGO_UNICO if det.producto else "-",
                    "cantidad": float(det.CANTIDAD or 0),
                    "motivo": m.motivo.DESCRIPCION_MOTIVO if m.motivo else ("Traslado de Inventario" if es_traslado else "Ajuste de inventario"),
                    "estado": m.ESTADO_APROBACION or "EN REVISION",
                    "autorizador": m.usuario_autoriza.NOMBRE_COMPLETO if m.usuario_autoriza else "-",
                    "observaciones": m.OBSERVACIONES or "-",
                    "efecto": m.tipo_movimiento.EFECTO_STOCK if m.tipo_movimiento else 1
                })
        return resultado
    except Exception:
        return []
    finally:
        session.close()
