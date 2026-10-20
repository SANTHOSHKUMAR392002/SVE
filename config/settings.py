import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
SECRET_KEY = os.getenv("SECRET_KEY", "local-dev-key-change-before-deploying")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    x.strip()
    for x in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,sve-4qp7.onrender.com"
    ).split(",")
]
INSTALLED_APPS = [
 "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
 "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","shop",
]
MIDDLEWARE = [
 "django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware",
 "django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware",
 "django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware",
 "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],
 "APP_DIRS":True,"OPTIONS":{"context_processors":[
 "django.template.context_processors.request","django.contrib.auth.context_processors.auth",
 "django.contrib.messages.context_processors.messages","shop.context_processors.shop_settings"]}}]
WSGI_APPLICATION = "config.wsgi.application"
if os.getenv("DB_ENGINE", "sqlite").lower() == "mysql":
    DATABASES = {"default":{"ENGINE":"django.db.backends.mysql","NAME":os.getenv("DB_NAME","shop_management"),
      "USER":os.getenv("DB_USER","shop_user"),"PASSWORD":os.getenv("DB_PASSWORD",""),
      "HOST":os.getenv("DB_HOST","127.0.0.1"),"PORT":os.getenv("DB_PORT","3306"),
      "OPTIONS":{"charset":"utf8mb4"}}}
else:
    DATABASES = {"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = [
 {"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
 {"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},
 {"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},
 {"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE="en-in"; TIME_ZONE="Asia/Kolkata"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATICFILES_DIRS=[BASE_DIR/"static"]
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
LOGIN_URL="login"; LOGIN_REDIRECT_URL="dashboard"; LOGOUT_REDIRECT_URL="login"
