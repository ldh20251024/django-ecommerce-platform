# payment/models.py
from django.db import models
from orders.models import Order
from django.contrib.auth import get_user_model
User = get_user_model()


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('stripe', '信用卡支付'),
        ('paypal', 'PayPal'),
        ('cod', '货到付款'),
    ]

    PAYMENT_STATUS = [
        ('pending', '待支付'),
        ('completed', '支付成功'),
        ('failed', '支付失败'),
        ('cancelled', '已取消'),
        ('waiting', '待调货'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    amount = models.DecimalField(max_digits=65, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"支付 #{self.id} - {self.get_payment_method_display()} - ¥{self.amount}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = '支付记录'
        verbose_name_plural = '支付记录'