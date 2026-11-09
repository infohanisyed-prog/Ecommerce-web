
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path(
    'update-cart/<int:product_id>/<str:action>/',
    views.update_cart_quantity,
    name='update_cart_quantity'
),
path('checkout/', views.checkout, name='checkout'),
path('track-order/', views.track_order, name='track_order'),
path('profile/', views.profile_view, name='profile'),
path('my-orders/', views.my_orders, name='my_orders'),

path('wishlist/', views.wishlist_view, name='wishlist'),

path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),

path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

path('order-status/', views.order_status, name='order_status'),
path('signup/', views.signup_view, name='signup'),
path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
]
