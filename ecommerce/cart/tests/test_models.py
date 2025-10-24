import pytest
from django.test import TestCase
from shop.models import Product, Category
from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestCartModel:
    def test_create_cart(self):
        """测试创建购物车"""
        cart = Cart.objects.create(cart='0')
        assert cart.id == 0
        assert str(cart) == '0'

    def test_create_cart_item(self):
        """测试创建购物车商品项"""
        # 创建测试数据
        category = Category.objects.create(name='电子产品', slug='electronics')
        product = Product.objects.create(
            category=category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )
        cart = Cart.objects.create(id='test-cart-123')

        # 创建购物车项
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )

        assert cart_item.quantity == 2
        assert cart_item.product == product
        assert cart_item.cart == cart
        assert cart_item.get_total_price() == 11998.00  # 5999 * 2

    def test_cart_item_str_representation(self):
        """测试购物车项字符串表示"""
        category = Category.objects.create(name='电子产品', slug='electronics')
        product = Product.objects.create(
            category=category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00
        )
        cart = Cart.objects.create(id='test-cart-123')
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )

        assert str(cart_item) == 'iPhone 13'