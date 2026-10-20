from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class ShopProfile(models.Model):
    name=models.CharField(max_length=160,default="SRI VINAYAGA ELECTRICALS")
    shop_code=models.CharField(max_length=12,unique=True,default="SVE")
    address=models.TextField(blank=True)
    phone=models.CharField(max_length=30,blank=True)
    def __str__(self): return f"{self.name} ({self.shop_code})"

class Category(models.Model):
    name=models.CharField(max_length=100,unique=True)
    code=models.CharField(max_length=8,unique=True)
    description=models.TextField(blank=True)
    class Meta: ordering=["name"]
    def __str__(self): return self.name

class Vendor(models.Model):
    vendor_code=models.CharField(max_length=20,unique=True,blank=True)
    name=models.CharField(max_length=160)
    phone=models.CharField(max_length=30,blank=True)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    gst_number=models.CharField("GST number",max_length=15,blank=True)
    products=models.ManyToManyField("Product",blank=True,related_name="vendors")
    def save(self,*args,**kwargs):
        if not self.vendor_code:
            self.vendor_code=f"VEN-{(Vendor.objects.count()+1):06d}"
        super().save(*args,**kwargs)
    def __str__(self): return f"{self.vendor_code} - {self.name}"

class Product(models.Model):
    sku=models.CharField(max_length=40,unique=True,blank=True)
    name=models.CharField(max_length=200)
    category=models.ForeignKey(Category,on_delete=models.PROTECT,null=True,blank=True)
    brand=models.CharField(max_length=100,blank=True)
    hsn_code=models.CharField("HSN code",max_length=20,blank=True)
    unit=models.CharField(max_length=20,default="pcs")
    purchase_price=models.DecimalField(max_digits=12,decimal_places=2,default=Decimal("0"),validators=[MinValueValidator(Decimal("0"))])
    selling_price=models.DecimalField(max_digits=12,decimal_places=2,default=Decimal("0"),validators=[MinValueValidator(Decimal("0"))])
    stock_quantity=models.DecimalField(max_digits=12,decimal_places=3,default=Decimal("0"),validators=[MinValueValidator(Decimal("0"))])
    low_stock_level=models.DecimalField(max_digits=12,decimal_places=3,default=Decimal("5"))
    is_active=models.BooleanField(default=True)
    def save(self,*args,**kwargs):
        if not self.sku:
            profile=ShopProfile.objects.first()
            prefix=profile.shop_code if profile else "SVE"
            code=self.category.code if self.category_id else "PRD"
            self.sku=f"{prefix}-{code}-{(Product.objects.count()+1):06d}"
            while Product.objects.filter(sku=self.sku).exists():
                self.sku=f"{prefix}-{code}-{(Product.objects.count()+2):06d}"
        super().save(*args,**kwargs)
    def __str__(self): return f"{self.sku} - {self.name}"

class Purchase(models.Model):
    invoice_number=models.CharField(max_length=40,unique=True,blank=True)
    vendor=models.ForeignKey(Vendor,on_delete=models.PROTECT,related_name="purchases")
    purchase_date=models.DateField(default=timezone.localdate)
    vendor_invoice=models.CharField(max_length=80,blank=True)
    total_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0"))
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if not self.invoice_number: self.invoice_number=f"PUR-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        super().save(*args,**kwargs)
    def __str__(self): return self.invoice_number

class PurchaseItem(models.Model):
    purchase=models.ForeignKey(Purchase,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.DecimalField(max_digits=12,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=12,decimal_places=2)
    line_total=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0"))

class Sale(models.Model):
    invoice_number=models.CharField(max_length=40,unique=True,blank=True)
    sale_date=models.DateField(default=timezone.localdate)
    customer_name=models.CharField(max_length=160,default="Walk-in Customer")
    customer_phone=models.CharField(max_length=30,blank=True)
    discount=models.DecimalField(max_digits=12,decimal_places=2,default=Decimal("0"))
    total_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0"))
    cost_amount=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0"))
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if not self.invoice_number: self.invoice_number=f"SAL-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        super().save(*args,**kwargs)
    @property
    def gross_profit(self): return self.total_amount-self.cost_amount
    def __str__(self): return self.invoice_number

class SaleItem(models.Model):
    sale=models.ForeignKey(Sale,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity=models.DecimalField(max_digits=12,decimal_places=3)
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)
    unit_cost=models.DecimalField(max_digits=12,decimal_places=2)
    line_total=models.DecimalField(max_digits=14,decimal_places=2,default=Decimal("0"))

class StockTransaction(models.Model):
    TYPES=[("OPENING","Opening stock"),("PURCHASE","Purchase received"),("SALE","Sale"),("ADJUSTMENT","Adjustment"),("RETURN","Customer return")]
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name="stock_transactions")
    transaction_type=models.CharField(max_length=12,choices=TYPES)
    quantity_change=models.DecimalField(max_digits=12,decimal_places=3)
    balance_after=models.DecimalField(max_digits=12,decimal_places=3)
    reference=models.CharField(max_length=60,blank=True)
    note=models.CharField(max_length=250,blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]


class SheetEntry(models.Model):
    """Sheet module: one row = stock bought on one date for one product.
    S.No is NOT stored - it is counted per date (1,2,3... for every date) when displayed.
    Sales of a row reduce only that row's stock (balance), never other dates' rows."""
    entry_date=models.DateField(default=timezone.localdate)
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name="sheet_entries")
    vendor=models.ForeignKey(Vendor,on_delete=models.PROTECT,null=True,blank=True,related_name="sheet_entries")
    stock=models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(Decimal("0"))])
    sales=models.DecimalField(max_digits=12,decimal_places=3,null=True,blank=True,validators=[MinValueValidator(Decimal("0"))])
    mrp=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True,validators=[MinValueValidator(Decimal("0"))])
    disc=models.DecimalField("Disc %",max_digits=5,decimal_places=2,null=True,blank=True,validators=[MinValueValidator(Decimal("0")),MaxValueValidator(Decimal("100"))])
    price=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal("0"))])
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="sheet_entries")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=["-entry_date","id"]
        verbose_name_plural="Sheet entries"
    @property
    def balance(self): return self.stock-(self.sales or Decimal("0"))
    @property
    def product_name(self): return self.product.name
    @property
    def hsn_code(self): return self.product.hsn_code
    def __str__(self): return f"{self.entry_date:%d-%m-%Y} - {self.product.name}"
