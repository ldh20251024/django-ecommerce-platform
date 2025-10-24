# payment/tests/test_integration.py
import pytest
from django.urls import reverse
from payment.models import Payment
from django.contrib.auth import get_user_model
from django.test import Client
from shop.models import Product, Category
from orders.models import Order, OrderItem

User = get_user_model()

@pytest.mark.django_db
class TestPaymentIntegration:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )

        self.order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )

    def test_complete_payment_flow_cod(self):
        """测试完整的货到付款流程"""
        self.client.force_login(self.user)

        # 1. 访问支付选项页面
        response = self.client.get(reverse('payment:payment_options', args=[self.order.id]))
        assert response.status_code == 200

        # 2. 选择货到付款
        response = self.client.post(
            reverse('payment:payment_options', args=[self.order.id]),
            {'payment_method': 'cod'}
        )

        # 3. 验证重定向到成功页面
        assert response.status_code == 302
        assert response.url == reverse('payment:payment_success', args=[self.order.id])

        # 4. 验证支付记录创建
        payment = Payment.objects.get(order=self.order)
        assert payment.payment_method == 'cod'
        assert payment.payment_status == 'completed'

        # 5. 验证订单状态更新
        self.order.refresh_from_db()
        assert self.order.is_paid == True
        assert self.order.payment_method == 'cod'

        # 6. 访问成功页面
        response = self.client.get(reverse('payment:payment_success', args=[self.order.id]))
        assert response.status_code == 200
        assert '支付成功' in response.content.decode()

    def test_stripe_payment_flow(self, mocker):
        """测试Stripe支付流程"""
        # Mock Stripe API
        mock_intent = mocker.Mock()
        mock_intent.client_secret = 'test_client_secret'
        mock_intent.id = 'test_payment_intent_id'
        mocker.patch('stripe.PaymentIntent.create', return_value=mock_intent)

        self.client.force_login(self.user)

        # 1. 访问Stripe支付页面
        response = self.client.get(reverse('payment:stripe_checkout', args=[self.order.id]))
        assert response.status_code == 200

        # 2. 验证支付记录创建
        payment = Payment.objects.get(order=self.order, payment_method='stripe')
        assert payment.payment_status == 'pending'

        # 3. 创建支付意向
        response = self.client.post(
            reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
            content_type='application/json'
        )
        assert response.status_code == 200

        # 4. 验证支付记录更新
        payment.refresh_from_db()
        assert payment.transaction_id == 'test_payment_intent_id'

    def test_paypal_payment_flow(self):
        """测试PayPal支付流程"""
        self.client.force_login(self.user)

        # 1. 访问PayPal支付页面
        response = self.client.get(reverse('payment:paypal_checkout', args=[self.order.id]))
        assert response.status_code == 200

        # 2. 验证支付记录创建
        payment = Payment.objects.get(order=self.order, payment_method='paypal')
        assert payment.payment_status == 'pending'

        # 3. 模拟PayPal支付成功
        response = self.client.get(reverse('payment:paypal_success', args=[self.order.id]))
        assert response.status_code == 302

        # 4. 验证支付状态更新
        payment.refresh_from_db()
        assert payment.payment_status == 'completed'
        assert payment.transaction_id is not None