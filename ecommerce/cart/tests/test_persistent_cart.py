# cart/tests/test_persistent_cart.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from shop.models import Product, Category
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
class TestPersistentCart:
    def setup_method(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product1 = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=10
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='MacBook Pro',
            slug='macbook-pro',
            price=12999.00,
            stock=5
        )

    def test_cart_created_on_user_creation(self):
        """测试用户创建时自动创建购物车"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )

        # 验证购物车已创建
        assert hasattr(new_user, 'cart')
        assert Cart.objects.filter(user=new_user).exists()

    def test_cart_persistence_after_logout(self):
        """测试退出登录后购物车数据保留"""
        # 用户登录并添加商品到购物车
        self.client.force_login(self.user)

        # 添加商品到购物车
        self.client.post(reverse('cart:cart_add', args=[self.product1.id]))
        self.client.post(reverse('cart:cart_add', args=[self.product2.id]))

        # 验证购物车中有商品
        cart = Cart.objects.get(user=self.user)
        assert cart.items.count() == 2

        # 退出登录
        self.client.logout()

        # 重新登录
        self.client.force_login(self.user)

        # 验证购物车数据仍然存在
        cart_after_login = Cart.objects.get(user=self.user)
        assert cart_after_login.items.count() == 2
        assert cart_after_login.get_total_quantity() == 2

    def test_cart_total_calculation(self):
        """测试购物车总价计算"""
        self.client.force_login(self.user)

        # 添加商品
        self.client.post(reverse('cart:cart_add', args=[self.product1.id]))
        self.client.post(reverse('cart:cart_add', args=[self.product2.id]))

        cart = Cart.objects.get(user=self.user)
        expected_total = self.product1.price + self.product2.price
        assert cart.get_total_price() == expected_total

    def test_cart_item_quantity_update(self):
        """测试购物车商品数量更新"""
        self.client.force_login(self.user)

        # 添加商品
        self.client.post(reverse('cart:cart_add', args=[self.product1.id]))

        # 更新数量
        self.client.post(reverse('cart:cart_update', args=[self.product1.id]), {
            'quantity': 3
        })

        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product1)
        assert cart_item.quantity == 3

    def test_cart_clear(self):
        """测试清空购物车"""
        self.client.force_login(self.user)

        # 添加商品
        self.client.post(reverse('cart:cart_add', args=[self.product1.id]))
        self.client.post(reverse('cart:cart_add', args=[self.product2.id]))

        # 清空购物车
        self.client.post(reverse('cart:cart_clear'))

        cart = Cart.objects.get(user=self.user)
        assert cart.items.count() == 0