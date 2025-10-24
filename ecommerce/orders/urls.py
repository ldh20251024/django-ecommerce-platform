from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('delete/<int:order_id>/', views.order_delete, name='order_delete'),
    path('list/', views.order_list, name='order_list'),
    # 新增退款相关URL
    path('refund/request/<int:order_id>/', views.refund_request, name='refund_request'),
    path('refund/process/<int:order_id>/', views.process_refund, name='process_refund'),
]