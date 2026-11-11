
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Product, Order, OrderItem, Wishlist
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm, CustomSignupForm
import random
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import EmailOTP
from .forms import CustomSignupForm

def get_cart_count(request):
    cart = request.session.get('cart', {})
    return sum(cart.values())


def home(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    products = Product.objects.all()

    if category in ['electronics', 'fashion', 'accessories']:
        products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'store/home.html', {
        'products': products,
        'query': query,
        'category': category,
        'cart_count': get_cart_count(request),
    })

def add_to_cart(request, product_id):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        cart = request.session.get('cart', {})

        product_id = str(product.id)

        cart[product_id] = cart.get(product_id, 0) + 1

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('home')


def cart(request):
    cart_data = request.session.get('cart', {})

    products = Product.objects.filter(id__in=cart_data.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart_data.get(str(product.id), 0)
        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': get_cart_count(request),
    })


def remove_from_cart(request, product_id):
    
    if request.method == 'POST':
        cart_data = request.session.get('cart', {})
        cart_data.pop(str(product_id), None)

        request.session['cart'] = cart_data
        request.session.modified = True

    return redirect('cart')
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    is_in_wishlist = False

    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_count': get_cart_count(request),
        'is_in_wishlist': is_in_wishlist,
    })
def update_cart_quantity(request, product_id, action):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id = str(product_id)

        if product_id in cart:

            if action == 'increase':
                cart[product_id] += 1

            elif action == 'decrease':
                cart[product_id] -= 1

                if cart[product_id] <= 0:
                    del cart[product_id]

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart')
def checkout(request):

    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():

        product = get_object_or_404(Product, id=product_id)

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if request.method == 'POST':

        customer_name = request.POST.get('customer_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if customer_name and email and phone and address:

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                customer_name=customer_name,
                email=email,
                phone=phone,
                address=address,
                total_amount=total
            )

            for item in cart_items:

                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price
                )

            request.session['cart'] = {}
            request.session.modified = True

            return render(
                request,
                'store/order_success.html',
                {'order': order}
            )

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': get_cart_count(request),
    })
def track_order(request):

    order = None
    error = False

    if request.method == 'POST':

        order_id = request.POST.get('order_id')
        email = request.POST.get('email')

        if order_id and email:
            order = Order.objects.filter(
                id=order_id,
                email__iexact=email
            ).first()

            if order is None:
                error = True

    return render(request, 'store/track_order.html', {
        'order': order,
        'error': error,
    })
# Signup View
def signup_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomSignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            otp = str(random.randint(100000, 999999))

            EmailOTP.objects.update_or_create(
                user=user,
                defaults={
                    'otp': otp,
                    'created_at': timezone.now(),
                    'attempts': 0
                }
            )

            send_mail(
                'NEXORA Email Verification OTP',
                f'Your OTP is {otp}. It is valid for 5 minutes.',
                None,
                [user.email],
                fail_silently=False,
            )

            request.session['otp_user_id'] = user.id

            return redirect('verify_otp')

    else:
        form = CustomSignupForm()

    return render(request, 'store/signup.html', {
        'form': form,
    })
def verify_otp_view(request):

    user_id = request.session.get('otp_user_id')

    if not user_id:
        return redirect('signup')

    user = get_object_or_404(User, id=user_id)

    otp_record = EmailOTP.objects.filter(user=user).first()

    if not otp_record:
        return redirect('signup')

    if timezone.now() - otp_record.created_at > timedelta(minutes=5):
        otp_record.delete()
        messages.error(request, 'OTP expired. Please sign up again.')
        return redirect('signup')

    if request.method == 'POST':

        entered_otp = request.POST.get('otp', '').strip()

        if otp_record.attempts >= 5:
            messages.error(request, 'Too many attempts. Please sign up again.')
            return redirect('signup')

        otp_record.attempts += 1
        otp_record.save(update_fields=['attempts'])

        if entered_otp == otp_record.otp:

            user.is_active = True
            user.save(update_fields=['is_active'])

            otp_record.delete()
            request.session.pop('otp_user_id', None)

            messages.success(request, 'Email verified! You can now log in.')
            return redirect('login')

        messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'store/verify_otp.html')

# Login View
def login_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')

    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {
        'form': form,
    })


# Logout View
def logout_view(request):

    if request.method == 'POST':
        logout(request)

    return redirect('home')

@login_required
def profile_view(request):

    edit_mode = request.GET.get('edit') == '1'

    if request.method == 'POST':

        form = ProfileUpdateForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Your profile has been updated successfully!'
            )

            return redirect('profile')

        edit_mode = True

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'store/profile.html', {
        'form': form,
        'edit_mode': edit_mode,
        'cart_count': get_cart_count(request),
    })

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/my_orders.html', {
        'orders': orders,
        'cart_count': get_cart_count(request),
    })


@login_required
def wishlist_view(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product')

    return render(request, 'store/wishlist.html', {
        'wishlist_items': wishlist_items,
        'cart_count': get_cart_count(request),
    })


@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    

    return redirect('wishlist')


@login_required
def remove_from_wishlist(request, product_id):

    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()


    return redirect('wishlist')


@login_required
def order_status(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/order_status.html', {
        'orders': orders,
        'cart_count': get_cart_count(request),
    })
