from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('ttg.views',
    url(r'output/(?P<version>current)/feed.zip$', 'feed_zip', name='feed_zip'),
    url(r'output/(?P<version>current)/viewer/$', 'feed_zip', name='viewer'),
)
