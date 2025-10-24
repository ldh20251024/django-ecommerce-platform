from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart
from .models import Order, OrderItem
from django.urls import reverse
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from .forms import OrderCreateForm, RefundRequestForm
from .tasks import send_refund_confirmation_email
# 假设payment应用中有处理支付网关退款的工具函数
from payment.utils import process_payment_refund  # 需要根据实际payment应用实现

# 辅助函数：获取订单（不存在返回404）
def _get_order(order_id,user):
    """获取商品实例，不存在则返回404"""
    return get_object_or_404(Order, id=order_id, user=user)

@login_required
def refund_request(request, order_id):
    """显示退款申请表单"""
    order = _get_order(order_id,request.user)

    # 检查订单是否可以退款
    if not order.can_refund():
        messages.error(request, '该订单无法申请退款')
        return redirect('orders:order_detail', order_id=order.id)

    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            # 验证退款金额是否合理
            amount = form.cleaned_data['amount']
            if amount > order.get_total_cost():
                messages.error(request, f'退款金额不能超过订单总金额 ¥{order.get_total_cost()}')
                return render(request, 'orders/refund_request.html', {'order': order, 'form': form})

            return redirect('orders:process_refund', order_id=order.id)
    else:
        # 默认为全额退款
        form = RefundRequestForm(initial={'amount': order.get_total_cost()})

    return render(request, 'orders/refund_request.html', {
        'order': order,
        'form': form
    })


@login_required
@transaction.atomic
def process_refund(request, order_id):
    """处理退款逻辑"""
    order = _get_order(order_id, request.user)

    # 再次检查订单是否可以退款
    if not order.can_refund():
        messages.error(request, '该订单无法申请退款')
        return redirect('orders:order_detail', order_id=order.id)

    form = RefundRequestForm(request.POST)
    if form.is_valid():
        try:
            # 1. 调用支付网关API处理退款
            # 这里需要根据实际的支付方式调用相应的退款接口
            refund_success = process_payment_refund(
                order_id=order.id,
                amount=form.cleaned_data['amount'],
                payment_method=order.payment_method
            )

            if refund_success:
                # 2. 更新订单状态（使用事务确保数据一致性）
                order.is_refunded = True
                order.refund_reason = form.cleaned_data['reason']
                order.refund_amount = form.cleaned_data['amount']
                order.refund_date = timezone.now()
                order.save()

                # 3. 发送退款确认邮件（异步任务）
                send_refund_confirmation_email.delay(order.id)

                messages.success(request, '退款申请已处理，资金将在1-3个工作日内退回原支付账户')
                return redirect('orders:order_detail', order_id=order.id)
            else:
                messages.error(request, '退款处理失败，请稍后重试')
        except Exception as e:
            # 记录错误日志
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Refund processing error: {str(e)}")
            messages.error(request, f'处理退款时发生错误: {str(e)}')
    else:
        messages.error(request, '表单数据无效，请检查后重试')

    return render(request, 'orders/refund_request.html', {
        'order': order,
        'form': form
    })

@login_required
def order_create(request):
    """创建订单 - 使用数据库购物车"""
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        # 未登录用户重定向到登录页面，并携带next参数
        login_url = reverse('accounts:login')
        next_url = reverse('orders:order_create')
        redirect_url = f"{login_url}?next={next_url}"
        return redirect(redirect_url)
    # 获取用户的数据库购物车
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.error(request, '您的购物车是空的，无法创建订单')
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # 创建订单项
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            # 清空购物车
            cart_items.all().delete()

            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderCreateForm()

    return render(request, 'orders/create.html', {
        'cart': cart,
        'cart_items': cart_items,
        'form': form,
        'total_price': cart.get_total_price()
    })


@login_required
def order_detail(request, order_id):
    order = _get_order(order_id, request.user)

    # 如果订单未支付，显示支付按钮
    show_payment_button = not order.is_paid
    return render(request, 'orders/detail.html', {
        'order': order,
        'show_payment_button': show_payment_button
    })

def order_delete(request, order_id):
    order = _get_order(order_id, request.user)

    order_items = order.items.all()
    for item in order_items:
        item.delete()

    order.delete()

    return redirect('orders:order_list')




@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/list.html', {'orders': orders})