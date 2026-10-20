import os
from .models import ShopProfile
DEFAULT_NAME="SRI VINAYAGA ELECTRICALS"; DEFAULT_CODE="SVE"
def shop_settings(request):
    profile = ShopProfile.objects.first()
    # old defaults ("My Shop"/"MYS") are ignored so the shop name always shows correctly
    cands=[profile.name if profile else "",os.getenv("SHOP_NAME","")]
    name=next((c.strip() for c in cands if c and c.strip() and c.strip()!="My Shop"),DEFAULT_NAME)
    cands=[profile.shop_code if profile else "",os.getenv("SHOP_CODE","")]
    code=next((c.strip() for c in cands if c and c.strip() and c.strip()!="MYS"),DEFAULT_CODE)
    return {"SHOP_NAME": name,"SHOP_CODE": code}
