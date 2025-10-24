# cart/signals.py
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from .models import Cart
from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from .utils import merge_carts

User = get_user_model()

@receiver(user_logged_in)
def merge_session_cart_on_login(sender, request, user, **kwargs):
    """用户登录时合并session购物车到数据库购物车"""
    # print(f"🔄 用户 {user.username} 登录，开始合并购物车...")

    # 检查session中是否有购物车数据
    session_cart = request.session.get('cart', {})

    if session_cart:
        # print(f"发现session购物车，包含 {len(session_cart)} 个商品")
        merged_cart = merge_carts(session_cart, user)

        if merged_cart:
            # 合并成功后清除session购物车
            if 'cart' in request.session:
                del request.session['cart']
                # print("✅ 已清除session购物车")

            # 保存session修改
            request.session.modified = True

            # print(f"✅ 购物车合并成功，用户购物车现有 {merged_cart.items.count()} 个商品")
        else:
            pass
            # print("❌ 购物车合并失败")
    else:
        pass
        # print("ℹ️  session中无购物车数据，无需合并")


@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """在用户创建时自动创建购物车"""
    if created:
        Cart.objects.get_or_create(user=instance)
        # print(f"✅ 为用户 {instance.username} 创建购物车")


@receiver(post_save, sender=User)
def save_user_cart(sender, instance, **kwargs):
    """保存用户购物车"""
    if hasattr(instance, 'cart'):
        instance.cart.save()