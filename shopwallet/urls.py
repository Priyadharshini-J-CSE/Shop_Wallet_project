from django.contrib import admin
from django.urls import path, include
from store.views import register_view, process_payment

urlpatterns = [
    path('admin/', admin.site.urls),
    # First page: user registration
    path('', register_view, name='home'),  # Root redirects to register

    # Registration URL
    path('accounts/register/', register_view, name='register'),

    # Auth URLs (login/logout handled by Django)
    path('accounts/', include('django.contrib.auth.urls')),

    # Store app routes
    path('store/', include('store.urls')),

    # Payment processing (direct route for form submission)
    path('process-payment/', process_payment, name='process_payment'),
]