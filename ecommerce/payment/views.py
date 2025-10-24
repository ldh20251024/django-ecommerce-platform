# payment/views.py
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from orders.models import Order
from shop.models import Product
from .models import Payment

# 配置Stripe
if hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = settings.STRIPE_SECRET_KEY

# 辅助函数：获取订单（不存在返回404）
def _get_order(order_id,user):
    """获取商品实例，不存在则返回404"""
    return get_object_or_404(Order, id=order_id, user=user)

# 辅助函数：创建待处理的支付记录（不存在返回404）
def _get_payment(order,user,payment_method,payment_status):
    """获取商品实例，不存在则返回404"""
    return Payment.objects.get_or_create(
                order=order,
                user=user,
                payment_method=payment_method,
                payment_status=payment_status,
                amount=order.get_total_cost()
            )

@login_required
def payment_options(request, order_id):
    """支付选项页面"""
    order = _get_order(order_id,request.user)

    if order.is_paid:
        messages.warning(request, '该订单已支付')
        return redirect('orders:order_detail', order_id=order.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        # 对于货到付款，可以添加额外的确认参数（可选）
        if payment_method == 'cod' and not request.POST.get('confirmed'):
            pass
            # 这里可以记录日志或进行其他处理
            # print(f"用户选择了货到付款，但未经过前端确认 - 订单 #{order.id}")
            # 我们仍然处理，因为前端已经有确认对话框

        if payment_method == 'stripe':
            # 创建待处理的Stripe支付记录
            # Payment.objects.get_or_create(
            #     order=order,
            #     user=request.user,
            #     payment_method='stripe',
            #     payment_status='pending',
            #     amount=order.get_total_cost()
            # )
            _get_payment(order,request.user,'stripe','pending')
            return redirect('payment:stripe_checkout', order_id=order.id)

        elif payment_method == 'paypal':
            # 创建待处理的PayPal支付记录
            # Payment.objects.get_or_create(
            #     order=order,
            #     user=request.user,
            #     payment_method='paypal',
            #     payment_status='pending',
            #     amount=order.get_total_cost()
            # )
            _get_payment(order, request.user, 'paypal', 'pending')
            return redirect('payment:paypal_checkout', order_id=order.id)

        elif payment_method == 'cod':
            # 货到付款
            # Payment.objects.get_or_create(
            #     order=order,
            #     user=request.user,
            #     payment_method='cod',
            #     payment_status='completed',
            #     amount=order.get_total_cost()
            # )
            _get_payment(order, request.user, 'cod', 'completed')
            order.is_paid = True
            order.payment_method = 'cod'
            order.save()

            messages.success(request, '订单创建成功！我们将安排发货，请准备现金支付。')
            return redirect('payment:payment_success', order_id=order.id)

    context = {
        'order': order,
    }
    return render(request, 'payment/payment_options.html', context)


@login_required
def stripe_checkout(request, order_id):
    """Stripe支付页面"""
    order = _get_order(order_id, request.user)

    if order.is_paid:
        messages.warning(request, '该订单已支付')
        return redirect('orders:order_detail', order_id=order.id)

    # 获取或创建待支付的Stripe支付记录
    # payment, created = Payment.objects.get_or_create(
    #     order=order,
    #     payment_method='stripe',
    #     payment_status='pending',
    #     defaults={
    #         'user': request.user,
    #         'amount': order.get_total_cost()
    #     }
    # )
    payment = _get_payment(order, request.user,'stripe','pending')

    context = {
        'order': order,
        'payment': payment,
        'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
    }
    return render(request, 'payment/stripe_checkout.html', context)


@login_required
def create_stripe_payment_intent(request, order_id):
    """创建Stripe支付意向 - 增强错误日志"""
    # print(f"=== 创建Stripe支付意向请求 ===")
    # print(f"订单ID: {order_id}")
    # print(f"用户: {request.user}")

    if request.method == 'POST':
        try:
            order = _get_order(order_id, request.user)
            # print(f"找到订单: #{order.id}, 金额: {order.get_total_cost()}")
        except Order.DoesNotExist:
            # print(f"❌ 订单不存在: {order_id}")
            return JsonResponse({
                'error': '订单不存在'
            }, status=400)

        # 检查订单是否已支付
        if order.is_paid:
            # print(f"❌ 订单已支付: #{order.id}")
            return JsonResponse({
                'error': '该订单已支付，无法重复支付'
            }, status=400)

        try:
            # 获取或创建支付记录
            # payment, created = Payment.objects.get_or_create(
            #     order=order,
            #     payment_method='stripe',
            #     payment_status='pending',
            #     defaults={
            #         'user': request.user,
            #         'amount': order.get_total_cost()
            #     }
            # )
            payment, created = _get_payment(order, request.user, 'stripe', 'pending')

            # print(f"支付记录: {'创建' if created else '已存在'} - ID: {payment.id}")

            # 检查Stripe配置
            stripe_secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            if not stripe_secret_key:
                # print("❌ Stripe密钥未配置")
                return JsonResponse({
                    'error': '支付系统配置错误，请联系管理员'
                }, status=500)

            # print(f"Stripe密钥: {stripe_secret_key[:20]}...")

            # 检查金额
            amount = order.get_total_cost()
            amount_in_cents = int(amount * 100)
            # print(f"支付金额: {amount}元 = {amount_in_cents}分")

            if amount <= 0:
                # print("❌ 金额无效")
                return JsonResponse({
                    'error': '订单金额无效'
                }, status=400)

            # 配置Stripe
            stripe.api_key = stripe_secret_key

            # 创建Stripe支付意向
            # print("正在创建Stripe支付意向...")
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency='cny',
                metadata={
                    'order_id': order.id,
                    'user_id': request.user.id,
                    'payment_id': payment.id
                }
            )

            # print(f"✅ Stripe支付意向创建成功: {intent.id}")

            # 更新支付记录的交易ID
            payment.transaction_id = intent.id
            payment.save()

            return JsonResponse({
                'clientSecret': intent.client_secret,
                'paymentIntentId': intent.id
            })


        except Exception as e:
            # 捕获所有异常，包括可能的Stripe异常
            # print(f"❌ 支付意向创建错误: {e}")
            import traceback
            traceback.print_exc()

            # 根据异常类型返回不同的错误消息
            error_message = str(e)
            if 'Invalid API Key' in error_message:
                error_message = '支付系统配置错误，请联系管理员'
            elif 'Amount must be no more than' in error_message:
                error_message = '订单金额超过支付限制，请调整订单金额'
            elif 'Amount must be at least' in error_message:
                error_message = '订单金额过低，无法完成支付'
            else:
                error_message = f'支付服务暂时不可用: {error_message}'

            return JsonResponse({'error': error_message}, status=400)

    # print("❌ 非POST请求")
    return JsonResponse({'error': '方法不允许'}, status=405)


