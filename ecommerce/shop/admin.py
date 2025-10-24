from django.contrib import admin
from .models import Category, Product, Review
from django.core.exceptions import ValidationError

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available', 'created', 'updated')
    list_filter = ('available', 'created', 'updated', 'category')
    list_editable = ('price', 'available')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    raw_id_fields = ('category',)
    date_hierarchy = 'created'

    def save_model(self, request, obj, form, change):
        # 保存前验证图片
        try:
            obj.clean()  # 调用模型的clean方法
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, str(e), level='error')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created')
    list_filter = ('rating', 'created')
    search_fields = ('product__name', 'user__username', 'comment')