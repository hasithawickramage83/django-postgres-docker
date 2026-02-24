from django.contrib import admin
from .models import Product, ProductImage

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','product_model','product_dimension' , 'price', 'discount_percentage', 'quantity', 'is_active', 'created_at', 'updated_at')
    list_editable = ('discount_percentage', 'quantity', 'is_active','product_model')
    search_fields = ('name','product_model',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image')
