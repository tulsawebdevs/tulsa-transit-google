# Copy to local_settings.py and modify as desired

import os.path
import sys
ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('your_name', 'your_email'),
)

# Use a local Spatialite (SQLite3 + GIS) database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': path('ttg.sqlite'),       # create in this folder
    }
}

# postgres version
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'ttg_project',
        'USER': 'ttg',
        'PASSWORD': 'ggt',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
'''

LOCAL_INSTALLED_APPS = []
# Add django-extensions manage.py commands, like runserver_plus
try:
    import django_extensions
except ImportError:
    pass
else:
    assert django_extensions
    LOCAL_INSTALLED_APPS.append('django_extensions')

# To use nose to run tests, install django_nose and enable below
if False and 'test' in sys.argv:
    DATABASES['default']['NAME'] = ':memory:'
    LOCAL_INSTALLED_APPS.append('django_nose')
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
