from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import datetime
from .utils import *
from .forms import *
from .filters import *


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user)

                return redirect('login')

        context = {'form': form}
        return render(request, 'store/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('store')
            else:
                messages.info(request, 'Username OR password is incorrect')

        context = {}
        return render(request, 'store/login.html', context)


def logoutUser(request):
    logout(request)
    return redirect('store')


@login_required(login_url='login')
def profile(request):
    data = cartData(request)
    cartItems = data['cartItems']
    customer = request.user.customer

    completed_orders = []
    for order in Order.objects.all():
        if order.customer == customer and order.complete:
            completed_orders.append(order)

    items = []
    for o in OrderItem.objects.all():
        for order in Order.objects.all():
            if o.order == order:
                items.append(o)

    form = CustomerForm(instance=customer)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        form.save()

    context = {'customer': customer, 'form': form, 'cartItems': cartItems, 'completed_orders': completed_orders,
               'items': items}
    return render(request, 'store/profile.html', context)


def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    products = Product.objects.filter(num_views__gte=0).order_by('-num_views')[:6]
    departments = Department.objects.all()
    context = {'products': products, 'cartItems': cartItems, 'departments': departments}
    return render(request, 'store/store.html', context)


def departmentPage(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    data = cartData(request)
    cartItems = data['cartItems']
    products = Product.objects.filter(gender=department)
    myFilter = ProductFilter(request.GET, queryset=products)
    products = myFilter.qs
    return render(request, "store/department.html", {'cartItems': cartItems, 'department': department, 'products': products, 'myFilter': myFilter})


def productPage(request, product_id):
    data = cartData(request)
    cartItems = data['cartItems']
    product = get_object_or_404(Product, id=product_id)
    product.num_views += 1
    product.save()
    return render(request, "store/product.html", {"product": product, 'cartItems': cartItems})


def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action', action)
    print('ProductId', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment completed', safe=False)


def faq(request):
    data = cartData(request)
    cartItems = data['cartItems']
    return render(request, "store/faq.html", {'cartItems': cartItems, 'index': [0, 1, 2, 3]})


def contact(request):
    data = cartData(request)
    cartItems = data['cartItems']
    return render(request, "store/contact.html", {'cartItems': cartItems})
