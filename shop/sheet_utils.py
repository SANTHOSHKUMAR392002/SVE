"""Helpers for the Sheet module: S.No is counted per date (1,2,3... restarting every date)."""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from .models import SheetEntry


def sno_map(dates):
    """{entry_pk: S.No} for every entry on the given dates (S.No = position inside its own date)."""
    counters, result = {}, {}
    qs = SheetEntry.objects.filter(entry_date__in=list(dates)).order_by("entry_date", "id").values_list("id", "entry_date")
    for pk, d in qs:
        counters[d] = counters.get(d, 0) + 1
        result[pk] = counters[d]
    return result


def number(entries):
    """Return entries as a list, each with .sno set to its per-date S.No."""
    entries = list(entries)
    m = sno_map({e.entry_date for e in entries})
    for e in entries:
        e.sno = m.get(e.pk, 0)
    return entries


def group_by_date(entries):
    """entries (already ordered by date) -> [{'date':date,'rows':[entries],'stock':..,'sales':..}]"""
    groups, index = [], {}
    for e in number(entries):
        g = index.get(e.entry_date)
        if g is None:
            g = index[e.entry_date] = {"date": e.entry_date, "rows": [], "stock": 0, "sales": 0}
            groups.append(g)
        g["rows"].append(e)
        g["stock"] += e.stock
        g["sales"] += (e.sales or 0)
    return groups


def date_counts():
    """{'2026-10-14': 3, ...} - how many entries each date already has (to show the next S.No)."""
    return {d.isoformat(): n for d, n in
            SheetEntry.objects.values_list("entry_date").annotate(n=Count("id")).order_by()}


def daily_totals(start, end, fill=False):
    """Date-wise totals between start and end (dates). Returns list of dicts:
    {date, stock, sales, balance, entries}. fill=True adds zero rows for dates with no entries."""
    rows = (SheetEntry.objects.filter(entry_date__range=(start, end)).values("entry_date")
            .annotate(st=Sum("stock"), sa=Sum("sales"), n=Count("id")).order_by("entry_date"))
    by = {r["entry_date"]: r for r in rows}
    days = []
    if fill:
        d = start
        while d <= end:
            days.append(d); d += timedelta(days=1)
    else:
        days = sorted(by)
    out = []
    for d in days:
        r = by.get(d)
        st = (r["st"] if r else None) or Decimal("0"); sa = (r["sa"] if r else None) or Decimal("0")
        out.append({"date": d, "stock": st, "sales": sa, "balance": st - sa, "entries": r["n"] if r else 0})
    return out


def vendor_totals(start, end):
    """Vendor-wise totals between start and end (with GST number)."""
    from django.db.models import F, DecimalField, ExpressionWrapper
    amt = ExpressionWrapper(F("stock") * F("price"), output_field=DecimalField(max_digits=18, decimal_places=2))
    qs = (SheetEntry.objects.filter(entry_date__range=(start, end), vendor__isnull=False)
          .values("vendor_id", "vendor__name", "vendor__gst_number")
          .annotate(st=Sum("stock"), sa=Sum("sales"), n=Count("id"), amount=Sum(amt)).order_by("vendor__name"))
    return [{"id": r["vendor_id"], "name": r["vendor__name"], "gst": r["vendor__gst_number"], "entries": r["n"],
             "stock": r["st"] or Decimal("0"), "sales": r["sa"] or Decimal("0"), "amount": r["amount"] or Decimal("0")} for r in qs]


def totals(rows):
    st = sum((r["stock"] for r in rows), Decimal("0")); sa = sum((r["sales"] for r in rows), Decimal("0"))
    return {"stock": st, "sales": sa, "balance": st - sa, "entries": sum(r["entries"] for r in rows)}


def chart_payload(rows):
    """JSON-friendly data for the Chart.js bar chart (static/js/charts.js)."""
    return {"labels": [r["date"].isoformat() for r in rows],
            "stock": [float(r["stock"]) for r in rows],
            "sales": [float(r["sales"]) for r in rows]}
