from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views


urlpatterns = [
    path("", views.bienvenida, name="inicio"),

    path("admin/", admin.site.urls),

    path("", include("django.contrib.auth.urls")),

    path("clientes/", include(("clientes.urls", "clientes"), namespace="clientes")),
    path("proveedores/", include(("proveedores.urls", "proveedores"), namespace="proveedores")),
    path("productos/", include(("productos.urls", "productos"), namespace="productos")),
    path("ventas/", include(("ventas.urls", "ventas"), namespace="ventas")),
    path("reportes/", include(("reportes.urls", "reportes"), namespace="reportes")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

