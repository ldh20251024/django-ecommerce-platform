import os
import django
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from cart.views import cart_detail

try:
    factory = RequestFactory()
    request = factory.get('/cart/')
    request.session = {}

    response = cart_detail(request)
    print(f"✓ 购物车详情视图状态码: {response.status_code}")
    print(f"✓ 视图返回正常")

except Exception as e:
    print(f"✗ 视图错误: {e}")
    import traceback

    traceback.print_exc()