@login_required
def stripe_payment_success(request, order_id):
    """Stripe支付成功处理"""
    order = _get_order(order_id, request.user)

    # 更新订单和支付状态
    payment = Payment.objects.filter(
        order=order,
        payment_method='stripe',
        payment_status='pending'
    ).first()
    if payment:
        payment.payment_status = 'completed'
        payment.save()


    order.is_paid = True
    order.payment_method = 'stripe'
    order.save()

    messages.success(request, '支付成功！感谢您的购买。')
    return redirect('payment:payment_success', order_id=order.id)


@login_required
def paypal_checkout(request, order_id):
    """PayPal支付页面"""
    order = _get_order(order_id, request.user)

    if order.is_paid:
        messages.warning(request, '该订单已支付')
        return redirect('orders:order_detail', order_id=order.id)

    # 获取或创建待支付的PayPal支付记录
    # payment, created = Payment.objects.get_or_create(
    #     order=order,
    #     payment_method='paypal',
    #     payment_status='pending',
    #     defaults={
    #         'user': request.user,
    #         'amount': order.get_total_cost()
    #     }
    # )
    payment, created = _get_payment(order, request.user, 'paypal', 'pending')

    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'payment/paypal_checkout.html', context)


@login_required
def paypal_success(request, order_id):
    """PayPal支付成功处理"""
    order = _get_order(order_id, request.user)

    # 更新订单和支付状态
    payment = Payment.objects.filter(
        order=order,
        payment_method='paypal',
        payment_status='pending'
    ).first()
    if payment:
        payment.payment_status = 'completed'
        payment.transaction_id = f"paypal_{order.id}_{payment.id}"
        payment.save()

    order.is_paid = True
    order.payment_method = 'paypal'
    order.save()

    messages.success(request, 'PayPal支付成功！感谢您的购买。')
    return redirect('payment:payment_success', order_id=order.id)


