from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # 修改这里：检查 session 是否有 modified 属性
        """保存购物车到 session"""
        # 确保购物车数据被保存到 session
        self.session[settings.CART_SESSION_ID] = self.cart

        # 标记 session 为已修改（如果 session 对象支持的话）
        if hasattr(self.session, 'modified'):
            self.session.modified = True
        elif hasattr(self.session, '_modified'):
            # 某些 Django 版本使用 _modified
            self.session._modified = True
        # 对于普通字典，我们不需要设置 modified 属性

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        # clear方法目前只删除了session中的购物车，但是内存中的self.cart仍然指向一个字典。
        # 当我们再次访问购物车时，由于session中已经没有了购物车，所以会重新初始化一个空的购物车，
        # 但是当前实例的self.cart并没有被清空。
        # 为了保持一致性，我们应该同时清空self.cart。
        # 删除session中的购物车
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
        # 清空内存中的购物车
        self.cart = {}
        self.save()
        # 我们之前的设计是利用了字典是可变对象，self.cart和session['cart']是同一个字典，
        # 所以修改self.cart就等于修改了session['cart']。
        # 但是，如果我们给self.cart重新赋值（比如在clear方法中），那么这种联系就断了。
        # 因此，我们需要修改save方法，确保每次保存时都将self.cart赋值给session