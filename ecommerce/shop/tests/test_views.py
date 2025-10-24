import pytest
from django.test import Client
from django.urls import reverse
from ..models import Category, Product
from django.core.paginator import Page
from shop.models import Review
from django.contrib.auth import get_user_model
User = get_user_model()


@pytest.mark.django_db
class TestProductReviews:
    def setup_method(self):
        self.client = Client()
        # 创建用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 创建分类和产品
        self.category = Category.objects.create(
            name='测试分类',
            slug='test-category'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='测试产品',
            slug='test-product',
            price=99.99,
            stock=10,
            available=True
        )

    def test_review_form_display(self):
        """测试评论表单是否正确显示"""
        response = self.client.get(
            reverse('shop:product_detail', args=[self.product.id, self.product.slug])
        )
        assert response.status_code == 200
        assert 'review_form' in response.context

    def test_add_review_authenticated(self):
        """测试登录用户可以提交评论"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('shop:product_detail', args=[self.product.id, self.product.slug]),
            {
                'rating': 5,
                'comment': '这是一个测试评论'
            }
        )
        # 检查是否重定向（评论提交成功后应该重定向）
        assert response.status_code == 302

        # 检查评论是否被创建
        assert Review.objects.filter(
            product=self.product,
            user=self.user,
            rating=5
        ).exists()

        # 检查产品评分是否被更新
        self.product.refresh_from_db()
        assert self.product.rating == 5.0

    def test_add_review_unauthenticated(self):
        """测试未登录用户不能提交评论"""
        response = self.client.post(
            reverse('shop:product_detail', args=[self.product.id, self.product.slug]),
            {
                'rating': 5,
                'comment': '这是一个测试评论'
            }
        )
        # 未登录用户应该被重定向到登录页
        assert response.status_code == 302
        assert 'login' in response.url

        # 评论不应该被创建
        assert not Review.objects.filter(product=self.product).exists()

    def test_duplicate_review(self):
        """测试用户不能重复评论同一产品"""
        self.client.login(username='testuser', password='testpass123')

        # 第一次提交评论
        self.client.post(
            reverse('shop:product_detail', args=[self.product.id, self.product.slug]),
            {
                'rating': 5,
                'comment': '这是第一个测试评论'
            }
        )

        # 第二次提交评论（应该失败）
        response = self.client.post(
            reverse('shop:product_detail', args=[self.product.id, self.product.slug]),
            {
                'rating': 4,
                'comment': '这是第二个测试评论'
            }
        )

        # 检查是否重定向
        assert response.status_code == 302

        # 检查评论数量仍然是1
        assert Review.objects.filter(product=self.product).count() == 1

@pytest.mark.django_db
class TestShopViews:
    def setup_method(self):
        self.client = Client()
        # 创建测试数据
        self.category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 13',
            slug='iphone-13',
            price=5999.00,
            stock=100
        )

    def test_product_list_view(self):
        """测试商品列表视图"""
        response = self.client.get(reverse('shop:product_list'))
        assert response.status_code == 200
        assert 'products' in response.context
        assert 'categories' in response.context

    def test_product_list_by_category(self):
        """测试按分类查看商品"""
        response = self.client.get(
            reverse('shop:product_list_by_category',
                    args=[self.category.slug])
        )
        assert response.status_code == 200
        assert response.context['category'] == self.category

    def test_product_detail_view(self):
        """测试商品详情视图"""
        response = self.client.get(
            reverse('shop:product_detail',
                    args=[self.product.id, self.product.slug])
        )
        assert response.status_code == 200
        assert response.context['product'] == self.product

    def test_product_detail_not_found(self):
        """测试不存在的商品详情"""
        response = self.client.get(
            reverse('shop:product_detail',
                    args=[999, 'nonexistent'])
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestProductSearchView:
    """测试商品搜索视图"""

    def setup_method(self):
        """测试设置"""
        # 创建测试分类
        self.electronics = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        self.books = Category.objects.create(
            name='图书',
            slug='books'
        )

        # 创建测试商品
        self.iphone = Product.objects.create(
            category=self.electronics,
            name='iPhone 13',
            slug='iphone-13',
            description='苹果智能手机',
            price=5999.00,
            stock=50,
            available=True
        )
        self.macbook = Product.objects.create(
            category=self.electronics,
            name='MacBook Pro',
            slug='macbook-pro',
            description='苹果笔记本电脑',
            price=12999.00,
            stock=30,
            available=True
        )
        self.novel = Product.objects.create(
            category=self.books,
            name='Python编程入门',
            slug='python-programming',
            description='Python编程学习书籍',
            price=59.00,
            stock=100,
            available=True
        )
        self.out_of_stock = Product.objects.create(
            category=self.electronics,
            name='旧款手机',
            slug='old-phone',
            description='已停产的旧款手机',
            price=499.00,
            stock=0,
            available=True
        )

    def test_search_view_url(self, client):
        """测试搜索视图URL"""
        url = reverse('shop:product_search')
        response = client.get(url)

        assert response.status_code == 200
        assert 'search_form' in response.context
        assert 'filter_form' in response.context

    def test_search_by_name(self, client):
        """测试按商品名称搜索"""
        url = reverse('shop:product_search')
        response = client.get(url, {'q': 'iPhone'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert len(page_obj) == 1
        assert page_obj[0].name == 'iPhone 13'

    def test_search_by_description(self, client):
        """测试按商品描述搜索"""
        url = reverse('shop:product_search')
        response = client.get(url, {'q': '笔记本'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert len(page_obj) == 1
        assert page_obj[0].name == 'MacBook Pro'

    def test_search_no_results(self, client):
        """测试无结果的搜索"""
        url = reverse('shop:product_search')
        response = client.get(url, {'q': '不存在的商品'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert len(page_obj) == 0
        assert response.context['total_products'] == 0

    def test_filter_by_category(self, client):
        """测试按分类筛选"""
        url = reverse('shop:product_search')
        response = client.get(url, {'category': self.books.id})

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert len(page_obj) == 1
        assert page_obj[0].name == 'Python编程入门'

    def test_filter_by_price_range(self, client):
        """测试按价格范围筛选"""
        url = reverse('shop:product_search')

        # 测试低价范围
        response = client.get(url, {'price_range': '0-100'})
        page_obj = response.context['page_obj']

        assert len(page_obj) == 1
        assert page_obj[0].name == 'Python编程入门'

        # 测试中等价格范围 (100-500)
        response = client.get(url, {'price_range': '100-500'})
        page_obj = response.context['page_obj']
        assert len(page_obj) == 1
        assert page_obj[0].name == '旧款手机'

        # 测试高价范围 (5000-)
        response = client.get(url, {'price_range': '5000-'})
        page_obj = response.context['page_obj']
        # 应该有两个高价商品：iPhone 13 和 MacBook Pro
        assert len(page_obj) == 2
        product_names = [product.name for product in page_obj]
        assert 'iPhone 13' in product_names
        assert 'MacBook Pro' in product_names

    def test_filter_by_custom_price(self, client):
        """测试自定义价格范围筛选"""
        url = reverse('shop:product_search')
        response = client.get(url, {
            'min_price': '1000',
            'max_price': '10000'
        })

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert len(page_obj) == 1
        assert page_obj[0].name == 'iPhone 13'

    def test_filter_in_stock_only(self, client):
        """测试仅显示有货商品"""
        url = reverse('shop:product_search')
        response = client.get(url, {'in_stock': 'on'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']

        # 应该只返回有库存的商品
        product_names = [product.name for product in page_obj]
        assert '旧款手机' not in product_names
        assert len(page_obj) == 3  # iPhone, MacBook, Python书

    def test_sort_by_price_ascending(self, client):
        """测试按价格升序排序"""
        url = reverse('shop:product_search')
        response = client.get(url, {'sort_by': 'price'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']

        # 价格应该从低到高
        prices = [product.price for product in page_obj]
        assert prices == sorted(prices)

    def test_sort_by_price_descending(self, client):
        """测试按价格降序排序"""
        url = reverse('shop:product_search')
        response = client.get(url, {'sort_by': '-price'})

        assert response.status_code == 200
        page_obj = response.context['page_obj']

        # 价格应该从高到低
        prices = [product.price for product in page_obj]
        assert prices == sorted(prices, reverse=True)

    def test_combined_search_and_filter(self, client):
        """测试搜索和筛选的组合"""
        url = reverse('shop:product_search')
        response = client.get(url, {
            'q': '苹果',
            'category': self.electronics.id,
            'in_stock': 'on'
        })

        assert response.status_code == 200
        page_obj = response.context['page_obj']

        # 应该返回包含"苹果"的电子产品且有库存的商品
        product_names = [product.name for product in page_obj]
        assert 'iPhone 13' in product_names
        assert 'MacBook Pro' in product_names
        assert len(page_obj) == 2

    def test_pagination(self, client):
        """测试分页功能"""
        # 创建更多商品以测试分页
        for i in range(15):
            Product.objects.create(
                category=self.electronics,
                name=f'测试商品 {i}',
                slug=f'test-product-{i}',
                description='测试商品描述',
                price=100.00 + i,
                stock=10,
                available=True
            )

        url = reverse('shop:product_search')
        response = client.get(url, {'page': 2})

        assert response.status_code == 200
        page_obj = response.context['page_obj']
        assert isinstance(page_obj, Page)
        assert page_obj.number == 2


@pytest.mark.django_db
class TestProductListView:
    """测试商品列表视图"""

    def setup_method(self):
        """测试设置"""
        self.category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='测试商品',
            slug='test-product',
            description='测试商品描述',
            price=100.00,
            stock=10,
            available=True
        )