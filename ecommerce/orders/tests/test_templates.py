import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
class TestOrderTemplates:
    def setup_method(self):
        self.client = Client()

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

        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )

    def test_order_create_template(self):
        """测试订单创建模板"""
        self.client.force_login(self.user)

        # 添加商品到购物车
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'update': False}
        )

        response = self.client.get(reverse('orders:order_create'))
        assert response.status_code == 200

        content = response.content.decode()
        assert '创建订单' in content
        assert 'iPhone 13' in content
        assert '11998.00' in content  # 5999 * 2

    def test_order_detail_template(self):
        """测试订单详情模板"""
        self.client.force_login(self.user)

        response = self.client.get(reverse('orders:order_detail', args=[self.order.id]))
        assert response.status_code == 200

        content = response.content.decode()
        assert '订单详情' in content
        assert 'iPhone 13' in content
        assert '11998.00' in content
        assert '张' in content
        assert '三' in content

    def test_order_list_template(self):
        """测试订单列表模板"""
        self.client.force_login(self.user)

        # 创建第二个订单
        order2 = Order.objects.create(
            user=self.user,
            first_name='李',
            last_name='四',
            email='lisi@example.com',
            address='上海市浦东新区',
            postal_code='200000',
            city='上海'
        )

        response = self.client.get(reverse('orders:order_list'))
        assert response.status_code == 200

        content = response.content.decode()
        assert '我的订单' in content
        assert '张' in content
        assert '李' in content
        assert '三' in content
        assert '四' in content