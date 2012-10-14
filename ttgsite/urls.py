from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'ttg.views.home', name='home'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout',
        kwargs={'next_page': reverse_lazy('home')}),
    url(r'^ttg/', include('ttg.urls')),
)

if settings.ENABLE_ADMIN_DOCS:
    urlpatterns += patterns(
        '', url(r'^admin/doc/', include('django.contrib.admindocs.urls')))

urlpatterns += patterns(
    '', url(r'^admin/', include(admin.site.urls))
)

if settings.DEBUG:
    urlpatterns += patterns(
        '', url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.MEDIA_ROOT}),
    )
