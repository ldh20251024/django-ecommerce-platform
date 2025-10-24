# payment/tests/test_models.py
import pytest
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from orders.models import Order, OrderItem
from payment.models import Payment

User = get_user_model()


@pytest.mark.django_db
class TestPaymentModel:
    def setup_method(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 创建测试分类和商品
        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )

        # 创建订单
        self.order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        # 创建订单项
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )

    def test_create_payment(self):
        """测试创建支付记录"""
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            amount=self.order.get_total_cost()
        )

        assert payment.order == self.order
        assert payment.user == self.user
        assert payment.payment_method == 'stripe'
        assert payment.amount == 5999.00 * 2
        assert payment.payment_status == 'pending'
        assert str(payment) == f"支付 #{payment.id} - 信用卡支付 - ¥{payment.amount}"

    def test_payment_status_choices(self):
        """测试支付状态选项"""
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='paypal',
            amount=self.order.get_total_cost()
        )

        # 测试支付状态默认值
        assert payment.payment_status == 'pending'

        # 测试支付状态选择
        payment.payment_status = 'completed'
        payment.save()
        assert payment.payment_status == 'completed'

        payment.payment_status = 'failed'
        payment.save()
        assert payment.payment_status == 'failed'

    def test_payment_method_choices(self):
        """测试支付方式选项"""
        # 测试Stripe支付
        stripe_payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            amount=self.order.get_total_cost()
        )
        assert stripe_payment.payment_method == 'stripe'
        assert stripe_payment.get_payment_method_display() == '信用卡支付'

        # 测试PayPal支付
        paypal_payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='paypal',
            amount=self.order.get_total_cost()
        )
        assert paypal_payment.payment_method == 'paypal'
        assert paypal_payment.get_payment_method_display() == 'PayPal'

        # 测试货到付款
        cod_payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='cod',
            amount=self.order.get_total_cost()
        )
        assert cod_payment.payment_method == 'cod'
        assert cod_payment.get_payment_method_display() == '货到付款'

    def test_payment_ordering(self):
        """测试支付记录排序（按创建时间倒序）"""
        payment1 = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            amount=self.order.get_total_cost()
        )

        payment2 = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='paypal',
            amount=self.order.get_total_cost()
        )

        payments = Payment.objects.all()
        # 应该按照创建时间倒序排列（最新的在前面）
        assert payments[0] == payment2
        assert payments[1] == payment1

    def test_payment_with_transaction_id(self):
        """测试带交易ID的支付记录"""
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='stripe',
            payment_status='completed',
            amount=self.order.get_total_cost(),
            transaction_id='pi_123456789'
        )

        assert payment.transaction_id == 'pi_123456789'
        assert payment.payment_status == 'completed'