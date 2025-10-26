from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
User = get_user_model()
from django.db import models


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='确认密码')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    # 重写clean方法，合并唯一性检查（关键优化）
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        # 一次查询同时检查username和email是否存在（替代默认的两次单独查询）
        existing_user = User.objects.filter(
            models.Q(username=username) | models.Q(email=email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                self.add_error('username', '用户名已存在')
            if existing_user.email == email:
                self.add_error('email', '邮箱已被注册')

        # 密码一致性检查
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            self.add_error('password2', '两次密码不一致')

        return cleaned_data

    def save(self, commit=True):
        """保存用户，确保邮箱被设置"""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['receiver', 'phone', 'province', 'city', 'district', 'detail', 'is_default']
        widgets = {
            'receiver': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'receiver': '收货人',
            'phone': '联系电话',
            'province': '省份',
            'city': '城市',
            'district': '区县',
            'detail': '详细地址',
            'is_default': '设为默认地址',
        }