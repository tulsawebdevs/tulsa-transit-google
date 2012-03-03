# Copy to local_settings.py and modify as desired

import os.path
ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('your_name', 'your_email'),
)

# Use a local SQLite3 database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path('ttg.sqlite'),       # create in this folder
    }
}

LOCAL_INSTALLED_APPS = []
# Add django-extensions manage.py commands, like runserver_plus
try:
    import django_extensions
except ImportError:
    pass
else:
    LOCAL_INSTALLED_APPS.append('django_extensions')
