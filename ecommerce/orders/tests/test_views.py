import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from shop.models import Product, Category
from cart.cart import Cart

User = get_user_model()


@pytest.mark.django_db
class TestOrderViews:
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

    def test_order_create_view_get(self):
        """测试订单创建页面GET请求"""
        # 先登录用户
        self.client.force_login(self.user)

        # 添加商品到购物车
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'update': False}
        )

        response = self.client.get(reverse('orders:order_create'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'cart' in response.context

    def test_order_create_view_post_success(self):
        """测试成功创建订单"""
        self.client.force_login(self.user)

        # 添加商品到购物车
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'update': False}
        )

        form_data = {
            'first_name': '张',
            'last_name': '三',
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            'postal_code': '100000',
            'city': '北京'
        }

        response = self.client.post(reverse('orders:order_create'), form_data)

        # 创建成功后应该重定向到订单详情页
        assert response.status_code == 302
        assert '/orders/detail/' in response.url

    def test_order_create_empty_cart(self):
        """测试空购物车创建订单"""
        self.client.force_login(self.user)

        response = self.client.get(reverse('orders:order_create'))
        # 空购物车应该重定向回购物车页面
        assert response.status_code == 302
        assert reverse('cart:cart_detail') in response.url

    def test_order_detail_view(self):
        """测试订单详情页面"""
        self.client.force_login(self.user)

        # 先创建订单
        from orders.models import Order, OrderItem
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
            product=self.product,
            price=self.product.price,
            quantity=2
        )

        response = self.client.get(reverse('orders:order_detail', args=[order.id]))
        assert response.status_code == 200
        assert 'order' in response.context

    def test_order_list_view(self):
        """测试订单列表页面"""
        self.client.force_login(self.user)

        # 创建一些订单
        from orders.models import Order
        order1 = Order.objects.create(
            user=self.user,
            first_name='张',
            last_name='三',
            email='zhangsan@example.com',
            address='北京市朝阳区',
            postal_code='100000',
            city='北京'
        )

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
        assert 'orders' in response.context
        orders = response.context['orders']
        assert len(orders) == 2
        assert order1 in orders
        assert order2 in orders