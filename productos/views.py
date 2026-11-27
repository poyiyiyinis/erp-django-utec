
"""
Vistas del módulo de productos e inventario — ERP Django.
"""

from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ProductoForm
from .models import Producto


# ─────────────────────────────────────────────────────────────
# VISTA DE LISTADO
# ─────────────────────────────────────────────────────────────

class ProductoListView(ListView):
    """Lista paginada de productos activos."""

    model = Producto
    template_name = 'productos/lista.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        return (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )


# ─────────────────────────────────────────────────────────────
# DETALLE DEL PRODUCTO
# ─────────────────────────────────────────────────────────────

class ProductoDetailView(DetailView):
    """Detalle individual de un producto."""

    model = Producto
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'
    pk_url_kwarg = 'producto_id'

    def get_queryset(self):
        return Producto.objects.select_related(
            'categoria',
            'proveedor'
        )


# ─────────────────────────────────────────────────────────────
# CREAR PRODUCTO
# ─────────────────────────────────────────────────────────────

class ProductoCreateView(LoginRequiredMixin, CreateView):
    """Formulario para registrar un nuevo producto."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/crear.html'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" creado exitosamente.'
        )

        return response


# ─────────────────────────────────────────────────────────────
# EDITAR PRODUCTO
# ─────────────────────────────────────────────────────────────

class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    """Formulario para editar un producto existente."""

    model = Producto
    form_class = ProductoForm
    template_name = 'productos/editar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" actualizado.'
        )

        return response


# ─────────────────────────────────────────────────────────────
# ELIMINAR PRODUCTO
# ─────────────────────────────────────────────────────────────

class ProductoDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView
):
    """Confirmación y eliminación de un producto."""

    model = Producto
    template_name = 'productos/eliminar.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('productos:lista')

    permission_required = 'productos.delete_producto'

    def form_valid(self, form):
        nombre = self.object.nombre

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'Producto "{nombre}" eliminado.'
        )

        return response


# ─────────────────────────────────────────────────────────────
# HISTORIAL DE CAMBIOS
# ─────────────────────────────────────────────────────────────

class HistoricoProductoView(LoginRequiredMixin, TemplateView):
    """Muestra el historial de cambios de precio y stock."""

    template_name = 'productos/historico.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        producto = get_object_or_404(
            Producto,
            pk=kwargs['producto_id']
        )

        registros_raw = list(producto.history.all()[:100])
        registros_anotados = []

        for i, registro in enumerate(registros_raw):
            cambios = {}

            if i < len(registros_raw) - 1:
                anterior = registros_raw[i + 1]
                delta = registro.diff_against(anterior)

                for cambio in delta.changes:
                    cambios[cambio.field] = {
                        'anterior': cambio.old,
                        'nuevo': cambio.new,
                    }

            registros_anotados.append({
                'registro': registro,
                'cambios': cambios,
                'es_creacion': registro.history_type == '+',
                'es_borrado': registro.history_type == '-',
                'precio_cambio': 'precio' in cambios,
                'stock_cambio': 'stock' in cambios,
            })

        ctx['producto'] = producto
        ctx['registros'] = registros_anotados
        ctx['total'] = producto.history.count()

        return ctx
