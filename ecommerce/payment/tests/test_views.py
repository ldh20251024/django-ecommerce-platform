# payment/tests/test_views.py
import pytest
import json
from django.urls import reverse
from django.test import Client
from payment.models import Payment
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from orders.models import Order, OrderItem
from unittest.mock import Mock, patch

User = get_user_model()


@pytest.mark.django_db
class TestPaymentViews:
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

    def test_payment_options_view_requires_login(self):
        """测试支付选项页面需要登录"""
        response = self.client.get(reverse('payment:payment_options', args=[self.order.id]))
        assert response.status_code == 302  # 重定向到登录页面

    def test_payment_options_view_authenticated(self):
        """测试已登录用户访问支付选项页面"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment:payment_options', args=[self.order.id]))
        assert response.status_code == 200
        assert '选择支付方式' in response.content.decode()
        assert '信用卡/借记卡支付' in response.content.decode()
        assert 'PayPal' in response.content.decode()
        assert '货到付款' in response.content.decode()

    def test_payment_options_post_cod(self):
        """测试选择货到付款"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment:payment_options', args=[self.order.id]),
            {'payment_method': 'cod'}
        )

        assert response.status_code == 302  # 重定向到成功页面
        # 检查支付记录是否创建
        payment = Payment.objects.get(order=self.order, payment_method='cod')
        assert payment.payment_status == 'completed'

        # 刷新订单对象
        self.order.refresh_from_db()
        assert self.order.is_paid == True
        assert self.order.payment_method == 'cod'

    def test_payment_options_post_stripe(self):
        """测试选择Stripe支付"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment:payment_options', args=[self.order.id]),
            {'payment_method': 'stripe'}
        )

        assert response.status_code == 302  # 重定向到Stripe支付页面
        # 检查支付记录是否创建
        payment = Payment.objects.get(order=self.order, payment_method='stripe')
        assert payment.payment_status == 'pending'

    def test_payment_options_post_paypal(self):
        """测试选择PayPal支付"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment:payment_options', args=[self.order.id]),
            {'payment_method': 'paypal'}
        )

        assert response.status_code == 302  # 重定向到PayPal支付页面
        # 检查支付记录是否创建
        payment = Payment.objects.get(order=self.order, payment_method='paypal')
        assert payment.payment_status == 'pending'

    def test_payment_success_view(self):
        """测试支付成功页面"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment:payment_success', args=[self.order.id]))
        assert response.status_code == 200
        assert '支付成功' in response.content.decode()

    def test_stripe_checkout_view(self):
        """测试Stripe支付页面"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment:stripe_checkout', args=[self.order.id]))
        assert response.status_code == 200
        assert '信用卡支付' in response.content.decode()

    def test_paypal_checkout_view(self):
        """测试PayPal支付页面"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('payment:paypal_checkout', args=[self.order.id]))
        assert response.status_code == 200
        assert 'PayPal' in response.content.decode()


@pytest.mark.django_db
class TestStripePaymentFlow:
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

    def test_create_stripe_payment_intent_requires_auth(self):
        """测试创建Stripe支付意向需要认证"""
        response = self.client.post(
            reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
            content_type='application/json'
        )
        assert response.status_code == 302  # 重定向到登录

    def test_create_stripe_payment_intent_with_mock(self, mocker):
        """测试创建Stripe支付意向（使用mock）"""

        # 首先创建支付记录
        Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            payment_status='pending',
            amount=self.order.get_total_cost()
        )
        # Mock Stripe API
        mock_intent = mocker.Mock()
        mock_intent.client_secret = 'test_client_secret'
        mock_intent.id = 'test_payment_intent_id'

        mocker.patch('stripe.PaymentIntent.create', return_value=mock_intent)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'clientSecret' in data
        assert data['clientSecret'] == 'test_client_secret'

        # 验证支付记录被更新
        payment = Payment.objects.get(order=self.order, payment_method='stripe')
        assert payment.transaction_id == 'test_payment_intent_id'



# payment/tests/test_views.py (添加更多测试)
@pytest.mark.django_db
class TestStripePaymentFlowRobust:
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

    def test_create_stripe_payment_intent_creates_payment_if_not_exists(self):
        """测试如果支付记录不存在，会自动创建"""

        # with patch 是 Python unittest.mock 模块中的一个上下文管理器，
        # 用于临时替换代码中的对象、函数或类。它的主要作用包括：
        # 模拟外部依赖：在测试中替换对外部服务（如StripeAPI、数据库、网络请求）的调用
        # 控制返回值：可以预设被替换对象的返回值
        # 验证调用：检查被替换对象是否被正确调用，以及调用参数
        # 隔离测试：确保测试不依赖外部系统的可用性

        # 在with 块内部，所有对 payment.views.stripe.PaymentIntent.create 的调用
        # 都会被重定向到 mock_create 对象，而不是真正的Stripe API。
        # patch和mock在此处的作用是模拟外部服务，而不用真正调用stripe的api。避免产生费用
        # 直接调用真实Stripe API
        # result = stripe.PaymentIntent.create(amount=1000, currency='usd')

        # 问题：
        # 1. 需要真实的API密钥
        # 2. 会产生真实的交易费用
        # 3. 依赖网络连接
        # 4. 测试速度慢
        # 5. 无法测试错误情况
        with patch('payment.views.stripe.PaymentIntent.create') as mock_create:
            mock_intent = Mock()
            mock_intent.client_secret = 'test_client_secret'
            mock_intent.id = 'test_payment_intent_id'
            mock_create.return_value = mock_intent

            self.client.force_login(self.user)

            # 确保开始时没有支付记录
            assert not Payment.objects.filter(order=self.order, payment_method='stripe').exists()

            response = self.client.post(
                reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
                content_type='application/json'
            )

            assert response.status_code == 200

            # 验证支付记录被创建
            payment = Payment.objects.get(order=self.order, payment_method='stripe')
            assert payment.transaction_id == 'test_payment_intent_id'
            assert payment.payment_status == 'pending'

    def test_create_stripe_payment_intent_updates_existing_payment(self):
        """测试如果支付记录存在，会更新现有记录"""
        # 先创建支付记录
        existing_payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            payment_status='pending',
            amount=self.order.get_total_cost()
        )

        with patch('payment.views.stripe.PaymentIntent.create') as mock_create:
            mock_intent = Mock()
            mock_intent.client_secret = 'test_client_secret'
            mock_intent.id = 'test_payment_intent_id'
            mock_create.return_value = mock_intent

            self.client.force_login(self.user)

            response = self.client.post(
                reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
                content_type='application/json'
            )

            assert response.status_code == 200

            # 验证现有支付记录被更新
            existing_payment.refresh_from_db()
            assert existing_payment.transaction_id == 'test_payment_intent_id'

    def test_create_stripe_payment_intent_stripe_error(self):
        """测试Stripe API错误处理"""
        with patch('payment.views.stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = Exception("Stripe API Error")

            self.client.force_login(self.user)

            response = self.client.post(
                reverse('payment:create_stripe_payment_intent', args=[self.order.id]),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.content)
            assert 'error' in data
            assert 'Stripe API Error' in data['error']