import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory

try:
    # 测试购物车URL
    cart_detail_url = reverse('cart:cart_detail')
    print(f"✓ 购物车详情URL: {cart_detail_url}")

    cart_add_url = reverse('cart:cart_add', args=[1])
    print(f"✓ 添加购物车URL: {cart_add_url}")

    cart_remove_url = reverse('cart:cart_remove', args=[1])
    print(f"✓ 移除购物车URL: {cart_remove_url}")

    # 测试URL解析
    factory = RequestFactory()
    request = factory.get('/cart/')

    print("✓ 所有URL配置正确！")

except Exception as e:
    print(f"✗ URL配置错误: {e}")
    import traceback

    traceback.print_exc()