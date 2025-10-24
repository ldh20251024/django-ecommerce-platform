from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordChangeDoneView  # 导入自定义视图


app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.address_add, name='address_add'),
    path('addresses/edit/<int:pk>/', views.address_edit, name='address_edit'),
    path('addresses/delete/<int:pk>/', views.address_delete, name='address_delete'),
    path('addresses/set-default/<int:pk>/', views.set_default_address, name='set_default_address'),
    # 利用 Django 内置的密码修改视图，只需配置 URL 和模板即可。
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password-change/done/'
    ), name='password_change'),
    # 自定义的密码修改成功视图（处理登出和跳转）
    path('password-change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]