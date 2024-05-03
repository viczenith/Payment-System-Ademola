from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.views.generic.edit import CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile
import os
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse

def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            currency = form.cleaned_data['change_currency']

            baseline_amount_gbp = 1000
            GBP_to_USD_rate = 1.36
            GBP_to_EUR_rate = 1.17
            USD_to_EUR_rate = 0.86

            if currency == '£':
                initial_amount = baseline_amount_gbp
            elif currency == '$':
                initial_amount = baseline_amount_gbp
            elif currency == '€':
                initial_amount = baseline_amount_gbp
            else:
                messages.error(request, 'Incorrect currency selected')
                return redirect('register')

            user.save()

            if hasattr(user, 'profile'):
                profile = user.profile
            else:
                profile = Profile.objects.create(user=user, total_balance=initial_amount)

            profile.save()

            
            login(request, user)

            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})



def user_logout(request):
    logout(request)
    return redirect('/')
