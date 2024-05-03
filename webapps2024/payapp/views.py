from register.models import PaymentRequest
from register.forms import PaymentRequestForm, TransactionForm
from django import forms
import logging
from decimal import Decimal
from register.forms import CustomUserCreationForm, DepositForm
from register.models import Transaction
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from register.models import Profile
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

def transfer_money(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)

            if transaction.amount > request.user.profile.total_balance:
                messages.error(request, 'Insufficient balance. Please check your balance.')
                return redirect('transfer_money')

            transaction.sender = request.user
            transaction.balance_after_transaction = request.user.profile.total_balance - transaction.amount
            transaction.receiver = form.cleaned_data['receiver_email']
            
            
            if transaction.amount > 0:
                transaction.transaction_type = 'Deposit'
            elif transaction.amount < 0:
                transaction.transaction_type = 'Withdrawal'
            else:
                transaction.transaction_type = 'Transfer'
            
            transaction.save()

            request.user.profile.total_balance = transaction.balance_after_transaction
            request.user.profile.save()

            transaction.receiver.profile.total_balance += transaction.amount
            transaction.receiver.profile.save()

            messages.success(request, f'Transaction successful! Your money has been transferred. ${transaction.amount}')

            return redirect('transfer_money')

    else:
        form = TransactionForm()

    return render(request, 'transfer_money.html', {'form': form})



def transaction_history(request):
    if request.user.is_authenticated:
        transactions = Transaction.objects.filter(sender=request.user)
        return render(request, 'transaction_history.html', {'transactions': transactions})
    else:
        pass


@login_required
def profile(request):
    user = request.user
    sent_transactions = Transaction.objects.filter(sender=user)
    received_transactions = Transaction.objects.filter(receiver=user)
    return render(request, 'profile.html', {'user': user, 'sent_transactions': sent_transactions, 'received_transactions': received_transactions})



class ProfileView(LoginRequiredMixin, View):
    template_name = 'profile.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


def change_currency(request):
    if request.method == 'POST':
        new_currency = request.POST.get('new_currency')
        user = request.user

        # Conversion rates
        GBP_to_USD_rate = Decimal('1.37')
        GBP_to_EUR_rate = Decimal('1.17')
        USD_to_EUR_rate = Decimal('0.86')

        initial_amount_gbp = user.profile.total_balance

        if new_currency == '£':
            converted_amount = initial_amount_gbp
        elif new_currency == '$':
            converted_amount = initial_amount_gbp / GBP_to_USD_rate
        elif new_currency == '€':
            converted_amount = initial_amount_gbp / GBP_to_EUR_rate
        else:
            messages.error(request, 'Unsupported currency selected.')
            return redirect('change_currency')

        user.profile.total_balance = converted_amount
        user.profile.save()

        user.change_currency = new_currency
        user.save()

        messages.success(request, 'Currency conversion successful.')
        return redirect('profile')

    else:
        user = request.user
        context = {
            'user': user,
        }
        return render(request, 'change_currency.html', context)


class DepositForm(forms.Form):
    amount = forms.DecimalField(label='Amount', min_value=0, required=True)



@method_decorator(login_required, name='dispatch')
class DepositView(View):
    template_name = 'deposit_money.html'

    def get(self, request):
        form = DepositForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            if amount > 0:
                request.user.profile.total_balance += amount
                request.user.profile.save()

                Transaction.objects.create(
                    sender=request.user,
                    receiver=None,
                    amount=amount 
                )

                return redirect('profile')

        return render(request, self.template_name, {'form': form})



logger = logging.getLogger(__name__)



class WithdrawView(View):
    template_name = 'withdraw_money.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Withdrawal amount must be greater than zero.")

            user = request.user
            profile = Profile.objects.select_for_update().get(user=user)

            if profile.total_balance >= amount:
                
                profile.total_balance -= amount
                profile.save()

                messages.success(request, f'Withdrawal of ${amount} successful!')
                return redirect('withdraw_money')
            
            else:
                messages.error(request, 'Insufficient funds for withdrawal.')
        except ValueError as e:
            logger.error(f"Invalid withdrawal amount: {e}")
            messages.error(request, 'Invalid withdrawal amount. Please enter a valid positive number.')
        except Profile.DoesNotExist:
            
            logger.error("User profile not found.")
            messages.error(request, 'User profile not found. Please contact support.')
        except Exception as e:
            
            logger.exception("An unexpected error occurred during withdrawal.")
            messages.error(request, 'An unexpected error occurred. Please try again later.')

        return render(request, self.template_name, {'messages': messages.get_messages(request)})


@login_required
def create_payment_request(request):
    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            payment_request.requester = request.user
            payment_request.save()
            messages.success(request, 'Payment request created successfully.')
            return redirect('create_payment_requests')
        else:
            messages.error(request, 'Invalid form data. Please correct the errors.')
    else:
        form = PaymentRequestForm()
    return render(request, 'create_payment_request.html', {'form': form})

@login_required
def view_payment_requests(request):
    payment_requests = PaymentRequest.objects.filter(recipient=request.user).order_by('-id')
    return render(request, 'view_payment_requests.html', {'payment_requests': payment_requests})

@login_required
def accept_payment_request(request, request_id):
    payment_request = get_object_or_404(PaymentRequest, id=request_id)

    if not payment_request.is_accepted:
        if payment_request.amount > payment_request.recipient.profile.total_balance:
            messages.error(request, 'Insufficient balance. Please check your balance.')
            return redirect('view_payment_requests')
        
        payment_request.is_accepted = True
        payment_request.save()

        
        payment_request.requester.profile.total_balance += payment_request.amount
        payment_request.requester.profile.save()

        payment_request.recipient.profile.total_balance -= payment_request.amount
        payment_request.recipient.profile.save()

        messages.success(request, 'Payment request accepted successfully.')
    else:
        messages.error(request, 'Payment request has already been accepted.')

    return redirect('view_payment_requests')

@login_required
def reject_payment_request(request, request_id):
    payment_request = get_object_or_404(PaymentRequest, id=request_id)

    if payment_request.is_accepted:
        messages.error(request, 'Cannot reject an already accepted payment request.')
    else:
        payment_request.delete()
        messages.success(request, 'Payment request rejected successfully.')

    return redirect('view_payment_requests')