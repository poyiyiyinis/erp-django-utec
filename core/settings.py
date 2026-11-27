

# core/settings.py

import dj_database_url
from datetime import timedelta
import environ
from pathlib import Path




BASE_DIR = Path(__file__).resolve().parent.parent




# ── VARIABLES DE ENTORNO ────────────────────────────────────────────────
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')


SECRET_KEY = env(
    'SECRET_KEY',
    default='dev-key-insegura-solo-para-desarrollo'
)
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = []




# ── APPS INSTALADAS ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    'core',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'anymail',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'django_filters',
    'rest_framework.authtoken',
    'whitenoise.runserver_nostatic',
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',
    'catalogo',
]




# ── MIDDLEWARE ──────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]




ROOT_URLCONF = 'core.urls'




# ── TEMPLATES ───────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.carrito_info',
            ],
        },
    },
]




# ── BASE DE DATOS ───────────────────────────────────────────────────────
# ── BASE DE DATOS ────────────────────────────────────────────────────────

DATABASE_URL = env('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }




# ── INTERNACIONALIZACIÓN ─────────────────────────────────────────────────
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True




# ── ARCHIVOS ESTÁTICOS ──────────────────────────────────────────────────
STATIC_URL = '/static/'


STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


STATIC_ROOT = BASE_DIR / 'staticfiles'


STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)


WHITENOISE_MANIFEST_STRICT = False




# ── ARCHIVOS MEDIA ──────────────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




# ── AUTENTICACIÓN ───────────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/productos/'
LOGOUT_REDIRECT_URL = '/'




# ── DJANGO REST FRAMEWORK ───────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 20,
}




DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




# ── STRIPE ───────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY = env(
    'STRIPE_SECRET_KEY',
    default='sk_test_placeholder'
)
STRIPE_PUBLISHABLE_KEY = env(
    'STRIPE_PUBLISHABLE_KEY',
    default='pk_test_placeholder'
)
STRIPE_WEBHOOK_SECRET = env(
    'STRIPE_WEBHOOK_SECRET',
    default='whsec_placeholder'
)




# ── CORREO ELECTRÓNICO ──────────────────────────────────────────────────
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)


DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='ERP Django <be.hernandezp.2528@cbtis198.edu.mx>'
)


EMAIL_SUBJECT_PREFIX = '[ERP Django] '


ADMINS = [
    ('Admin ERP', env(
        'ADMIN_EMAIL',
        default='admin@erp-django.com'
    )),
]


SENDGRID_API_KEY = env('SENDGRID_API_KEY', default='')


ANYMAIL = {
    'SENDGRID_API_KEY': SENDGRID_API_KEY,
}




# ── JAZZMIN ──────────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    'site_title': 'ERP Django',
    'site_header': 'ERP UTEC Celaya',
    'site_brand': '📦 ERP Django',
    'welcome_sign': 'Bienvenido al Sistema ERP · UTEC Celaya',
    'copyright': 'MC. Román Fernando López González · UTEC Celaya',


    'site_icon': None,
    'site_logo': None,


    'search_model': [
        'clientes.Cliente',
        'productos.Producto'
    ],


    'topmenu_links': [
        {'name': 'Inicio ERP', 'url': '/', 'new_window': False},
        {'name': 'Productos', 'url': '/productos/'},
        {'name': 'Clientes', 'url': '/clientes/'},
        {'name': 'Ventas', 'url': '/ventas/'},
    ],


    'usermenu_links': [
        {'name': 'Ver ERP', 'url': '/', 'new_window': False},
    ],


    'order_with_respect_to': [
        'clientes',
        'proveedores',
        'productos',
        'ventas',
        'configuracion',
        'auth',
    ],


    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'clientes.Cliente': 'fas fa-user-tie',
        'proveedores.Proveedor': 'fas fa-truck',
        'productos.Categoria': 'fas fa-tags',
        'productos.Producto': 'fas fa-box',
        'ventas.Venta': 'fas fa-file-invoice-dollar',
        'ventas.DetalleVenta': 'fas fa-list',
        'ventas.Pedido': 'fas fa-shopping-cart',
        'configuracion.ConfiguracionERP': 'fas fa-cogs',
    },


    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',


    'related_modal_active': True,
    'custom_css': 'erp_custom.css',
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],


    'changeform_format': 'horizontal_tabs',
    'language_chooser': False,
}




JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-dark',
    'accent': 'accent-navy',
    'navbar': 'navbar-dark',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-navy',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,


    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}




# ── DJANGO SITES ────────────────────────────────────────────────────────
SITE_ID = 1




# ── AUTHENTICATION BACKENDS ─────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]




# ── ALLAUTH ──────────────────────────────────────────────────────────────
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True




# ── CELERY ───────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env(
    'REDIS_URL',
    default='redis://localhost:6379/0'
)


CELERY_RESULT_BACKEND = env(
    'REDIS_URL',
    default='redis://localhost:6379/0'
)


CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True


CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 360


CELERY_TASK_DEFAULT_QUEUE = 'erp_django'


CELERY_TASK_ALWAYS_EAGER = DEBUG
CELERY_TASK_EAGER_PROPAGATES = True




# ── CELERY BEAT — TAREAS PROGRAMADAS ────────────────────────────────────
from celery.schedules import crontab




# Configuración de hora del reporte desde Render
REPORTE_DIARIO_HORA = env(
    'REPORTE_DIARIO_HORA',
    default='18:12'
)


try:
    _rep_h, _rep_m = map(
        int,
        REPORTE_DIARIO_HORA.split(':')
    )


    if not (0 <= _rep_h <= 23 and 0 <= _rep_m <= 59):
        raise ValueError('Hora fuera de rango')


except (ValueError, AttributeError):
    _rep_h, _rep_m = 18, 12




CELERY_BEAT_SCHEDULE = {
    'verificar-stock-bajo-cada-hora': {
        'task': 'ventas.verificar_stock_bajo',
        'schedule': timedelta(hours=1),
        'args': (5,),
        'options': {'queue': 'erp_django'},
    },


    'reporte-ventas-diario': {
        'task': 'ventas.reporte_ventas_diario',
        'schedule': crontab(
            hour=_rep_h,
            minute=_rep_m
        ),
        'options': {'queue': 'erp_django'},
    },
}