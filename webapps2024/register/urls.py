from django.urls import path
from .views import *
from payapp.views import *
from django.contrib.auth.views import *

urlpatterns = [
    path('', home, name='home'),
    path('transfer/', transfer_money, name='transfer_money'),
    path('history/', transaction_history, name='transaction_history'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
    path('profile/', profile, name='profile'),

    path('deposit_money/', DepositView.as_view(), name='deposit_money'),
    path('withdraw_money/', WithdrawView.as_view(), name='withdraw_money'),
    path('transfer_money/', transfer_money, name='transfer_money'),
    path('deposit/profile/', ProfileView.as_view(), name='deposit_profile'),
    path('change-currency/', change_currency, name='change_currency'),

    path('create_payment_requests/', create_payment_request, name='create_payment_requests'),
    path('view_payment_requests/', view_payment_requests, name='view_payment_requests'),
    path('accept_payment_request/<int:request_id>/', accept_payment_request, name='accept_payment_request'),
    path('reject_payment_request/<int:request_id>/', reject_payment_request, name='reject_payment_request'),

]
