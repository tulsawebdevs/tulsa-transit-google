from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import transitfeed

from forms import UploadFileForm
from models import MediaFile

def home(request):
    '''View for the home page'''
    return render_to_response(
        'ttg/home.html',
        {},
        RequestContext(request))


def feed_zip(request, version):
    '''View for an output GTFS zip file'''
    return HttpResponse('Not implemented yet')


def viewer(request, version):
    '''View for the schedule viewer'''
    current_feed = MediaFile.objects.filter(file_type='F').latest('added_at')
    schedule_key = 'schedule.%d' % current_feed.id 
    schedule = cache.get(schedule_key)
    if not schedule:    
        schedule = transitfeed.Schedule(
            problem_reporter=transitfeed.ProblemReporter())
        current_feed = MediaFile.objects.filter(
            file_type='F').latest('added_at')
        schedule.Load(current_feed.abspath())
        cache.set(schedule_key, schedule)

    return render_to_response(
        'ttg/viewer.html',
        {},
        RequestContext(request))


def file_list(request):
    '''View for files, including upload form'''
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.save_upload(request.FILES['upload'])
            messages.info(request,
                          'File uploaded as %s' % form.instance.local_name)
            form = UploadFileForm()
    else:
        form = UploadFileForm()
    return render_to_response(
        'ttg/file_list.html',
        {'form': form, 'files': MediaFile.objects.all()},
        RequestContext(request))
