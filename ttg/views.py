from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.template import RequestContext

from forms import UploadFileForm
from models import MediaFile, Version


def home(request):
    '''View for the home page'''
    return render_to_response(
        'ttg/home.html',
        {},
        RequestContext(request))


def feed_zip(request, version):
    '''View for an output GTFS zip file'''
    feed = get_object_or_404(MediaFile, file_type=MediaFile.GTFS_FILE, version__name=version)
    wrapper = FileWrapper(feed.file)
    response = HttpResponse(wrapper, content_type='text/plain')
    response['Content-Length'] = feed.file.size
    return response


def set_version(request, version, mediafile_id):
    assert request.method == 'POST'
    mediafile = get_object_or_404(MediaFile, id=mediafile_id)
    Version.objects.filter(mediafile__file_type=mediafile.file_type, name=version).delete()
    Version.objects.get_or_create(name=version, mediafile=mediafile)
    return redirect('file_list')


@login_required
def file_list(request):
    '''View for files, including upload form'''
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.info(request,
                          'File uploaded as %s' % form.instance.file.name)
            return redirect('file_list')
    else:
        form = UploadFileForm()
    return render_to_response(
        'ttg/file_list.html',
        {'form': form, 'files': MediaFile.objects.all()},
        RequestContext(request))
