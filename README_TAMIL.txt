SHOP MANAGEMENT WEBSITE - LOCAL SETUP

இந்த project-ல் உள்ளவை:
- Login மற்றும் பல user accounts (Django admin மூலம் users உருவாக்கலாம்)
- Product/category/vendor management
- ஒவ்வொரு product-க்கும் shop code + category code + unique number கொண்ட ID
- Purchase entry செய்தால் stock தானாக அதிகரிக்கும்
- Sales entry செய்தால் stock தானாகக் குறையும்; stock போதவில்லை என்றால் sale நிராகரிக்கப்படும்
- Stock history, invoice number, print bill
- Date range sales, purchase, gross profit reports
- Default database SQLite; MySQL-க்கு மாற்றவும் configuration உள்ளது

WINDOWS-ல் RUN செய்வது:
1. Python 3.11 அல்லது அதற்கு மேல் install செய்யவும்.
2. ZIP-ஐ extract செய்யவும்.
3. Extract செய்த folder-ல் Command Prompt / PowerShell திறக்கவும்.
4. Commands:

   py -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   py manage.py makemigrations shop
   py manage.py migrate
   py manage.py createsuperuser
   py manage.py runserver

5. Browser-ல் http://127.0.0.1:8000/ திறக்கவும்.
6. createsuperuser மூலம் உருவாக்கிய username/password கொண்டு login செய்யவும்.
7. முதலில் Categories பக்கத்தில் category உருவாக்கவும். உதாரணம்: Switches / Code: SW.
8. Products பக்கத்தில் product சேர்க்கவும். ID தானாக MYS-SW-000001 போன்ற வடிவில் உருவாகும்.
9. Vendors-ல் supplier சேர்த்து, Purchases / Stock In வழியாக வந்த stock பதிவு செய்யவும்.
10. Sales / Bills-ல் sale பதிவு செய்து bill-ஐ Print செய்யவும்.

MYSQL பயன்படுத்த:
- MySQL Server நிறுவி database உருவாக்கவும்:
  CREATE DATABASE shop_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
- .env-ல் DB_ENGINE=mysql மற்றும் DB_NAME, DB_USER, DB_PASSWORD values மாற்றவும்.
- mysqlclient install ஆகவில்லை என்றால் Windows-ல் compatible wheel / build tools தேவைப்படலாம்.
- MySQL configuration மாற்றிய பிறகு migrate ஓட்டவும்.

குறிப்பு:
- இது local development starter project. Internet-ல் deploy செய்வதற்கு முன் DEBUG=False, secure SECRET_KEY,
  ALLOWED_HOSTS, HTTPS, backups, permissions, returns/expense/tax rules போன்றவற்றை configure செய்து test செய்யவும்.
- பல users உருவாக்க / permissions அமைக்க /admin/ பயன்படுத்தவும்.
- Shop name/code மாற்ற, /admin/ இல் Shop profiles சேர்க்கவும். Shop code unique ஆக இருக்க வேண்டும்.

NEW CHANGES (Sheet module)
- pip install -r requirements.txt   (openpyxl add aagi irukku)
- py manage.py makemigrations shop
- py manage.py migrate
  (Product-la HSN code field, Sheet-la price optional - so migration kandippa run pannunga)


=====================================================
LATEST CHANGES (Date-wise Sheet + Products module)
=====================================================
- Shop name: SRI VINAYAGA ELECTRICALS (sidebar, login, PDF/Word)
- Sheet: S.No ovvoru date-kum 1 la irundhu start aagum (date-wise). Entry delete panna antha date-oda S.No thaanaa maarum.
- Quantity field remove pannitten. Fields: Date, Product name, HSN code, Stock, Sales, Price.
- Sales: antha date-oda (antha row-oda) stock mattum kuraiyum (Balance = Stock - Sales).
  Pudhusa vera date-la same product vaangina antha stock disturb aagaadhu.
- Product name dropdown: type pannum podhu mattum, match aagura product names kaattum. Click panna HSN code fix aagum.
  Pudhu name type panna HSN neengale podanum - athu Products module-la save aagum.
- Products module: Name + HSN mattum. Product-ah click panna date-wise history (Date, HSN, Stock, Sales, Balance, Price, Edit).
- Excel import remove pannitten.

