
# ventas/tasks.py
"""Tareas asíncronas de la aplicación ventas."""

import logging
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================
# 1. CONFIRMACION DE COMPRA AL CLIENTE
# ============================================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """
    Envía la confirmación de compra al cliente.

    Evita correos duplicados mediante el campo correo_enviado.
    Si el correo ya fue enviado, devuelve estado skip.
    """

    from configuracion.models import ConfiguracionERP
    from ventas.models import Pedido

    # --------------------------------------------------------
    # 1. BUSCAR EL PEDIDO
    # --------------------------------------------------------

    try:
        pedido = Pedido.objects.select_related('cliente').get(
            pk=pedido_id
        )

    except Pedido.DoesNotExist:
        logger.error(
            f'[correo_confirmacion] Pedido {pedido_id} no existe.'
        )

        return {
            'estado': 'error',
            'pedido_id': pedido_id,
            'razon': 'Pedido no encontrado',
        }

    # --------------------------------------------------------
    # 2. EVITAR CORREOS DUPLICADOS
    # --------------------------------------------------------

    if pedido.correo_enviado:
        logger.info(
            f'[correo_confirmacion] Pedido {pedido_id}: '
            'correo ya enviado anteriormente. Se omite el envío.'
        )

        return {
            'estado': 'skip',
            'pedido_id': pedido_id,
            'razon': 'correo ya enviado',
        }

    try:
        # ----------------------------------------------------
        # 3. OBTENER CONFIGURACION DE LA EMPRESA
        # ----------------------------------------------------

        config = ConfiguracionERP.get_instance()

        # ----------------------------------------------------
        # 4. PREPARAR LOS PRODUCTOS DEL PEDIDO
        # ----------------------------------------------------

        items = []

        for item_original in pedido.items_snapshot or []:
            item = dict(item_original)

            cantidad = int(item.get('cantidad', 0))
            precio = Decimal(str(item.get('precio', '0')))

            item['subtotal'] = precio * cantidad

            items.append(item)

        # ----------------------------------------------------
        # 5. PREPARAR CONTEXTO DEL CORREO
        # ----------------------------------------------------

        url_pedido = (
            'https://erp-django-utec.onrender.com'
            f'/ventas/{pedido.pk}/'
        )

        contexto = {
            'pedido': pedido,
            'config': config,
            'items': items,
            'url_pedido': url_pedido,
        }

        correo_destino = pedido.cliente.correo

        # ----------------------------------------------------
        # 6. GENERAR CORREO EN TEXTO Y HTML
        # ----------------------------------------------------

        texto_plano = render_to_string(
            'emails/confirmacion_pedido.txt',
            contexto
        )

        html_body = render_to_string(
            'emails/confirmacion_pedido.html',
            contexto
        )

        # ----------------------------------------------------
        # 7. CONSTRUIR MENSAJE
        # ----------------------------------------------------

        mensaje = EmailMultiAlternatives(
            subject=(
                f'Confirmación de pedido '
                f'{pedido.numero_pedido} '
                f'— {config.nombre_empresa}'
            ),
            body=texto_plano,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_destino],
        )

        mensaje.attach_alternative(
            html_body,
            'text/html'
        )

        # ----------------------------------------------------
        # 8. ENVIAR CORREO AL CLIENTE
        # ----------------------------------------------------

        resultado = mensaje.send()

        if resultado != 1:
            raise RuntimeError(
                'No se pudo confirmar el envío del correo al cliente.'
            )

        # ----------------------------------------------------
        # 9. MARCAR CORREO COMO ENVIADO
        # ----------------------------------------------------

        pedido.correo_enviado = True

        pedido.save(
            update_fields=['correo_enviado']
        )

        logger.info(
            f'[correo_confirmacion] Correo enviado a '
            f'{correo_destino}. Pedido {pedido.numero_pedido}.'
        )

        return {
            'estado': 'ok',
            'pedido_id': pedido_id,
            'cliente_enviado': True,
        }

    except Exception as exc:
        logger.exception(
            f'[correo_confirmacion] Error al procesar pedido '
            f'{pedido.numero_pedido}: {exc}'
        )

        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )


# ============================================================
# 2. VERIFICAR PRODUCTOS CON STOCK BAJO
# ============================================================

@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """Verifica productos con stock bajo y avisa al administrador."""

    from productos.models import Producto

    productos_bajos = list(
        Producto.objects
        .select_related('categoria')
        .filter(
            activo=True,
            stock__lt=umbral
        )
        .values(
            'pk',
            'nombre',
            'stock',
            'categoria__nombre'
        )
        .order_by('stock')
    )

    if not productos_bajos:
        logger.info(
            f'[stock_bajo] Todos los productos tienen stock >= {umbral}.'
        )

        return {
            'umbral': umbral,
            'total': 0,
            'productos_bajos': [],
        }

    logger.warning(
        f'[stock_bajo] {len(productos_bajos)} producto(s) '
        f'con stock < {umbral}.'
    )

    if settings.ADMINS:
        _enviar_alerta_stock(
            productos_bajos,
            umbral
        )

    return {
        'umbral': umbral,
        'total': len(productos_bajos),
        'productos_bajos': productos_bajos,
    }


def _enviar_alerta_stock(
    productos_bajos: list,
    umbral: int
) -> None:
    """Envía alerta de inventario bajo al administrador."""

    from configuracion.models import ConfiguracionERP

    config = ConfiguracionERP.get_instance()

    fecha = timezone.now().strftime(
        '%d/%m/%Y %H:%M'
    )

    url_admin = (
        'https://erp-django-utec.onrender.com'
        '/admin/productos/producto/'
    )

    contexto = {
        'productos_bajos': productos_bajos,
        'total_productos': len(productos_bajos),
        'umbral': umbral,
        'fecha': fecha,
        'url_admin': url_admin,
        'config': config,
    }

    asunto = (
        f'[ALERTA] {len(productos_bajos)} producto(s) '
        f'con stock < {umbral}'
    )

    texto_plano = render_to_string(
        'emails/alerta_stock.txt',
        contexto
    )

    html_body = render_to_string(
        'emails/alerta_stock.html',
        contexto
    )

    admin_nombre, admin_correo = settings.ADMINS[0]

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_correo],
    )

    mensaje.attach_alternative(
        html_body,
        'text/html'
    )

    try:
        mensaje.send()

        logger.info(
            f'[stock_bajo] Alerta enviada a {admin_correo}. '
            f'{len(productos_bajos)} productos.'
        )

    except Exception:
        logger.exception(
            '[stock_bajo] Error al enviar alerta.'
        )


# ============================================================
# 3. REPORTE DIARIO DE VENTAS
# ============================================================

@shared_task(
    bind=True,
    max_retries=2,
    name='ventas.reporte_ventas_diario',
)
def reporte_ventas_diario(self) -> dict:
    """
    Genera y envía el reporte diario de ventas al administrador.

    Se ejecuta mediante Celery Beat según su programación.
    """

    from django.db.models import (
        DecimalField,
        ExpressionWrapper,
        F,
        Sum,
    )

    from configuracion.models import ConfiguracionERP
    from ventas.models import DetalleVenta, Pedido

    hoy = timezone.localdate()

    config = ConfiguracionERP.get_instance()

    # --------------------------------------------------------
    # 1. INDICADORES DEL DIA
    # --------------------------------------------------------

    pedidos_hoy = Pedido.objects.filter(
        fecha_pedido__date=hoy,
        estado='pagado'
    )

    total_pedidos = pedidos_hoy.count()

    total_facturado = pedidos_hoy.aggregate(
        total=Sum('total_pagado')
    )['total'] or Decimal('0.00')

    # --------------------------------------------------------
    # 2. CINCO PRODUCTOS CON MAYORES INGRESOS
    # --------------------------------------------------------

    top_productos = list(
        DetalleVenta.objects
        .filter(
            venta__fecha__date=hoy
        )
        .values(
            nombre=F('producto__nombre')
        )
        .annotate(
            unidades=Sum('cantidad'),
            ingreso=Sum(
                ExpressionWrapper(
                    F('cantidad') * F('precio_unitario'),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2
                    )
                )
            )
        )
        .order_by('-ingreso')[:5]
    )

    logger.info(
        f'[reporte_diario] {hoy}: {total_pedidos} pedidos, '
        f'${total_facturado} facturados, '
        f'{len(top_productos)} productos top.'
    )

    # --------------------------------------------------------
    # 3. ENVIAR REPORTE AL ADMINISTRADOR
    # --------------------------------------------------------

    if settings.ADMINS:
        _enviar_reporte_ventas(
            hoy,
            total_pedidos,
            total_facturado,
            top_productos,
            config
        )

    return {
        'fecha': str(hoy),
        'total_pedidos': total_pedidos,
        'total_facturado': str(total_facturado),
        'top_productos': top_productos,
    }


def _enviar_reporte_ventas(
    fecha,
    total_pedidos,
    total_facturado,
    top_productos,
    config
) -> None:
    """Envía el reporte diario al primer administrador."""

    url_admin = (
        'https://erp-django-utec.onrender.com'
        '/admin/ventas/venta/'
    )

    fecha_str = fecha.strftime('%d/%m/%Y')

    contexto = {
        'fecha': fecha_str,
        'config': config,
        'total_pedidos': total_pedidos,
        'total_facturado': total_facturado,
        'top_productos': top_productos,
        'url_admin': url_admin,
    }

    asunto = (
        f'Reporte de ventas del {fecha_str} '
        f'— {config.nombre_empresa}'
    )

    texto_plano = render_to_string(
        'emails/reporte_ventas.txt',
        contexto
    )

    html_body = render_to_string(
        'emails/reporte_ventas.html',
        contexto
    )

    admin_nombre, admin_correo = settings.ADMINS[0]

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_correo],
    )

    mensaje.attach_alternative(
        html_body,
        'text/html'
    )

    try:
        mensaje.send()

        logger.info(
            f'[reporte_diario] Reporte enviado a {admin_correo}.'
        )

    except Exception:
        logger.exception(
            '[reporte_diario] Error al enviar reporte.'
        )
