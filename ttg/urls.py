from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'ttg.views',
    url(r'files/by_version/(?P<version>current)/feed.zip$', 'feed_zip',
        name='feed_zip'),
    url(r'files/$', 'file_list', name='file_list'),
    url(r'files/(?P<mediafile_id>\d+)/current$', 'set_version',
        kwargs=dict(version='current'), name='set_current'),
)
