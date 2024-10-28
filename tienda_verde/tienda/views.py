from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm
from .models import Carrito, Producto, CarritoProducto, Pedido, PedidoProducto, Producto
from django.contrib import messages


def index(request):
    return render(request, 'tienda/index.html')

def productos(request):
    return render(request, 'tienda/productos.html')


class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
           
            # Según el tipo de usuario vamos a redirigir a distintas secciones
            if user.is_superuser:            
            #Si es admin redirigimos al panel de administración
                return redirect('/admin/') 
            #Si es un vendedor redirigimos al panel de pedidos pero filtrado para pedidos pendientes
            elif user.groups.filter(name='Vendedor').exists():
                return redirect('/admin/tienda/pedido/?estado__exact=pendiente')  

            #Si es un usuario normal entonces redirigimos al inicio     
            else:
                return redirect('/')  
        else:
            #Si es incorrecto renderizamos la pagina de inicio con un un mensaje de error
            return render(request, 'tienda/index.html', {
                'error': 'Usuario o contraseña incorrectos.',
                'user': request.user  
            })

    def get(self, request, *args, **kwargs):
        return redirect('/')  #Redirigir al inicio si no es un POST


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password']) 
            user.save()
            #Al registrarse iniciaremos sesión automaticamente
            login(request, user)  
            #Redirigimos al inicio
            return redirect('index')  
    else:
        form = UserRegistrationForm()

    # Renderizamos el formulario en la página de registro.
    return render(request, 'tienda/register.html', {'form': form})


def productos_view(request):
    #Filtramos los productos disponibles de la base
    productos = Producto.objects.filter(disponible=True) 
    
    #Renderizamos los productos en productos.html
    return render(request, 'tienda/productos.html', {'productos': productos})


def agregar_al_carrito(request, producto_id):

    # Verificamos si el usuario está registrado. Si no lo está, lo redirigimos a la página de registro.

    if not request.user.is_authenticated:
        return redirect('register') 

    #Mapeamos el producto
    producto = Producto.objects.get(id=producto_id)
    
    #Creamos u obtenemos el objeto carrito para el usuario.
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    #Creamos u obtenemos el objeto carrito_producto para el producto en el carrito.
    carrito_producto, created = CarritoProducto.objects.get_or_create(carrito=carrito, producto=producto)
    
    #Añadimos una unidad del producto al objeto carrito_producto
    if not created:
        carrito_producto.cantidad += 1
        carrito_producto.save()

    #Si el usuario apretó el botón comprar, iremos directo al carrito
    if request.POST.get('comprar') is not None:
        return redirect('ver_carrito')

    #Almacenamos un mensaje de exito que mostraremos al redirigir a productos
    messages.success(request, f'{producto.nombre} agregado al carrito.')
    return redirect('productos') 

def ver_carrito(request):
    #Seleccionamos el carrito
    carrito = Carrito.objects.get(usuario=request.user)
    
    #Seleccionamos los productos del carrito
    productos = CarritoProducto.objects.filter(carrito=carrito)

    #Obtenemos el total multiplicando el precio por la cantidad para cada producto
    total = sum(item.producto.precio * item.cantidad for item in productos)

    #Almacenamos los subtotales por producto en un diccionario
    productos_con_subtotales = [
        {
            'producto': item.producto,
            'cantidad': item.cantidad,
            'subtotal': item.producto.precio * item.cantidad,
            'id': item.id 
        }
        for item in productos
    ]
    
    #Renderizamos la información de productos en carrito.html 
    return render(request, 'tienda/carrito.html', {'productos': productos_con_subtotales, 'total': total})


def eliminar_del_carrito(request, item_id):
    #Obtenemos el carrito
    carrito = Carrito.objects.get(usuario=request.user)
    #Intentamos eliminar el producto del carrito, para eso debemos hacer el match con el id
    try:
        carrito_producto = CarritoProducto.objects.get(id=item_id, carrito=carrito)
        carrito_producto.delete()
    except CarritoProducto.DoesNotExist:
        print(f'No se encontró CarritoProducto con id {item_id} para el carrito del usuario {request.user.username}.')

    return redirect('ver_carrito')


def carrito(request):
    productos_ids = request.session.get('carrito', {})
    
    productos = []
    total = 0

    for producto_id, cantidad in productos_ids.items():
        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        total += subtotal
        productos.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })

    return render(request, 'tienda/carrito.html', {'productos': productos, 'total': total})


def confirmar_compra(request):
    
    # Obtenemos el carrito del usuario
    carrito = Carrito.objects.get(usuario=request.user)
    
    #Filtramos los productos del carrito
    productos = CarritoProducto.objects.filter(carrito=carrito)

    if productos.exists():
        #Calculamos el total
        total = sum(item.producto.precio * item.cantidad for item in productos)

        #Creamos un nuevo pedido
        pedido = Pedido.objects.create(usuario=request.user, total=total)

        #Registramos los productos del pedido
        for item in productos:
            PedidoProducto.objects.create(pedido=pedido, producto=item.producto, cantidad=item.cantidad)
            #Vamos limpiando el carrito al insertar al pedido
            item.delete() 

        #Una vez el pedido esté ingresado mostramos el mensaje de confirmación
        return render(request, 'tienda/compra_confirmada.html', {'mensaje': 'Compra ingresada con éxito.'})

    return render(request, 'tienda/compra_confirmada.html', {'mensaje': 'No hay productos en el carrito.'})


def ver_productos(request):
    #Seleccionamos el carrito del usuario
    carrito = Carrito.objects.get(usuario=request.user)
    #Seleccionamos los productos del carrito
    productos_carrito = CarritoProducto.objects.filter(carrito=carrito)

    productos_disponibles = Producto.objects.all()

    return render(request, 'tienda/productos_con_carrito.html', {
        'productos': productos_disponibles,
        'productos_carrito': productos_carrito
    })
