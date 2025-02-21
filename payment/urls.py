from django.urls import path
from .views import PaymentListView, PaymentDetailView, payment_process, payment_done, payment_canceled, handle_ipn
from payment import views
urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('paypal/<int:payment_id>/', views.payment_process, name='payment_process'),
    path('paypal-return/', views.payment_done, name='payment-done'),
    path('paypal-cancel/', views.payment_canceled, name='payment-canceled'),
    path('paypal-ipn/', views.handle_ipn, name='paypal-ipn'),
]


