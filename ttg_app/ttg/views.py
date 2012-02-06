from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

def home(request):
    return render_to_response(
        'ttg/home.html',
        {},
        RequestContext(request))

def feed_zip(request, version):
    return HttpResponse('Not implemented yet')

def viewer(request, version):
    return HttpResponse('Not implemented yet')