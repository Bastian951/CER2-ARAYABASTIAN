from django.urls import path
from . import views
from .views import CustomLoginView
from .views import register
from .views import productos_view
from django.contrib.auth import views as auth_views
from .views import agregar_al_carrito, ver_carrito,eliminar_del_carrito
from .views import confirmar_compra



urlpatterns = [
    path('', views.index, name='index'),
    path('productos/', productos_view, name='productos'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('agregar_al_carrito/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('eliminar_del_carrito/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('confirmar_compra/', confirmar_compra, name='confirmar_compra'),

]

