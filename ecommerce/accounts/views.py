from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from django.urls import reverse
from django.contrib.auth.views import PasswordChangeDoneView


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 保存用户（此时user已在内存中，无需重新查询）
            user = form.save()

            # 直接使用内存中的user实例登录，避免查询数据库
            login(request, user)  # 这里使用已有的user对象，不会触发新查询
            messages.success(request, '注册成功！欢迎来到我们的商店。')
            return redirect('accounts:dashboard')
        else:
            # 如果表单无效，显示错误信息
            messages.error(request, '注册失败，请检查表单错误。')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST', block=True)  # 每IP每分钟最多5次登录尝试
def user_login(request):
    # 获取重定向URL，默认为用户仪表板
    # 确保未登录的用户登录之后不用手动跳转
    # 获取next参数，优先从GET参数获取，然后是POST参数，最后使用默认值
    next_url = request.GET.get('next', '')
    if not next_url:
        next_url = request.POST.get('next', '')
    if not next_url:
        next_url = reverse('accounts:dashboard')  # 默认重定向到用户中心

    # print(f"DEBUG: next_url = {next_url}")  # 调试信息

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')

                # 确保重定向到正确的URL
                return redirect(next_url)
            else:
                messages.info(request, '用户名或密码错误。')
    else:
        form = UserLoginForm()

    # return render(request, 'accounts/login.html', {'form': form})
    return render(request, 'accounts/login.html', {
        'form': form,
        'next_url': next_url
    })


def user_logout(request):
    logout(request)
    messages.info(request, '您已成功退出登录。')
    return redirect('shop:product_list')


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    def dispatch(self, request, *args, **kwargs):
        # 1. 密码修改成功后，强制登出用户（清除会话）
        logout(request)

        # 2. 添加提示消息（告知用户需要重新登录）
        messages.success(request, "密码已成功修改，请使用新密码重新登录。")

        # 3. 跳转到登录页（替换为你的登录页URL名称）
        return redirect('accounts:login')  # 假设登录页的URL名称是 'login'

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html', {'user': request.user})

from django.contrib.auth.decorators import login_required
from .models import Address
from .forms import AddressForm

@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/address_list.html', {'addresses': addresses})

@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.filter(is_default=True).update(is_default=False)
            address.save()
            messages.success(request, '地址添加成功！')
            return redirect('accounts:address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': '添加收货地址'})

@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            if address.is_default:
                request.user.addresses.filter(is_default=True).exclude(pk=pk).update(is_default=False)
            address.save()
            messages.success(request, '地址修改成功！')
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': '编辑收货地址'})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, '地址删除成功！')
    return redirect('accounts:address_list')

@login_required
def set_default_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    request.user.addresses.filter(is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, '默认地址设置成功！')
    return redirect('accounts:address_list')