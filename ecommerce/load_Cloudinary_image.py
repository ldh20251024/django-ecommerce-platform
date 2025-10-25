# 在Django shell中执行
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()
from shop.models import Product
from cloudinary_storage.storage import MediaCloudinaryStorage

# 为所有旧图绑定存储后端
for product in Product.objects.all():
    if product.image:
        product.image.storage = MediaCloudinaryStorage()  # 强制关联Cloudinary存储
        product.save()  # 触发URL重新生成