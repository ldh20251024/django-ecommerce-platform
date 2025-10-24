import pytest
from cart.forms import CartAddProductForm


@pytest.mark.django_db
class TestCartAddProductForm:
    def test_valid_form(self):
        """测试有效表单"""
        form_data = {'quantity': 2, 'update': False}
        form = CartAddProductForm(data=form_data)
        assert form.is_valid() is True

    def test_invalid_quantity_zero(self):
        """测试数量为0的表单"""
        form_data = {'quantity': 0, 'update': False}
        form = CartAddProductForm(data=form_data)
        assert form.is_valid() is False
        assert 'quantity' in form.errors

    def test_invalid_quantity_negative(self):
        """测试负数数量的表单"""
        form_data = {'quantity': -1, 'update': False}
        form = CartAddProductForm(data=form_data)
        assert form.is_valid() is False
        assert 'quantity' in form.errors

    def test_missing_quantity(self):
        """测试缺少数量的表单"""
        form_data = {'update': False}
        form = CartAddProductForm(data=form_data)
        assert form.is_valid() is False
        assert 'quantity' in form.errors

    def test_update_field(self):
        """测试update字段"""
        form_data = {'quantity': 1, 'update': True}
        form = CartAddProductForm(data=form_data)
        assert form.is_valid() is True
        assert form.cleaned_data['update'] is True