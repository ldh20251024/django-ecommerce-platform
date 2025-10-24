# payment/tests/test_cod_confirmation.py
import pytest
from django.urls import reverse
from django.test import Client
from payment.models import Payment
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
class TestCodConfirmation:
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

    def test_cod_payment_creates_payment_record(self):
        """测试货到付款创建支付记录"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('payment:payment_options', args=[self.order.id]),
            {'payment_method': 'cod'}
        )

        # 验证重定向到成功页面
        assert response.status_code == 302
        assert 'success' in response.url

        # 验证支付记录创建
        payment = Payment.objects.get(order=self.order, payment_method='cod')
        assert payment.payment_status == 'completed'

        # 验证订单状态更新
        self.order.refresh_from_db()
        assert self.order.is_paid == True
        assert self.order.payment_method == 'cod'

    def test_cod_confirmation_in_template(self):
        """测试模板中包含确认对话框"""
        self.client.force_login(self.user)

        response = self.client.get(reverse('payment:payment_options', args=[self.order.id]))
        content = response.content.decode()

        # 验证页面包含必要的元素
        assert '货到付款' in content
        assert '确认货到付款' in content or 'codConfirmationModal' in content