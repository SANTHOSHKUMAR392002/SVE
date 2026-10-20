from django.contrib import admin
from .models import *
admin.site.register(ShopProfile)
admin.site.register(Category)
admin.site.register(Vendor)
admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(PurchaseItem)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(StockTransaction)
admin.site.register(SheetEntry)
