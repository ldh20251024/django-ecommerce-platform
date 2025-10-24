import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()


@pytest.mark.django_db
class TestUserViews:
    def setup_method(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_register_view_get(self):
        """测试注册页面GET请求"""
        response = self.client.get(reverse('accounts:register'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_register_view_post_success(self):
        """测试成功注册"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })

        # 调试信息
        if response.status_code != 302:
            print("注册失败，状态码:", response.status_code)
            if hasattr(response, 'context') and 'form' in response.context:
                print("表单错误:", response.context['form'].errors)

        # 注册成功后应该重定向
        assert response.status_code == 302
        # 检查用户是否创建
        user_exists = User.objects.filter(username='newuser').exists()
        print(f"用户 'newuser' 是否存在: {user_exists}")
        if not user_exists:
            print("所有用户:", User.objects.all().values_list('username', flat=True))
        assert user_exists is True

    def test_login_view_get(self):
        """测试登录页面GET请求"""
        response = self.client.get(reverse('accounts:login'))
        assert response.status_code == 200

    def test_login_view_post_success(self):
        """测试成功登录"""
        # 先创建用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # 登录成功后应该重定向
        assert response.status_code == 302

    def test_dashboard_requires_login(self):
        """测试仪表板需要登录"""
        response = self.client.get(reverse('accounts:dashboard'))
        # 未登录用户应该被重定向到登录页面
        assert response.status_code == 302
        assert 'login' in response.url