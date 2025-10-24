# cart/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Product
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import Sum, F


class Cart(models.Model):
    """购物车模型 - 与用户关联"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='用户'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return f"{self.user.username}的购物车"

    # get_total_price和get_total_quantity方法通过self.items.all()
    # 遍历购物车项，每次调用都会触发数据库查询，且循环中访问item.product还可能触发额外的关联查询
    # 极有可能导致数据库查询冗余，影响性能
    # def get_total_price(self):
    #     """计算购物车总价"""
    #     return sum(item.get_total_price() for item in self.items.all())
    #
    # def get_total_quantity(self):
    #     """计算购物车总数量"""
    #     return sum(item.quantity for item in self.items.all())

    # 优化：将 Cart 模型中的总和计算逻辑改为数据库层面的聚合操作，避免循环遍历和重复查询：
    def get_total_price(self):
        """使用数据库聚合计算总价（替代循环）"""
        return self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))  # 数据库层面计算乘积和
        )['total'] or 0  # 处理空购物车的情况

    def get_total_quantity(self):
        """使用数据库聚合计算总数量"""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    class Meta:
        verbose_name = '购物车'
        verbose_name_plural = '购物车'


class CartItem(models.Model):
    """购物车商品项"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='购物车'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='商品'
    )
    quantity = models.PositiveIntegerField('数量', default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """计算商品项总价"""
        return self.product.price * self.quantity

    class Meta:
        verbose_name = '购物车商品'
        verbose_name_plural = '购物车商品'
        unique_together = ['cart', 'product']  # 防止重复添加同一商品


# 信号处理 - 用户创建时自动创建购物车
@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """在用户创建时自动创建购物车"""
    if created:
        Cart.objects.get_or_create(user=instance)