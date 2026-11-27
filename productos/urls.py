
"""URLs de la aplicación productos."""

from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [

    path(
        '',
        views.ProductoListView.as_view(),
        name='lista'
    ),

    path(
        '',
        views.ProductoListView.as_view(),
        name='inicio'
    ),

    path(
        'nuevo/',
        views.ProductoCreateView.as_view(),
        name='crear'
    ),

    path(
        '<int:producto_id>/',
        views.ProductoDetailView.as_view(),
        name='detalle'
    ),

    path(
        '<int:producto_id>/editar/',
        views.ProductoUpdateView.as_view(),
        name='editar'
    ),

    path(
        '<int:producto_id>/eliminar/',
        views.ProductoDeleteView.as_view(),
        name='eliminar'
    ),

    path(
        '<int:producto_id>/historico/',
        views.HistoricoProductoView.as_view(),
        name='historico'
    ),
]
