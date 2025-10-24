import time
import requests
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()


def test_performance():
    base_url = 'http://127.0.0.1:8000'
    endpoints = [
        '/',
        '/cart/',
        '/account/login/',
    ]

    print("=== 性能测试 ===")

    for endpoint in endpoints:
        start_time = time.time()
        try:
            # 使用 requests 测试（需要先启动服务器）
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            load_time = time.time() - start_time

            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {endpoint}: {load_time:.2f}秒 (状态码: {response.status_code})")

        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {e}")

    print("================")


if __name__ == "__main__":
    test_performance()