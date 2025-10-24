# payment/admin.py - 优化支付记录管理
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'user', 'payment_method', 'payment_status', 'amount', 'created_at']
    list_filter = ['payment_method', 'payment_status', 'created_at']
    search_fields = ['order__id', 'user__username', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def order_id(self, obj):
        return obj.order.id

    order_id.short_description = '订单号'