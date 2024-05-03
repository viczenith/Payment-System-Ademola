# money_transfer/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('register.urls')),
    path('transactions/', include('register.urls')),
    path('history/', include('register.urls')),
    path('profile/', include('register.urls')),
    path('register/', include('register.urls')),
    path('logout/', include('register.urls')),
    path('login/', include('register.urls')),

    path('deposit_money/', include('register.urls')),
    path('withdraw_money/', include('register.urls')),
    path('change-currency/', include('register.urls')),

    path('create_payment_requests/', include('register.urls')),
    path('view_payment_requests/', include('register.urls')),
    path('accept_payment_request/<int:pk>/', include('register.urls')),
    path('reject_payment_request/<int:pk>/', include('register.urls')),
]