@login_required
def payment_success(request, order_id):
    """支付成功页面"""
    order = _get_order(order_id, request.user)

    order_items = order.items.all()
    payment = Payment.objects.filter(
        order=order,
        payment_status='completed'
    ).first()
    for item in order_items:
        product = get_object_or_404(Product, id=item.product_id)
        if not product or product.stock < item.quantity:
            if payment:
                payment.payment_status = 'waiting'
                payment.save()
                order.is_waiting = True
                order.save()

        # 更新库存与销量
        product.stock -= item.quantity
        product.sales += item.quantity
        product.save()

    # 发送通知
    # send_payment_success_notification(order, payment)

    return render(request, 'payment/payment_success.html', {'order': order})


@login_required
def payment_cancel(request, order_id):
    """支付取消页面"""
    order = _get_order(order_id, request.user)

    # 更新支付状态为取消
    payment = Payment.objects.filter(
        order=order,
        payment_status='pending'
    ).first()
    if payment:
        payment.payment_status = 'cancelled'
        payment.save()
    messages.info(request, '支付已取消')
    return render(request, 'payment/payment_cancel.html', {'order': order})


# Stripe Webhook处理
@csrf_exempt
def stripe_webhook(request):
    """Stripe Webhook处理"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # 处理支付成功事件
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']

        try:
            payment = Payment.objects.get(transaction_id=payment_intent['id'])
            payment.payment_status = 'completed'
            payment.save()

            order = payment.order
            order.is_paid = True
            order.payment_method = 'stripe'
            order.save()
        except Payment.DoesNotExist:
            pass

    return HttpResponse(status=200)


# payment/views.py - 添加支付状态查询
@login_required
def payment_status(request, order_id):
    """查询支付状态"""
    order = _get_order(order_id, request.user)
    payment = get_object_or_404(Payment, order=order)

    return JsonResponse({
        'order_id': order.id,
        'is_paid': order.is_paid,
        'payment_method': order.payment_method,
        'payment_status': payment.payment_status,
        'amount': str(payment.amount),
        'transaction_id': payment.transaction_id,
        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None
    })


# 添加支付成功后的邮件或消息通知
from django.core.mail import send_mail
# payment/views.py - 添加支付成功通知
def send_payment_success_notification(order, payment):
    """发送支付成功通知"""
    subject = f'支付成功 - 订单 #{order.id}'
    message = f'''
        尊敬的{order.first_name} {order.last_name}，

        您的订单 #{order.id} 已支付成功。
        支付金额：¥{payment.amount}
        支付方式：{payment.get_payment_method_display()}

        感谢您的购买！
        '''
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # 使用配置的默认发件人
            [order.email],
            fail_silently=False,  # 设置为 True 可以在出错时不抛出异常
        )
        messages.success(f"支付成功邮件已发送至 {order.email}")
    except Exception as e:
        messages.error(f"发送支付成功邮件失败: {str(e)}")
        # 可以选择记录到数据库或其他处理方式
        # 但不要让邮件发送失败影响主要业务流程