import re
from decimal import Decimal, ROUND_HALF_UP
from django import forms
from .models import Category, Product, Vendor, SheetEntry
class StyledModelForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"]=("form-check-input" if isinstance(f.widget,forms.CheckboxInput) else "form-control")
class CategoryForm(StyledModelForm):
    class Meta: model=Category; fields=["name","code","description"]
class ProductForm(StyledModelForm):
    """Products module: only product name + HSN code."""
    class Meta:
        model=Product; fields=["name","hsn_code"]
        labels={"name":"Product name","hsn_code":"HSN code"}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["hsn_code"].required=True
    def clean_name(self):
        name=" ".join(self.cleaned_data["name"].split())
        dup=Product.objects.filter(name__iexact=name)
        if self.instance.pk: dup=dup.exclude(pk=self.instance.pk)
        if dup.exists(): raise forms.ValidationError("This product already exists.")
        return name
    def clean_hsn_code(self): return self.cleaned_data["hsn_code"].strip()
class VendorForm(StyledModelForm):
    class Meta:
        model=Vendor; fields=["name","phone","email","gst_number","address"]
        labels={"gst_number":"GST number"}
        widgets={"gst_number":forms.TextInput(attrs={"placeholder":"e.g. 33ABCDE1234F1Z5","maxlength":"15","style":"text-transform:uppercase"}),
                 "address":forms.Textarea(attrs={"rows":3})}
    def clean_gst_number(self):
        g="".join(self.cleaned_data.get("gst_number","").split()).upper()
        if g and not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]",g):
            raise forms.ValidationError("Enter a valid 15-character GST number (e.g. 33ABCDE1234F1Z5).")
        return g
class PurchaseForm(forms.Form):
    vendor=forms.ModelChoiceField(queryset=Vendor.objects.all(),widget=forms.Select(attrs={"class":"form-select"}))
    purchase_date=forms.DateField(widget=forms.DateInput(attrs={"type":"date","class":"form-control"}))
    vendor_invoice=forms.CharField(required=False,widget=forms.TextInput(attrs={"class":"form-control"}))
class SaleForm(forms.Form):
    sale_date=forms.DateField(widget=forms.DateInput(attrs={"type":"date","class":"form-control"}))
    customer_name=forms.CharField(required=False,initial="Walk-in Customer",widget=forms.TextInput(attrs={"class":"form-control"}))
    customer_phone=forms.CharField(required=False,widget=forms.TextInput(attrs={"class":"form-control"}))
    discount=forms.DecimalField(required=False,min_value=0,initial=0,widget=forms.NumberInput(attrs={"class":"form-control","step":"0.01"}))

class SheetEntryForm(StyledModelForm):
    """Date, product (name + HSN), stock bought, sales, price.
    If the product name already exists in the Products module its HSN is used (fixed);
    otherwise a new product (name + HSN) is created in the Products module on save."""
    product_name=forms.CharField(max_length=200,label="Product name",widget=forms.TextInput(
        attrs={"autocomplete":"off","placeholder":"Type to search products"}))
    hsn_code=forms.CharField(max_length=20,required=False,label="HSN code",widget=forms.TextInput(
        attrs={"inputmode":"numeric","placeholder":"Auto-fills when you pick a product"}))
    vendor_name=forms.CharField(max_length=160,required=False,label="Vendor name",widget=forms.TextInput(
        attrs={"autocomplete":"off","placeholder":"Type to search vendors"}))
    field_order=["entry_date","product_name","hsn_code","vendor_name","stock","sales","mrp","disc","price"]
    class Meta:
        model=SheetEntry
        fields=["entry_date","stock","sales","mrp","disc","price"]
        labels={"entry_date":"Date","sales":"Sales (optional)","mrp":"MRP (optional)","disc":"Disc % (optional)","price":"Price"}
        widgets={
            "entry_date":forms.DateInput(attrs={"type":"date"},format="%Y-%m-%d"),
            "stock":forms.NumberInput(attrs={"step":"any","min":"0"}),
            "sales":forms.NumberInput(attrs={"step":"any","min":"0","placeholder":"Leave empty if none"}),
            "mrp":forms.NumberInput(attrs={"step":"0.01","min":"0","placeholder":"MRP"}),
            "disc":forms.NumberInput(attrs={"step":"0.01","min":"0","max":"100","placeholder":"Discount %"}),
            "price":forms.NumberInput(attrs={"step":"0.01","min":"0","placeholder":"Price (MRP - Disc %)"}),
        }
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance.pk:
            self.initial.setdefault("product_name",self.instance.product.name)
            self.initial.setdefault("hsn_code",self.instance.product.hsn_code)
            if self.instance.vendor_id: self.initial.setdefault("vendor_name",self.instance.vendor.name)
        self._product=None; self._vendor=None
        self.fields["price"].required=False   # may be auto-filled from MRP - Disc (checked in clean)
    def clean(self):
        data=super().clean()
        mrp,disc,price=data.get("mrp"),data.get("disc"),data.get("price")
        if mrp is not None:            # MRP given -> price = MRP - Disc (disc optional)
            disc=disc or Decimal("0")
            if disc>100: self.add_error("disc","Disc % cannot be more than 100.")
            else: data["price"]=(mrp-mrp*disc/Decimal("100")).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
        elif disc is not None and price is None:
            self.add_error("mrp","Enter MRP too, or just type the Price.")
        if data.get("price") is None and not self.errors.get("price") and not self.errors.get("mrp") and not self.errors.get("disc"):
            self.add_error("price","Price is required.")
        name=" ".join((data.get("product_name") or "").split())
        if name:
            data["product_name"]=name
            self._product=Product.objects.filter(name__iexact=name).order_by("id").first()
            if not self._product and not (data.get("hsn_code") or "").strip():
                self.add_error("hsn_code","HSN code is required for a new product.")
        vname=" ".join((data.get("vendor_name") or "").split())
        data["vendor_name"]=vname
        if vname: self._vendor=Vendor.objects.filter(name__iexact=vname).order_by("id").first()
        stock,sales=data.get("stock"),data.get("sales")
        if stock is not None and sales is not None and sales>stock:
            self.add_error("sales",f"Sales cannot be more than the stock of this entry ({stock.normalize():f}).")
        return data
    def save(self,commit=True):
        entry=super().save(commit=False)
        entry.price=self.cleaned_data["price"]
        product=self._product
        if product is None:
            product=Product.objects.create(name=self.cleaned_data["product_name"],hsn_code=self.cleaned_data["hsn_code"].strip())
        elif not product.is_active:
            product.is_active=True; product.save(update_fields=["is_active"])
        entry.product=product
        vname=self.cleaned_data.get("vendor_name") or ""
        if vname:
            vendor=self._vendor or Vendor.objects.create(name=vname)
            vendor.products.add(product)
            entry.vendor=vendor
        else:
            entry.vendor=None
        if commit: entry.save()
        return entry
