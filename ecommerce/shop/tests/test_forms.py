import pytest
from ..forms import ProductSearchForm, ProductFilterForm
from ..models import Category


@pytest.mark.django_db
class TestProductSearchForm:
    """测试商品搜索表单"""

    def test_search_form_valid_data(self):
        """测试搜索表单有效数据"""
        form_data = {'q': '手机'}
        form = ProductSearchForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['q'] == '手机'

    def test_search_form_empty_data(self):
        """测试搜索表单空数据"""
        form_data = {}
        form = ProductSearchForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['q'] is ""

    def test_search_form_long_query(self):
        """测试搜索表单长查询"""
        long_query = 'a' * 101  # 超过max_length=100
        form_data = {'q': long_query}
        form = ProductSearchForm(data=form_data)

        assert not form.is_valid()
        assert 'q' in form.errors

    def test_search_form_widget_attrs(self):
        """测试搜索表单小部件属性"""
        form = ProductSearchForm()
        q_field = form.fields['q']

        assert q_field.widget.attrs['placeholder'] == '搜索商品...'
        assert q_field.widget.attrs['class'] == 'form-control'
        assert q_field.widget.attrs['id'] == 'search-input'


@pytest.mark.django_db
class TestProductFilterForm:
    """测试商品筛选表单"""

    def setup_method(self):
        """测试设置"""
        self.category = Category.objects.create(
            name='电子产品',
            slug='electronics'
        )

    def test_filter_form_valid_data(self):
        """测试筛选表单有效数据"""
        form_data = {
            'category': self.category.id,
            'price_range': '0-100',
            'min_price': '50',
            'max_price': '80',
            'in_stock': True,
            'sort_by': 'price'
        }
        form = ProductFilterForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['category'] == self.category
        assert form.cleaned_data['price_range'] == '0-100'
        assert form.cleaned_data['min_price'] == 50
        assert form.cleaned_data['max_price'] == 80
        assert form.cleaned_data['in_stock'] is True
        assert form.cleaned_data['sort_by'] == 'price'

    def test_filter_form_empty_data(self):
        """测试筛选表单空数据"""
        form_data = {}
        form = ProductFilterForm(data=form_data)

        assert form.is_valid()
        # 检查默认值
        assert form.cleaned_data['category'] is None
        assert form.cleaned_data['price_range'] is ""
        assert form.cleaned_data['min_price'] is None
        assert form.cleaned_data['max_price'] is None
        assert form.cleaned_data['in_stock'] is False
        assert form.cleaned_data['sort_by'] == ''

    def test_filter_form_invalid_price(self):
        """测试筛选表单无效价格"""
        form_data = {
            'min_price': '-10',  # 负价格
            'max_price': 'invalid'  # 无效数字
        }
        form = ProductFilterForm(data=form_data)

        assert not form.is_valid()
        assert 'min_price' in form.errors
        assert 'max_price' in form.errors

    def test_filter_form_price_range_choices(self):
        """测试筛选表单价格范围选项"""
        form = ProductFilterForm()
        price_range_field = form.fields['price_range']

        expected_choices = [
            ('', '所有价格'),
            ('0-100', '¥0 - ¥100'),
            ('100-500', '¥100 - ¥500'),
            ('500-1000', '¥500 - ¥1000'),
            ('1000-5000', '¥1000 - ¥5000'),
            ('5000-', '¥5000以上'),
        ]

        assert list(price_range_field.choices) == expected_choices

    def test_filter_form_sort_choices(self):
        """测试筛选表单排序选项"""
        form = ProductFilterForm()
        sort_field = form.fields['sort_by']

        expected_choices = [
            ('-created', '最新上架'),
            ('price', '价格从低到高'),
            ('-price', '价格从高到低'),
            ('name', '名称 A-Z'),
            ('-sales', '销量最高'),
            ('rating', '评分最高'),
        ]

        assert list(sort_field.choices) == expected_choices

    def test_filter_form_widget_classes(self):
        """测试筛选表单小部件类"""
        form = ProductFilterForm()

        # 检查表单字段是否使用了正确的CSS类
        assert form.fields['category'].widget.attrs['class'] == 'form-select'
        assert form.fields['price_range'].widget.attrs['class'] == 'form-select'
        assert form.fields['sort_by'].widget.attrs['class'] == 'form-select'
        assert form.fields['min_price'].widget.attrs['class'] == 'form-control'
        assert form.fields['max_price'].widget.attrs['class'] == 'form-control'
        assert form.fields['in_stock'].widget.attrs['class'] == 'form-check-input'

    def test_filter_form_category_queryset(self):
        """测试筛选表单分类查询集"""
        form = ProductFilterForm()
        category_field = form.fields['category']

        # 应该包含所有分类
        assert self.category in category_field.queryset
        assert category_field.required is False
        assert category_field.empty_label == '所有分类'