# cart/management/commands/migrate_cart_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from django.contrib.sessions.models import Session
import json

User = get_user_model()


class Command(BaseCommand):
    help = '迁移session购物车数据到数据库购物车'

    def handle(self, *args, **options):
        self.stdout.write('开始迁移购物车数据...')

        migrated_count = 0

        # 遍历所有session
        for session in Session.objects.all():
            try:
                session_data = session.get_decoded()

                # 检查session中是否有购物车数据
                if 'cart' in session_data:
                    cart_data = session_data['cart']

                    # 查找session对应的用户
                    if '_auth_user_id' in session_data:
                        user_id = session_data['_auth_user_id']
                        try:
                            user = User.objects.get(id=user_id)

                            # 创建或获取用户的购物车
                            cart, created = Cart.objects.get_or_create(user=user)

                            # 迁移购物车商品
                            for product_id, quantity in cart_data.items():
                                from shop.models import Product
                                try:
                                    product = Product.objects.get(id=product_id)
                                    cart_item, item_created = CartItem.objects.get_or_create(
                                        cart=cart,
                                        product=product,
                                        defaults={'quantity': quantity}
                                    )
                                    if not item_created:
                                        # 如果已存在，更新数量
                                        cart_item.quantity += quantity
                                        cart_item.save()

                                    migrated_count += 1

                                except Product.DoesNotExist:
                                    self.stdout.write(f'商品 {product_id} 不存在，跳过')

                            self.stdout.write(f'用户 {user.username} 的购物车数据迁移完成')

                        except User.DoesNotExist:
                            self.stdout.write(f'用户 {user_id} 不存在，跳过')

            except Exception as e:
                self.stdout.write(f'处理session {session.session_key} 时出错: {e}')

        self.stdout.write(self.style.SUCCESS(f'购物车数据迁移完成，共迁移 {migrated_count} 个商品项'))