DATABASE MAATHAM (mukkiyam):
Sheet table structure maariyirukku, so test data-va keep panna mudiyaadhu. Fresh ah start panna:
   1. server stop (Ctrl+C)
   2. db.sqlite3 file-a delete pannunga
   3. shop\migrations folder irundha atha delete pannunga
   4. py manage.py makemigrations shop
   5. py manage.py migrate
   6. py manage.py createsuperuser
   7. py manage.py runserver


=====================================================
LATEST CHANGES (Vendor in Sheet, Dashboard graph, Reports PDF)
=====================================================
- Sidebar: "Purchases / Stock In" and "Categories" remove pannitten.
- Sheet: pudhu "Vendor name" field. Mudhal thadavai type pannina Vendors-la save aagum;
  adutha thadavai type pannum podhu match aagura vendor names dropdown-la varum.
- Vendors: vendor name click -> details + product list + date-wise history. "Edit vendor" button irukku.
- Products: "Download PDF" button (search pannina filtered list-um download aagum).
- Dashboard: Stock vs Sales graph (X = date, Y = quantity). 7 / 15 / 30 / 90 days select pannalaam.
  (Graph-ku internet venum - Chart.js CDN-la irundhu load aagum.)
- Reports: date range apply pannina date-wise Stock / Sales / Balance + graph. "Export PDF" button.

DATABASE: Sheet-la vendor column add aagirukku. Run pannunga (data poagaadhu):
   py manage.py makemigrations shop
   py manage.py migrate


=====================================================
LATEST CHANGES (MRP/Disc, zig-zag graph, Bill page)
=====================================================
- PDF downloads: table mattum (graph remove pannitten).
- Stock History page/menu remove pannitten.
- Graph: bar-ku bathila zig-zag line graph (Dashboard + Reports).
- Sheet: pudhu "MRP" & "Disc" fields (rendum optional). Price mandatory.
  MRP kuduthaa  Price = MRP - Disc  automatic-a varum. MRP illaina Price neengale type pannalaam.
  PDF / Word / Products / Vendor history-la MRP, Disc columns irukku.
- Sales / Bill: product name type pannunga -> dropdown-la select pannunga -> HSN auto.
  Quantity (+ / -) maathina Price = Qty x Unit price auto-a maarum. Sub total & Grand total live-a theriyum.
  Unit price = antha product-oda latest Sheet price (maathikalaam).

DATABASE: Sheet-la mrp, disc fields add aagirukku (price ippo required). Run pannunga:
   py manage.py makemigrations shop
   py manage.py migrate
   (migrations folder illaina "makemigrations shop" thaan mudhalla run pannanum. Pazhaya data irundha price illaadha rows-ku migrate-la default kekkum - 0 kudunga.)


=====================================================
FINAL CHANGES (Disc %, Vendor GST)
=====================================================
- Sheet: "Disc" ippo PERCENTAGE. Price = MRP - (MRP x Disc / 100). Udhaaranam: MRP 200, Disc 15% -> Price 170.
  Sheet table, PDF, Word, Product & Vendor history-la "Disc %" nu varum.
- Vendor: pudhu "GST number" field (optional, 15 character GSTIN - thappa irundha error kaattum).
  Vendors list, Vendor detail, Vendor edit/add form, Reports page & Reports PDF (Vendor-wise supply table) - ellathulayum varum.
- Vendors search-la GST number-um search pannalaam.

DATABASE: gst_number, disc maathram - run pannunga:
   py manage.py makemigrations shop
   py manage.py migrate


=====================================================
LOGO & WATERMARK
=====================================================
- Ganesh image-a transparent background PNG logo-va maathitten (static/img/logo.png, watermark.png, favicon.png).
- Logo: Sidebar, Login page, Bill header, browser tab icon.
- Bill page: nadula periya watermark (print-layum varum). Print bill click pannunga.
- Whole site: ellaa pages-layum romba light-a watermark (data padikka disturb aagaadhu).
- PDF downloads: faint watermark.
- Watermark kuraikka/kootta: static/css/app.css-la ".site-wm" (opacity .045) & ".inv-watermark" (opacity .08) maathunga.
