from django.contrib import admin
from .models import Producto

admin.site.site_header = "Tienda Verde"
admin.site.site_title = "Tienda Verde"
admin.site.index_title = "Panel de administración"

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'disponible')
    search_fields = ('nombre',)

admin.site.register(Producto, ProductoAdmin)

from .models import Pedido, PedidoProducto

class PedidoProductoInline(admin.TabularInline):
    model = PedidoProducto
    extra = 0  

class PedidoAdmin(admin.ModelAdmin):
    inlines = [PedidoProductoInline]
    list_display = ('id', 'usuario', 'fecha', 'estado', 'total')
    list_filter = ('estado', 'usuario')
    search_fields = ('usuario__username',)
    inlines = [PedidoProductoInline]

    #para el vendedor tendremos cambos de solo lectura, solo podrá modificar el estado del pedido

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='Vendedor').exists():
            return ['usuario', 'fecha', 'total']
        return []

admin.site.register(Pedido, PedidoAdmin)
