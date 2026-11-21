
# ventas/tasks.py
"""Tareas asíncronas de la app ventas — W17."""

import logging
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """Envía el correo de confirmación de pedido al cliente."""

    from configuracion.models import ConfiguracionERP
    from ventas.models import Pedido

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(
            f'[correo_confirmacion] Pedido {pedido_id} no existe.'
        )
        return {'estado': 'error', 'razon': 'Pedido no encontrado'}

    # Evitar correos duplicados.
    if pedido.correo_enviado:
        logger.info(
            f'[correo_confirmacion] Pedido {pedido.numero_pedido}: '
            'correo ya enviado anteriormente.'
        )
        return {
            'estado': 'skip',
            'pedido_id': pedido_id,
            'razon': 'correo ya enviado',
        }

    config = ConfiguracionERP.get_instance()

    # Preparar los productos y calcular sus subtotales.
    items = []

    for item_original in pedido.items_snapshot or []:
        item = dict(item_original)

        cantidad = int(item.get('cantidad', 0))
        precio = Decimal(str(item.get('precio', '0')))

        item['subtotal'] = precio * cantidad
        items.append(item)

    url_pedido = (
        f'https://erp-django-utec.onrender.com'
        f'/ventas/{pedido.pk}/'
    )

    contexto = {
        'pedido': pedido,
        'config': config,
        'items': items,
        'url_pedido': url_pedido,
    }

    asunto = (
        f'Confirmación de pedido {pedido.numero_pedido} '
        f'— {config.nombre_empresa}'
    )

    texto_plano = render_to_string(
        'emails/confirmacion_pedido.txt',
        contexto
    )

    html_body = render_to_string(
        'emails/confirmacion_pedido.html',
        contexto
    )

    correo_destino = pedido.cliente.correo
    correo_origen = settings.DEFAULT_FROM_EMAIL

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=correo_origen,
        to=[correo_destino],
    )

    mensaje.attach_alternative(html_body, 'text/html')

    try:
        mensaje.send()

        logger.info(
            f'[correo_confirmacion] Correo enviado a {correo_destino} '
            f'para pedido {pedido.numero_pedido}.'
        )

        pedido.correo_enviado = True
        pedido.save(update_fields=['correo_enviado'])

        return {
            'estado': 'ok',
            'pedido_id': pedido_id,
            'correo': correo_destino,
        }

    except Exception as exc:
        logger.error(
            f'[correo_confirmacion] Error al enviar correo para pedido '
            f'{pedido.numero_pedido}: {exc}'
        )
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )


@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """Verifica productos con stock bajo y envía alerta al administrador."""

    from productos.models import Producto

    productos_bajos = list(
        Producto.objects
        .select_related('categoria')
        .filter(activo=True, stock__lt=umbral)
        .values('pk', 'nombre', 'stock', 'categoria__nombre')
        .order_by('stock')
    )

    if not productos_bajos:
        logger.info(
            f'[stock_bajo] Todos los productos tienen stock >= {umbral}.'
        )
        return {
            'umbral': umbral,
            'total': 0,
            'productos_bajos': []
        }

    logger.warning(
        f'[stock_bajo] {len(productos_bajos)} producto(s) '
        f'con stock < {umbral}.'
    )

    if settings.ADMINS:
        _enviar_alerta_stock(productos_bajos, umbral)

    return {
        'umbral': umbral,
        'total': len(productos_bajos),
        'productos_bajos': productos_bajos,
    }


def _enviar_alerta_stock(productos_bajos: list, umbral: int) -> None:
    """Envía el correo de alerta de stock al administrador."""

    from configuracion.models import ConfiguracionERP

    config = ConfiguracionERP.get_instance()
    fecha = timezone.now().strftime('%d/%m/%Y %H:%M')

    url_admin = (
        'https://erp-django-utec.onrender.com/admin/productos/producto/'
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

    mensaje.attach_alternative(html_body, 'text/html')

    try:
        mensaje.send()
        logger.info(
            f'[stock_bajo] Alerta enviada a {admin_correo}. '
            f'{len(productos_bajos)} productos.'
        )
    except Exception as exc:
        logger.error(f'[stock_bajo] Error al enviar alerta: {exc}')
