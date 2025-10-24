from django.core.management.base import BaseCommand
from shop.models import Product, Category
from django.utils.text import slugify
import random


class Command(BaseCommand):
    help = '填充测试商品数据'

    def handle(self, *args, **options):
        categories = Category.objects.all()

        if not categories:
            self.stdout.write(self.style.ERROR('请先创建分类'))
            return

        products_data = [
            # 添加一些示例商品数据...
        ]

        for i, data in enumerate(products_data):
            product = Product(
                name=data['name'],
                slug=slugify(data['name']),
                description=data['description'],
                price=data['price'],
                stock=random.randint(0, 100),
                category=random.choice(categories),
                available=True
            )
            product.save()

        self.stdout.write(self.style.SUCCESS(f'成功创建 {len(products_data)} 个测试商品'))