from django.contrib import admin
from .models import Wishlist, Product, Category

# Register your models here.
admin.site.register(Wishlist)
admin.site.register(Product)
admin.site.register(Category)