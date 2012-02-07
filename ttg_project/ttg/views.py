from datetime import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

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
    return HttpResponse('Not implemented yet')


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
