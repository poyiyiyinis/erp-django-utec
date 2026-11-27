
# core/scheduled_views.py

import os
import secrets
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def ejecutar_reporte_diario(request):
    """
    Ejecuta el reporte diario mediante una solicitud
    protegida enviada desde GitHub Actions.
    """

    token_configurado = os.environ.get(
        'REPORTE_DIARIO_TOKEN',
        ''
    )

    token_recibido = request.headers.get(
        'X-Report-Token',
        ''
    )

    if not token_configurado:
        return JsonResponse(
            {'error': 'Token no configurado en el servidor.'},
            status=503
        )

    if not secrets.compare_digest(
        token_recibido,
        token_configurado
    ):
        return JsonResponse(
            {'error': 'No autorizado.'},
            status=403
        )

    try:
        from ventas.tasks import reporte_ventas_diario

        resultado = reporte_ventas_diario.run()

        logger.info(
            '[github_actions] Reporte diario ejecutado correctamente.'
        )

        return JsonResponse({
            'estado': 'ok',
            'mensaje': 'Reporte diario ejecutado.',
            'resultado': resultado,
        })

    except Exception:
        logger.exception(
            '[github_actions] Error ejecutando el reporte diario.'
        )

        return JsonResponse(
            {'error': 'No se pudo ejecutar el reporte diario.'},
            status=500
        )
