import pytest
from django.test import Client
from django.urls import reverse
from shop.models import Product, Category
from cart.models import Cart


@pytest.mark.django_db
class TestCartViews:
    def setup_method(self):
        self.client = Client()
        # 创建测试数据
        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )

    def test_cart_detail_view(self):
        """测试购物车详情页面"""
        print("测试购物车详情页面...")
        url = reverse('cart:cart_detail')
        print(f"URL: {url}")

        response = self.client.get(url)
        print(f"状态码: {response.status_code}")
        print(f"模板: {getattr(response, 'template_name', 'No template')}")

        assert response.status_code == 200
        assert 'cart' in response.context

    def test_add_to_cart_view(self):
        """测试添加商品到购物车"""
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'update': False}
        )
        # 应该重定向到购物车页面
        assert response.status_code == 302
        assert response.url == reverse('cart:cart_detail')

    def test_add_to_cart_invalid_quantity(self):
        """测试添加无效数量的商品到购物车"""
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 0, 'update': False}
        )
        # 应该重定向到购物车页面
        assert response.status_code == 302

    def test_remove_from_cart_view(self):
        """测试从购物车移除商品"""
        # 先添加商品到购物车
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'update': False}
        )

        # 然后移除
        response = self.client.post(
            reverse('cart:cart_remove', args=[self.product.id])
        )
        assert response.status_code == 302
        assert response.url == reverse('cart:cart_detail')

    def test_remove_nonexistent_product(self):
        """测试移除不存在的商品"""
        response = self.client.post(
            reverse('cart:cart_remove', args=[999])  # 不存在的商品ID
        )
        assert response.status_code == 302