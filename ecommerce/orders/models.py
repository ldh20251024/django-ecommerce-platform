from django.db import models
from django.conf import settings
from shop.models import Product
from django.db.models import Sum, F


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    is_waiting = models.BooleanField(default=False)
    # 新增退款相关字段
    is_refunded = models.BooleanField(default=False)  # 是否已退款
    refund_reason = models.TextField(blank=True, null=True)  # 退款原因
    refund_date = models.DateTimeField(blank=True, null=True)  # 退款时间
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # 退款金额
    payment_method = models.CharField(max_length=20, choices=[
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery'),
    ], blank=True, null=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        """使用数据库聚合计算总价（替代循环）"""
        return self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))  # 数据库层面计算乘积和
        )['total'] or 0  # 处理空购物车的情况

    # def get_total_cost(self):
    #     return sum(item.get_cost() for item in self.items.all())

    # 新增方法：判断是否可以退款
    def can_refund(self):
        # 已支付且未退款的订单可以申请退款
        return self.is_paid and not self.is_refunded


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity