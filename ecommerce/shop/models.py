from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
# shop/models.py（优化Product.image字段）
from django.core.validators import FileExtensionValidator
import pypinyin  # 需要安装：pip install pypinyin
# 导入 Cloudinary 存储后端
from cloudinary_storage.storage import MediaCloudinaryStorage

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)  # 新增 unique=True
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    stock = models.IntegerField(default=0, db_index=True)
    sales = models.IntegerField(default=0, db_index=True)
    name_initial = models.CharField(max_length=10, blank=True, verbose_name="名称首字母", db_index=True)  # 新增字段
    rating = models.DecimalField(
        max_digits=3,  # 如 4.5 占3位（整数1位+小数1位）
        decimal_places=1,  # 保留1位小数
        default=0.0,
        db_index=True
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/%d',
        storage=MediaCloudinaryStorage(),
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),  # 仅允许图片格式
        ],
        help_text="支持JPG、PNG格式，大小不超过10MB"
    )

    def clean(self):
        """验证图片大小"""
        from django.core.exceptions import ValidationError
        if self.image:
            if self.image.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError("图片大小不能超过10MB")

    def save(self, *args, **kwargs):
        """重写保存方法，自动提取首字母"""
        if self.name:
            first_char = self.name.strip()[0]  # 获取名称第一个字符
            # 处理中文字符：转为拼音首字母
            if '\u4e00' <= first_char <= '\u9fff':  # 判断是否为中文字符
                # 提取拼音首字母（如“苹果”→“P”）
                pinyin = pypinyin.lazy_pinyin(first_char)[0]
                self.name_initial = pinyin[0].upper()  # 首字母大写
            else:
                # 非中文字符（英文/数字等）：直接取首字符大写
                self.name_initial = first_char.upper()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        indexes = [
            # 基础单字段索引建议用db_index=True,简洁高效。
            # 对于同一个字段，db_index 和 models.Index只能选择其一使用，否则会造成重复与混乱
            # 并且复合索引必须用models.Index，且复合索引的第一个字段，无需添加单字索引

            # 高频组合索引（新增/调整）
            models.Index(fields=['available', 'sales']),  # 查在售+按销量排序（热门商品）
            models.Index(fields=['available', 'rating']),  # 查在售+按评分排序（好评商品）
            models.Index(fields=['available', 'stock']),  # 保留，查在售且有库存
            models.Index(fields=['category', 'available']),  # 按分类筛选在售商品（核心场景）
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class SearchQuery(models.Model):
    query = models.CharField(max_length=100)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-count', '-last_searched']
        indexes = [
            models.Index(fields=['query']),  # 加速“查询关键词是否存在”
        ]

    def __str__(self):
        return self.query

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['product', 'created']),  # 加速“商品的评论按时间排序”
        ]

    def __str__(self):
        return f'Review by {self.user.username} for {self.product.name}'