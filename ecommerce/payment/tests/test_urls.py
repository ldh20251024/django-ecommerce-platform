# payment/tests/test_urls.py
import pytest
from django.urls import reverse, resolve
from payment import views


@pytest.mark.django_db
class TestPaymentURLs:
    def test_payment_options_url(self):
        """测试支付选项URL"""
        url = reverse('payment:payment_options', args=[1])
        assert resolve(url).func == views.payment_options

    def test_stripe_checkout_url(self):
        """测试Stripe支付URL"""
        url = reverse('payment:stripe_checkout', args=[1])
        assert resolve(url).func == views.stripe_checkout

    def test_paypal_checkout_url(self):
        """测试PayPal支付URL"""
        url = reverse('payment:paypal_checkout', args=[1])
        assert resolve(url).func == views.paypal_checkout

    def test_payment_success_url(self):
        """测试支付成功URL"""
        url = reverse('payment:payment_success', args=[1])
        assert resolve(url).func == views.payment_success

    def test_create_stripe_payment_intent_url(self):
        """测试创建Stripe支付意向URL"""
        url = reverse('payment:create_stripe_payment_intent', args=[1])
        assert resolve(url).func == views.create_stripe_payment_intent

    def test_stripe_payment_success_url(self):
        """测试Stripe支付成功URL"""
        url = reverse('payment:stripe_payment_success', args=[1])
        assert resolve(url).func == views.stripe_payment_success

    def test_paypal_success_url(self):
        """测试PayPal支付成功URL"""
        url = reverse('payment:paypal_success', args=[1])
        assert resolve(url).func == views.paypal_success

    def test_payment_cancel_url(self):
        """测试支付取消URL"""
        url = reverse('payment:payment_cancel', args=[1])
        assert resolve(url).func == views.payment_cancel

    def test_stripe_webhook_url(self):
        """测试Stripe Webhook URL"""
        url = reverse('payment:stripe_webhook')
        assert resolve(url).func == views.stripe_webhook