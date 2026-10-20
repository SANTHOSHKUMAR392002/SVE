from decimal import Decimal
from datetime import timedelta, datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Count, Q, Max
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .models import Product, Vendor, Sale, StockTransaction, SheetEntry, ShopProfile
from .forms import ProductForm, VendorForm, SaleForm, SheetEntryForm
from . import sheet_export, sheet_utils, pdf_reports
from django.utils.http import url_has_allowed_host_and_scheme
import json
from .services import create_sale

def _shop_name():
    profile=ShopProfile.objects.first()
    return profile.name if profile and profile.name.strip() and profile.name!="My Shop" else "SRI VINAYAGA ELECTRICALS"

@login_required
def dashboard(request):
    today=timezone.localdate()
    try: days=int(request.GET.get("days","15"))
    except ValueError: days=15
    if days not in (7,15,30,90): days=15
    rows=sheet_utils.daily_totals(today-timedelta(days=days-1),today,fill=True)
    t_today=sheet_utils.totals([r for r in rows if r["date"]==today])
    allt=SheetEntry.objects.aggregate(st=Sum("stock"),sa=Sum("sales"))
    overall=(allt["st"] or Decimal("0"))-(allt["sa"] or Decimal("0"))
    return render(request,"shop/dashboard.html",{"days":days,"day_options":(7,15,30,90),"chart":sheet_utils.chart_payload(rows),"range_totals":sheet_utils.totals(rows),
        "today_stock":t_today["stock"],"today_sales":t_today["sales"],"overall_balance":overall,
        "product_count":Product.objects.filter(is_active=True).count(),"vendor_count":Vendor.objects.count(),
        "has_data":any(r["entries"] for r in rows),
        "recent":SheetEntry.objects.select_related("product","vendor").order_by("-entry_date","-id")[:8]})

def _products_qs(request):
    q=request.GET.get("q","").strip()
    qs=Product.objects.filter(is_active=True)
    if q: qs=qs.filter(Q(name__icontains=q)|Q(hsn_code__icontains=q))
    products=list(qs.annotate(total_stock=Sum("sheet_entries__stock"),total_sales=Sum("sheet_entries__sales"),entry_count=Count("sheet_entries")).order_by("name"))
    for p in products: p.balance=(p.total_stock or Decimal("0"))-(p.total_sales or Decimal("0"))
    return products,q

@login_required
def product_list(request):
    products,q=_products_qs(request)
    return render(request,"shop/product_list.html",{"products":products,"q":q})

@login_required
def product_pdf(request):
    products,q=_products_qs(request)
    resp=HttpResponse(pdf_reports.products_pdf(products,_shop_name(),q),content_type="application/pdf")
    resp["Content-Disposition"]=f'attachment; filename="products_{timezone.localdate():%Y%m%d}.pdf"'
    return resp

@login_required
def product_create(request):
    vid=request.GET.get("vendor","")
    vendor=Vendor.objects.filter(pk=vid).first() if vid.isdigit() else None
    form=ProductForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        p=form.save()
        if vendor:
            vendor.products.add(p)
            messages.success(request,f"{p.name} added to {vendor.name}.")
            return redirect("vendor_detail",pk=vendor.pk)
        messages.success(request,f"{p.name} added to Products.")
        return redirect("product_list")
    ctx={"form":form,"title":"Add Product","subtitle":"Only the product name and HSN code are needed."}
    if vendor: ctx.update(title=f"Add product for {vendor.name}",subtitle="It will be added to this vendor's product list.",cancel_url=reverse("vendor_detail",args=[vendor.pk]))
    return render(request,"shop/form.html",ctx)

@login_required
def product_edit(request,pk):
    product=get_object_or_404(Product,pk=pk)
    form=ProductForm(request.POST or None,instance=product)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Product updated (history shows the new name / HSN too).")
        return redirect("product_detail",pk=product.pk)
    return render(request,"shop/form.html",{"form":form,"title":"Edit product","subtitle":product.name,"cancel_url":reverse("product_detail",args=[product.pk])})

@login_required
def product_detail(request,pk):
    product=get_object_or_404(Product,pk=pk)
    entries=list(product.sheet_entries.select_related("vendor").order_by("-entry_date","id"))
    tot=product.sheet_entries.aggregate(st=Sum("stock"),sa=Sum("sales"))
    stock=tot["st"] or Decimal("0"); sales=tot["sa"] or Decimal("0")
    return render(request,"shop/product_detail.html",{"product":product,"entries":entries,"total_stock":stock,"total_sales":sales,"total_balance":stock-sales})

