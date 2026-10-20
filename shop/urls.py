from django.urls import path
from . import views
urlpatterns=[
 path("",views.dashboard,name="dashboard"),
 path("products/",views.product_list,name="product_list"),
 path("products/download/pdf/",views.product_pdf,name="product_pdf"),
 path("products/add/",views.product_create,name="product_create"),
 path("products/<int:pk>/",views.product_detail,name="product_detail"),
 path("products/<int:pk>/edit/",views.product_edit,name="product_edit"),
 path("vendors/",views.vendor_list,name="vendor_list"),
 path("vendors/<int:pk>/",views.vendor_detail,name="vendor_detail"),
 path("vendors/<int:pk>/edit/",views.vendor_edit,name="vendor_edit"),
 path("sales/",views.sale_list,name="sale_list"),
 path("sales/add/",views.sale_create,name="sale_create"),
 path("sales/<int:pk>/",views.sale_detail,name="sale_detail"),
 path("reports/",views.reports,name="reports"),
 path("reports/pdf/",views.reports_pdf,name="reports_pdf"),
 path("sheet/",views.sheet,name="sheet"),
 path("sheet/<int:pk>/edit/",views.sheet_edit,name="sheet_edit"),
 path("sheet/<int:pk>/delete/",views.sheet_delete,name="sheet_delete"),
 path("sheet/download/pdf/",views.sheet_pdf,name="sheet_pdf"),
 path("sheet/download/word/",views.sheet_word,name="sheet_word"),
]
