from django.shortcuts import render


def index(request):
    """
    Vista principal del módulo de reportes.
    """

    context = {
        "titulo": "Ventas",
        "descripcion": "Dashboard, KPIs y exportación de datos.",
        "espiral": "Espiral 7 · W19",
    }

    return render(
        request,
        "ventas/index.html",
        context,
    )