@login_required
def vendor_list(request):
    q=request.GET.get("q","").strip()
    form=VendorForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        v=form.save(); messages.success(request,f"Vendor {v.name} saved."); return redirect("vendor_detail",pk=v.pk)
    qs=Vendor.objects.all()
    if q: qs=qs.filter(Q(name__icontains=q)|Q(phone__icontains=q)|Q(vendor_code__icontains=q)|Q(gst_number__icontains=q))
    vendors=qs.annotate(entry_count=Count("sheet_entries"),total_stock=Sum("sheet_entries__stock"),last_date=Max("sheet_entries__entry_date")).order_by("name")
    return render(request,"shop/vendor_list.html",{"form":form,"vendors":vendors,"q":q})

@login_required
def vendor_edit(request,pk):
    vendor=get_object_or_404(Vendor,pk=pk)
    form=VendorForm(request.POST or None,instance=vendor)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Vendor details updated."); return redirect("vendor_detail",pk=vendor.pk)
    return render(request,"shop/form.html",{"form":form,"title":"Edit vendor","subtitle":vendor.vendor_code,"cancel_url":reverse("vendor_detail",args=[vendor.pk])})

@login_required
def vendor_detail(request,pk):
    vendor=get_object_or_404(Vendor,pk=pk)
    entries=list(vendor.sheet_entries.select_related("product").order_by("-entry_date","id"))
    stock=sum((e.stock for e in entries),Decimal("0")); sales=sum(((e.sales or 0) for e in entries),Decimal("0"))
    amount=sum((e.stock*e.price for e in entries if e.price is not None),Decimal("0"))
    prods={}
    for e in entries:
        d=prods.setdefault(e.product_id,{"product":e.product,"stock":Decimal("0"),"last":e.entry_date,"entries":0})
        d["stock"]+=e.stock; d["entries"]+=1
    products=sorted(prods.values(),key=lambda d:d["product"].name.lower())
    return render(request,"shop/vendor_detail.html",{"vendor":vendor,"entries":entries,"products":products,
        "total_stock":stock,"total_sales":sales,"total_amount":amount,"entry_count":len(entries)})

@login_required
def sale_create(request):
    form=SaleForm(request.POST or None,initial={"sale_date":timezone.localdate(),"customer_name":"Walk-in Customer","discount":0})
    if request.method=="POST" and form.is_valid():
        try:
            s=create_sale(sale_date=form.cleaned_data["sale_date"],customer_name=form.cleaned_data["customer_name"],customer_phone=form.cleaned_data["customer_phone"],discount=form.cleaned_data["discount"] or Decimal("0"),user=request.user,raw_lines=request.POST.get("items_json",""))
            messages.success(request,f"Sale {s.invoice_number} saved.")
            return redirect("sale_detail",pk=s.pk)
        except ValidationError as e: form.add_error(None," ".join(e.messages))
    latest={}
    for pid,price in SheetEntry.objects.exclude(price__isnull=True).order_by("entry_date","id").values_list("product_id","price"): latest[pid]=price   # newest wins
    products=[{"id":p["id"],"name":p["name"],"hsn_code":p["hsn_code"],"price":float(latest.get(p["id"],0))}
              for p in Product.objects.filter(is_active=True).order_by("name").values("id","name","hsn_code")]
    return render(request,"shop/sale_form.html",{"form":form,"products":products})

@login_required
def sale_list(request):
    return render(request,"shop/sale_list.html",{"sales":Sale.objects.select_related("created_by")[:200]})

@login_required
def sale_detail(request,pk):
    sale=get_object_or_404(Sale.objects.select_related("created_by").prefetch_related("items__product"),pk=pk)
    return render(request,"shop/sale_detail.html",{"sale":sale})

def _report_range(request):
    today=timezone.localdate()
    def parse(v,default):
        try: return datetime.strptime(v,"%Y-%m-%d").date()
        except (TypeError,ValueError): return default
    start=parse(request.GET.get("start"),today-timedelta(days=29)); end=parse(request.GET.get("end"),today)
    if start>end: start,end=end,start
    return start,end

@login_required
def reports(request):
    start,end=_report_range(request)
    rows=sheet_utils.daily_totals(start,end)            # only dates that have entries
    chart_rows=rows if (end-start).days<=92 else rows
    today=timezone.localdate()
    presets=[("Today",today,today),("Last 7 days",today-timedelta(days=6),today),("Last 30 days",today-timedelta(days=29),today),
             ("This month",today.replace(day=1),today)]
    return render(request,"shop/reports.html",{"start":start,"end":end,"rows":rows,"tot":sheet_utils.totals(rows),
        "chart":sheet_utils.chart_payload(rows),"vendor_rows":sheet_utils.vendor_totals(start,end),"presets":presets,"query":f"start={start.isoformat()}&end={end.isoformat()}"})

