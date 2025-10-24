import pytest
from orders.forms import OrderCreateForm


@pytest.mark.django_db
class TestOrderCreateForm:
    def test_valid_order_form(self):
        """测试有效的订单表单"""
        form_data = {
            'first_name': '张',
            'last_name': '三',
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            'postal_code': '100000',
            'city': '北京'
        }
        form = OrderCreateForm(data=form_data)
        assert form.is_valid() is True

    def test_invalid_email(self):
        """测试无效邮箱"""
        form_data = {
            'first_name': '张',
            'last_name': '三',
            'email': 'invalid-email',
            'address': '北京市朝阳区',
            'postal_code': '100000',
            'city': '北京'
        }
        form = OrderCreateForm(data=form_data)
        assert form.is_valid() is False
        assert 'email' in form.errors

    def test_missing_required_fields(self):
        """测试缺失必填字段"""
        form_data = {
            'first_name': '张',
            # 缺少 last_name
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            # 缺少 postal_code 和 city
        }
        form = OrderCreateForm(data=form_data)
        assert form.is_valid() is False
        assert 'last_name' in form.errors
        assert 'postal_code' in form.errors
        assert 'city' in form.errors

    def test_form_save(self):
        """测试表单保存"""
        form_data = {
            'first_name': '张',
            'last_name': '三',
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            'postal_code': '100000',
            'city': '北京'
        }
        form = OrderCreateForm(data=form_data)
        assert form.is_valid() is True

        # 测试保存（需要用户参数）
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        order = form.save(commit=False)
        order.user = user
        order.save()

        assert order.first_name == '张'
        assert order.last_name == '三'
        assert order.email == 'zhangsan@example.com'