from django.contrib import admin
from .models import Wishlist, Product, Category, GroupGift, Pledge

# Register your models here.
admin.site.register(Wishlist)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(GroupGift)
admin.site.register(Pledge)