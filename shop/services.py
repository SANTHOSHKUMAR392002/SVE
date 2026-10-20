import json
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Product, Purchase, PurchaseItem, Sale, SaleItem, StockTransaction

def decode_lines(raw, price_key):
    try: rows=json.loads(raw)
    except Exception: raise ValidationError("Please add at least one valid product row.")
    if not rows: raise ValidationError("Please add at least one product.")
    lines=[]
    for row in rows:
        try:
            product=Product.objects.get(pk=int(row["product_id"]),is_active=True)
            qty=Decimal(str(row["quantity"])); price=Decimal(str(row[price_key]))
        except Exception: raise ValidationError("A product row has invalid details.")
        if qty<=0 or price<0: raise ValidationError("Quantity must be positive and price cannot be negative.")
        lines.append((product,qty,price))
    return lines

@transaction.atomic
def create_purchase(*,vendor,purchase_date,vendor_invoice,user,raw_lines):
    lines=decode_lines(raw_lines,"unit_cost")
    purchase=Purchase.objects.create(vendor=vendor,purchase_date=purchase_date,vendor_invoice=vendor_invoice,created_by=user)
    total=Decimal("0")
    for original,qty,cost in lines:
        p=Product.objects.select_for_update().get(pk=original.pk)
        PurchaseItem.objects.create(purchase=purchase,product=p,quantity=qty,unit_cost=cost,line_total=qty*cost)
        p.stock_quantity+=qty; p.purchase_price=cost; p.save(update_fields=["stock_quantity","purchase_price"])
        vendor.products.add(p)
        StockTransaction.objects.create(product=p,transaction_type="PURCHASE",quantity_change=qty,balance_after=p.stock_quantity,reference=purchase.invoice_number,note=f"Received from {vendor.name}",created_by=user)
        total+=qty*cost
    purchase.total_amount=total; purchase.save(update_fields=["total_amount"])
    return purchase

@transaction.atomic
def create_sale(*,sale_date,customer_name,customer_phone,discount,user,raw_lines):
    lines=decode_lines(raw_lines,"unit_price")
    sale=Sale.objects.create(sale_date=sale_date,customer_name=customer_name or "Walk-in Customer",customer_phone=customer_phone,discount=discount or Decimal("0"),created_by=user)
    subtotal=Decimal("0"); cost_total=Decimal("0")
    for product,qty,price in lines:
        last=product.sheet_entries.exclude(price__isnull=True).order_by("-entry_date","-id").first()
        cost=last.price if last else Decimal("0")
        SaleItem.objects.create(sale=sale,product=product,quantity=qty,unit_price=price,unit_cost=cost,line_total=qty*price)
        subtotal+=qty*price; cost_total+=qty*cost
    if sale.discount>subtotal: raise ValidationError("Discount cannot exceed subtotal.")
    sale.total_amount=subtotal-sale.discount; sale.cost_amount=cost_total; sale.save(update_fields=["total_amount","cost_amount"])
    return sale
