# cart/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart, CartItem
from shop.models import Product
from .forms import CartAddProductForm

# 多个视图（如 cart_add、cart_remove、cart_update）中重复查询 Product、Cart 和 CartItem
# 同一视图中重复使用的对象（如 product、cart）只查询一次。
# 使用 select_related 或 prefetch_related 预加载关联对象，避免 N+1 查询。
# 消除重复查询：
# 抽取_get_user_cart辅助函数，统一处理购物车的获取 / 创建逻辑，避免在 5 个视图中重复编写Cart.objects.get_or_create
# 抽取_get_product辅助函数，统一处理商品查询逻辑，避免在 3 个视图中重复编写get_object_or_404(Product, id=product_id)
# 优化关联查询：
# 在_get_user_cart中使用prefetch_related('items__product')预加载购物车项及关联的商品，避免模板渲染时产生 N+1 查询问题
# 所有涉及购物车的操作都将使用预加载后的购物车对象，提升页面渲染性能
# 逻辑一致性：
# 所有视图统一使用get_or_create获取购物车，避免部分视图使用get_object_or_404导致的 404 错误（用户无购物车时自动创建空购物车）
# 保持原有业务逻辑不变的前提下，使代码结构更清晰，维护成本更低

# 辅助函数：获取或创建用户购物车并预加载关联数据
def _get_user_cart(user):
    """
    获取用户购物车，不存在则创建
    预加载购物车项及关联商品，避免N+1查询
    """
    return Cart.objects.prefetch_related('items__product').get_or_create(user=user)[0]

# 辅助函数：获取或创建用户购物车并预加载关联数据
def _get_user_cart_item(cart, product, cd):
    """
    检查商品是否在购物车中。不存在则创建新的商品记录
    """
    return CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': cd['quantity']}
        )

# 辅助函数：获取或创建用户购物车并预加载关联数据
def _get_user_cart_item_remove(cart, product):
    """
    检查商品是否在购物车中。不存在则创建新的商品记录
    无数量，用于删除
    """
    return CartItem.objects.get(
            cart=cart,
            product=product,
        )

# 辅助函数：获取商品（不存在返回404）
def _get_product(product_id):
    """获取商品实例，不存在则返回404"""
    return get_object_or_404(Product, id=product_id)

@login_required
def cart_detail(request):
    """购物车详情页面"""
    # cart, created = Cart.objects.get_or_create(user=request.user)
    #
    # context = {
    #     'cart': cart,
    # }
    # return render(request, 'cart/detail.html', context)
    """购物车详情页面"""
    cart = _get_user_cart(request.user)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
@login_required
def cart_add(request, product_id):
    """添加商品到购物车"""
    # product = get_object_or_404(Product, id=product_id)
    #
    # # 获取或创建用户的购物车
    # cart, created = Cart.objects.get_or_create(user=request.user)
    product = _get_product(product_id)
    cart = _get_user_cart(request.user)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        # 检查商品是否已在购物车中,不存在则创建新的购物车商品记录
        # cart_item, item_created = CartItem.objects.get_or_create(
        #     cart=cart,
        #     product=product,
        #     defaults={'quantity': cd['quantity']}
        # )
        cart_item, item_created = _get_user_cart_item(cart, product, cd)

        # 如果商品已存在，增加数量
        if not item_created:
            cart_item.quantity += cd['quantity']
            cart_item.save()
            messages.success(request, f'已更新 {product.name} 的数量')
        else:
            messages.success(request, f'已添加 {product.name} 到购物车')

    return redirect('cart:cart_detail')


@require_POST
@login_required
def cart_remove(request, product_id):
    """从购物车移除商品"""
    # product = get_object_or_404(Product, id=product_id)
    # cart = get_object_or_404(Cart, user=request.user)
    product = _get_product(product_id)
    cart = _get_user_cart(request.user)

    try:
        cart_item = _get_user_cart_item_remove(cart, product)
        cart_item.delete()
        messages.success(request, f'已从购物车移除 {product.name}')
    except CartItem.DoesNotExist:
        messages.error(request, '商品不在购物车中')

    return redirect('cart:cart_detail')


@require_POST
@login_required
def cart_update(request, product_id):
    """更新购物车商品数量"""
    # product = get_object_or_404(Product, id=product_id)
    # cart = get_object_or_404(Cart, user=request.user)
    product = _get_product(product_id)
    cart = _get_user_cart(request.user)
    quantity = int(request.POST.get('quantity', 0))

    if quantity < 1:
        messages.error(request, '数量必须大于0')
        return redirect('cart:cart_detail')

    try:
        cart_item = _get_user_cart_item_remove(cart, product)
        if quantity == 0:
            cart_item.delete()
            messages.success(request, f'已从购物车移除 {product.name}')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'已更新 {product.name} 的数量')
    except CartItem.DoesNotExist:
        messages.error(request, '商品不在购物车中')

    return redirect('cart:cart_detail')


@require_POST
@login_required
def cart_clear(request):
    """清空购物车"""
    # cart = get_object_or_404(Cart, user=request.user)
    cart = _get_user_cart(request.user)
    cart.items.all().delete()
    messages.success(request, '购物车已清空')
    return redirect('cart:cart_detail')