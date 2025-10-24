# cart/utils.py
from .models import Cart, CartItem
from shop.models import Product


def merge_carts(session_cart, user):
    """
    将session购物车数据合并到用户数据库购物车中
    """
    if not session_cart:
        return

    try:
        # 获取或创建用户购物车
        user_cart, created = Cart.objects.get_or_create(user=user)

        merged_items = 0

        # 遍历session购物车中的商品
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=product_id)

                # 检查商品是否已在用户购物车中
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    product=product,
                    defaults={'quantity': quantity}
                )

                if not item_created:
                    # 如果已存在，合并数量（取最大值或相加，这里选择相加）
                    cart_item.quantity += quantity
                    cart_item.save()

                merged_items += 1
                print(f"✅ 合并商品: {product.name} x {quantity}")

            except Product.DoesNotExist:
                print(f"❌ 商品 {product_id} 不存在，跳过")
                continue
            except Exception as e:
                print(f"❌ 合并商品 {product_id} 时出错: {e}")
                continue

        print(f"🎉 购物车合并完成，共合并 {merged_items} 个商品")
        return user_cart

    except Exception as e:
        print(f"❌ 购物车合并失败: {e}")
        return None