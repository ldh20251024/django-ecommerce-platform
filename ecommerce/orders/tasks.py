# orders/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from .models import Order

@shared_task
def send_refund_confirmation_email(order_id):
    """发送退款确认邮件"""
    order = Order.objects.get(id=order_id)
    subject = f'退款确认 #{order.id}'
    message = (f'尊敬的{order.first_name}，您的退款已处理完成\n\n'
               f'订单号: #{order.id}\n'
               f'退款金额: ¥{order.refund_amount}\n'
               f'退款原因: {order.refund_reason}\n\n'
               '资金将在1-3个工作日内退回您的原支付账户')
    send_mail(subject, message, 'noreply@yourdomain.com', [order.email])

@shared_task
def send_order_confirmation_email(order_id):
    order = Order.objects.get(id=order_id)
    subject = f'订单确认 #{order.id}'
    message = f'尊敬的{order.first_name}，您的订单已确认...'
    send_mail(subject, message, 'noreply@yourdomain.com', [order.email])