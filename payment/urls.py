app_name = 'payment'

from django.urls import path, include
from .views import (
    PaymentListView,
    PaymentDetailView,
    payment_process,
    esewa_payment_process,
    esewa_payment_success,
    esewa_payment_failure,
    payment_done,
    payment_canceled,
)

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('paypal/<int:booking_id>/<str:amount>/', payment_process, name='paypal-process'),
    path('esewa/<int:booking_id>/<str:amount>/', esewa_payment_process, name='esewa-process'),
    path('esewa-success/', esewa_payment_success, name='esewa_payment_success'),
    path('esewa-failure/', esewa_payment_failure, name='esewa_payment_failure'),
    path('paypal-return/', payment_done, name='payment-done'),
    path('paypal-cancel/', payment_canceled, name='payment-canceled'),
    path('paypal-ipn/', include('paypal.standard.ipn.urls'), name='paypal-ipn'),  # PayPal IPN endpoint
]