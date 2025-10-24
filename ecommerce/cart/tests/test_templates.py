import pytest
from django.test import Client
from django.urls import reverse
from shop.models import Product, Category


@pytest.mark.django_db
class TestCartTemplates:
    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='电子产品', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )

    def test_cart_detail_template(self):
        """测试购物车详情模板"""
        # 添加商品到购物车
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'update': False}
        )

        response = self.client.get(reverse('cart:cart_detail'))
        assert response.status_code == 200
        # 检查模板是否包含购物车信息
        assert 'cart' in response.context
        assert 'iPhone 13' in response.content.decode()
        assert '11998.00' in response.content.decode()  # 5999 * 2

    def test_empty_cart_template(self):
        """测试空购物车模板"""
        response = self.client.get(reverse('cart:cart_detail'))
        assert response.status_code == 200
        # 应该显示购物车为空的提示
        content = response.content.decode()
        assert '您的购物车是空的' in content.lower() or '暂无' in content

    def test_cart_context_processor(self):
        """测试购物车上下文处理器"""
        # 添加商品到购物车
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'update': False}
        )

        response = self.client.get(reverse('shop:product_list'))
        # 检查上下文处理器是否工作
        assert 'cart' in response.context