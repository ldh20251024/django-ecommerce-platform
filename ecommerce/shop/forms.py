# shop/forms.py
from django import forms
from .models import Category
import bleach
from .models import Review


class ProductSearchForm(forms.Form):
    """商品搜索表单"""
    q = forms.CharField(
        required=False,
        label='搜索',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': '搜索商品...',
            'class': 'form-control',
            'id': 'search-input'
        })
    )


# 允许的安全HTML标签（评论中仅保留基础格式）
ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p']
ALLOWED_ATTRIBUTES = {}  # 不允许任何属性（如onclick）


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_comment(self):
        """清洗评论内容，过滤XSS脚本"""
        comment = self.cleaned_data.get('comment', '')
        return bleach.clean(
            comment,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True  # 移除不允许的标签
        )

class ProductFilterForm(forms.Form):
    """商品筛选表单"""
    # 排序选项
    SORT_CHOICES = [
        ('-created', '最新上架'),
        ('price', '价格从低到高'),
        ('-price', '价格从高到低'),
        ('name_initial', '名称 A-Z'),
        ('-sales', '销量最高'),
        ('-rating', '评分最高'),
    ]

    # 评分筛选
    RATING_CHOICES = [
        ('', '所有评分'),
        ('4', '4星及以上'),
        ('3', '3星及以上'),
        ('2', '2星及以上'),
    ]

    # 价格区间
    PRICE_RANGES = [
        ('', '所有价格'),
        ('0-100', '¥0 - ¥100'),
        ('100-500', '¥100 - ¥500'),
        ('500-1000', '¥500 - ¥1000'),
        ('1000-5000', '¥1000 - ¥5000'),
        ('5000-', '¥5000以上'),
    ]

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='所有分类',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    price_range = forms.ChoiceField(
        choices=PRICE_RANGES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': '最低价',
            'class': 'form-control',
            'step': '0.01'
        })
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': '最高价',
            'class': 'form-control',
            'step': '0.01'
        })
    )

    in_stock = forms.BooleanField(
        required=False,
        initial=False,
        label='仅显示有货',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )