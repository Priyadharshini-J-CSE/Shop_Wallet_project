# from django.urls import path
# from django.contrib.auth import views as auth_views
# from . import views

# urlpatterns = [
# path('', views.index, name='index'),
# path('register/', views.register_view, name='register'),
# path('cart/', views.cart_view, name='cart'),
# path('add/int:product_id/', views.add_to_cart, name='add_to_cart'),
# path('clear/', views.clear_cart, name='clear_cart'),
# path('pay/', views.pay, name='pay'),
# path('recharge/', views.recharge_wallet, name='recharge_wallet'),

# # Authentication
# path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
# path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
# ]
from django.urls import path
from . import views

urlpatterns = [
path('', views.index, name='index'),
path('register/', views.register_view, name='register'),
path('cart/', views.cart_view, name='cart'),
path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
path('update/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
path('clear/', views.clear_cart, name='clear_cart'),
path('pay/', views.pay, name='pay'),
path('process-payment/', views.process_payment, name='process_payment'),
path('recharge/', views.recharge_wallet, name='recharge_wallet'),
path('mongodb-dashboard/', views.mongodb_dashboard, name='mongodb_dashboard'),
]