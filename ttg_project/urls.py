from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'ttg_project.ttg.views.home', name='home'),
    url(r'^ttg/', include('ttg_project.ttg.urls')),
)

if settings.ENABLE_ADMIN_DOCS:
    urlpatterns += patterns('',
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')))

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls))
)
