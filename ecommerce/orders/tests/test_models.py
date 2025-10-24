import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
class TestOrderModel:
    def setup_method(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 创建测试分类和商品
        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product1 = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='MacBook Pro',
            slug='macbook-pro',
            price=12999.00,
            stock=50
        )

    def test_create_order(self):
        """测试创建订单"""
        order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        assert order.user == self.user
        assert order.first_name == '张'
        assert order.last_name == '三'
        assert order.email == 'zhangsan@example.com'
        assert order.address == '北京市朝阳区'
        assert order.city == '北京'
        assert order.is_paid is False
        assert str(order) == f'Order {order.id}'

    def test_create_order_item(self):
        """测试创建订单项"""
        order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        # 创建订单项
        order_item1 = OrderItem.objects.create(
            order=order,
            product=self.product1,
            price=self.product1.price,
            quantity=2
        )

        order_item2 = OrderItem.objects.create(
            order=order,
            product=self.product2,
            price=self.product2.price,
            quantity=1
        )

        assert order_item1.order == order
        assert order_item1.product == self.product1
        assert order_item1.price == 5999.00
        assert order_item1.quantity == 2
        assert order_item1.get_cost() == 11998.00

        assert order_item2.get_cost() == 12999.00

    def test_order_total_cost(self):
        """测试订单总成本计算"""
        order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        OrderItem.objects.create(
            order=order,
            product=self.product1,
            price=self.product1.price,
            quantity=2
        )

        OrderItem.objects.create(
            order=order,
            product=self.product2,
            price=self.product2.price,
            quantity=1
        )

        total_cost = order.get_total_cost()
        expected_cost = 5999.00 * 2 + 12999.00
        assert total_cost == expected_cost

    def test_order_ordering(self):
        """测试订单排序"""
        order1 = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区'
        )

        order2 = Order.objects.create(
            user=self.user,
            first_name='李',
            last_name='四',
            email='lisi@example.com',
            address='上海市浦东新区'
        )

        orders = Order.objects.all()
        # 应该按照创建时间倒序排列（最新的在前面）
        assert orders[0] == order2
        assert orders[1] == order1


@pytest.mark.django_db
class TestOrderPaymentFields:
    def setup_method(self):
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

    def test_order_is_paid_field(self):
        """测试订单支付状态字段"""
        order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        # 测试默认值
        assert order.is_paid == False

        # 测试设置支付状态
        order.is_paid = True
        order.save()
        assert order.is_paid == True

    def test_order_payment_method_field(self):
        """测试订单支付方式字段"""
        order = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

        # 测试默认值
        assert order.payment_method is None

        # 测试设置支付方式
        order.payment_method = 'stripe'
        order.save()
        assert order.payment_method == 'stripe'

        order.payment_method = 'paypal'
        order.save()
        assert order.payment_method == 'paypal'

        order.payment_method = 'cod'
        order.save()
        assert order.payment_method == 'cod'