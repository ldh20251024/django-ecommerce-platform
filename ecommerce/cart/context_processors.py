from .cart import Cart
from .models import Cart as CartModel


def cart_context(request):
    """购物车上下文处理器 - 处理登录用户的购物车合并"""
    context = {}

    if request.user.is_authenticated:
        try:
            cart_model = CartModel.objects.get(user=request.user)
            context['cart'] = cart_model

            # 检查是否需要合并session购物车（双重保险）
            session_cart = request.session.get('cart', {})
            if session_cart:
                from .utils import merge_carts
                merged_cart = merge_carts(session_cart, request.user)
                if merged_cart:
                    # 清除session购物车
                    if 'cart' in request.session:
                        del request.session['cart']
                        request.session.modified = True
                    context['cart'] = merged_cart

        except CartModel.DoesNotExist:
            # 如果购物车不存在，创建一个
            cart_model = CartModel.objects.create(user=request.user)
            context['cart'] = cart_model
    else:
        # 未登录用户使用session购物车
        session_cart = request.session.get('cart', {})
        context['cart_items_count'] = len(session_cart)
        context['cart'] = None  # 未登录用户没有数据库购物车

    return context

def cart(request):
    return {'cart': Cart(request)}