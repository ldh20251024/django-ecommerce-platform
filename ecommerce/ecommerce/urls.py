from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('orders/', include('orders.urls', namespace='orders')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('payment/', include('payment.urls', namespace='payment')),
    # shop的URL模式是空路径，它会匹配所有请求，所以如果cart的URL放在shop之后，那么访问/cart/会被shop的URL模式捕获
    # URL配置的顺序很重要，特别是当有包含空字符串的模式时（如shop的URL配置），它会匹配所有未被前面模式匹配的请求。
    # 因此，我们将非空字符串的URL配置放在shop之前。否则当访问其他url时，可能会404
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # import debug_toolbar
    urlpatterns += [
        # path('__debug__/', include(debug_toolbar.urls)),
        path('silk/', include('silk.urls', namespace='silk')),
    ]

# route为空字符串的url必须放在最后，因为他会匹配所有url。放前面会覆盖其他格式的url
urlpatterns += path('', include('shop.urls', namespace='shop')),