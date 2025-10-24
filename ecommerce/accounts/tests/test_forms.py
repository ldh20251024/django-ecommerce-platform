import pytest
from django.test import TestCase
from ..forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth import get_user_model
User = get_user_model()

@pytest.mark.django_db
class TestUserRegistrationForm:
    def test_valid_registration_form(self):
        """测试有效的注册表单"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = UserRegistrationForm(data=form_data)
        assert form.is_valid() is True

    def test_invalid_email_registration(self):
        """测试重复邮箱注册"""
        # 先创建一个用户
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123'
        )

        # 尝试用相同邮箱注册新用户
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = UserRegistrationForm(data=form_data)
        # 调试信息：打印表单错误
        if form.is_valid():
            print("表单验证通过了，但应该失败")
            print("表单数据:", form.cleaned_data)
        else:
            print("表单验证失败，错误信息:", form.errors)

        assert form.is_valid() is False
        assert 'email' in form.errors

    def test_password_mismatch(self):
        """测试密码不匹配"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpassword123',
            'password2': 'differentpassword'
        }
        form = UserRegistrationForm(data=form_data)
        assert form.is_valid() is False
        assert 'password2' in form.errors