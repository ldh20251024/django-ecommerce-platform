import pytest
from django.core.exceptions import ValidationError
from ..models import Category, Product


@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        """测试创建分类"""
        category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        assert category.name == '电子产品'
        assert category.slug == 'electronics'
        assert str(category) == '电子产品'

    def test_category_ordering(self):
        """测试分类排序"""
        Category.objects.create(name='B分类', slug='b-category')
        Category.objects.create(name='A分类', slug='a-category')

        categories = Category.objects.all()
        assert categories[0].name == 'A分类'
        assert categories[1].name == 'B分类'


@pytest.mark.django_db
class TestProductModel:
    def test_create_product(self):
        """测试创建商品"""
        category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        product = Product.objects.create(
            category=category,
            name='iPhone 13',
            slug='iphone-13',
            description='苹果手机',
            price=5999.00,
            stock=100
        )
        assert product.name == 'iPhone 13'
        assert product.price == 5999.00
        assert product.available is True
        assert str(product) == 'iPhone 13'

    def test_product_absolute_url(self):
        """测试商品绝对URL"""
        category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        product = Product.objects.create(
            category=category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00
        )
        url = product.get_absolute_url()
        assert str(product.id) in url
        assert product.slug in url