@login_required
def reports_pdf(request):
    start,end=_report_range(request)
    rows=sheet_utils.daily_totals(start,end)
    data=pdf_reports.report_pdf(_shop_name(),start,end,rows,sheet_utils.totals(rows),sheet_utils.vendor_totals(start,end))
    resp=HttpResponse(data,content_type="application/pdf")
    resp["Content-Disposition"]=f'attachment; filename="report_{start:%Y%m%d}_{end:%Y%m%d}.pdf"'
    return resp


# ===== Sheet module =====
def _sheet_filtered(request):
    q=request.GET.get("q","").strip(); start=request.GET.get("start","").strip(); end=request.GET.get("end","").strip()
    qs=SheetEntry.objects.select_related("product","vendor")
    if q: qs=qs.filter(Q(product__name__icontains=q)|Q(product__hsn_code__icontains=q)|Q(vendor__name__icontains=q))
    try:
        if start: qs=qs.filter(entry_date__gte=start)
        if end: qs=qs.filter(entry_date__lte=end)
        list(qs[:1])
    except (ValidationError,ValueError):
        start=end=""; qs=SheetEntry.objects.select_related("product","vendor")
    return qs.order_by("-entry_date","id"),q,start,end

def _safe_next(request):
    nxt=request.GET.get("next","")
    return nxt if nxt and url_has_allowed_host_and_scheme(nxt,allowed_hosts={request.get_host()}) else ""

def _sheet_page(request,form,editing=None):
    entries,q,start,end=_sheet_filtered(request)
    groups=sheet_utils.group_by_date(entries)
    counts=sheet_utils.date_counts()
    if editing:
        editing.sno=sheet_utils.sno_map([editing.entry_date]).get(editing.pk,1)
        next_sno=editing.sno
    else:
        d=form["entry_date"].value()
        next_sno=counts.get(str(d),0)+1
    products=list(Product.objects.filter(is_active=True).order_by("name").values("name","hsn_code"))
    vendors=list(Vendor.objects.order_by("name").values("name","phone"))
    return render(request,"shop/sheet.html",{"vendors":vendors,"form":form,"groups":groups,"entry_count":sum(len(g["rows"]) for g in groups),
        "q":q,"start":start,"end":end,"editing":editing,"next_sno":next_sno,"products":products,
        "date_counts":counts,"edit_info":{"date":editing.entry_date.isoformat(),"sno":editing.sno} if editing else None,
        "query":request.GET.urlencode(),"next_url":_safe_next(request)})

@login_required
def sheet(request):
    initial={"entry_date":timezone.localdate()}
    pid=request.GET.get("product","")
    pre=Product.objects.filter(pk=pid).first() if pid.isdigit() else None
    if pre: initial.update(product_name=pre.name,hsn_code=pre.hsn_code)
    form=SheetEntryForm(request.POST or None,initial=initial)
    if request.method=="POST" and form.is_valid():
        e=form.save(commit=False); e.created_by=request.user; e.save()
        sno=sheet_utils.sno_map([e.entry_date]).get(e.pk,"")
        messages.success(request,f"{e.entry_date:%d-%m-%Y} - S.No {sno} saved ({e.product.name}).")
        return redirect("sheet")
    return _sheet_page(request,form)

@login_required
def sheet_edit(request,pk):
    entry=get_object_or_404(SheetEntry.objects.select_related("product","vendor"),pk=pk)
    form=SheetEntryForm(request.POST or None,instance=entry)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Entry updated.")
        return redirect(_safe_next(request) or "sheet")
    return _sheet_page(request,form,editing=entry)

@login_required
@require_POST
def sheet_delete(request,pk):
    entry=get_object_or_404(SheetEntry,pk=pk); entry.delete()
    messages.success(request,"Entry deleted. S.No of that date is renumbered.")
    return redirect(_safe_next(request) or "sheet")

def _sheet_download(request,kind):
    entries,q,start,end=_sheet_filtered(request)
    entries=sheet_utils.number(entries)
    shop=_shop_name()
    stamp=timezone.localdate().strftime("%Y%m%d")
    if kind=="pdf":
        data=sheet_export.build_pdf(entries,shop,start,end); ctype="application/pdf"
    else:
        data=sheet_export.build_docx(entries,shop,start,end); ctype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    resp=HttpResponse(data,content_type=ctype)
    resp["Content-Disposition"]=f'attachment; filename="sheet_{stamp}.{"pdf" if kind=="pdf" else "docx"}"'
    return resp

@login_required
def sheet_pdf(request): return _sheet_download(request,"pdf")

@login_required
def sheet_word(request): return _sheet_download(request,"docx")
