# payment/urls.py
from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('options/<int:order_id>/', views.payment_options, name='payment_options'),
    path('stripe/<int:order_id>/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/create-payment-intent/<int:order_id>/',
         views.create_stripe_payment_intent, name='create_stripe_payment_intent'),
    path('stripe/success/<int:order_id>/', views.stripe_payment_success, name='stripe_payment_success'),
    path('paypal/<int:order_id>/', views.paypal_checkout, name='paypal_checkout'),
    path('paypal/success/<int:order_id>/', views.paypal_success, name='paypal_success'),
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]