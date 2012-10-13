import os.path

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel


class MediaFile(TimeStampedModel):
    '''An uploaded or generated file'''
    MTTA_SIGNUP = u'S'
    GTFS_FILE = u'F'
    TYPE_CHOICES = (
        (MTTA_SIGNUP, 'MTTA Signup .zip'),
        (GTFS_FILE, 'GTFS Feed .zip'),
    )

    UPLOADED = u'u'
    GENERATED = u'g'
    SOURCE_CHOICES = (
        (UPLOADED, u'Uploaded'),
        (GENERATED, u'Generated'),
    )

    file = models.FileField(upload_to='ttg-media')
    file_type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)

    def __unicode__(self):
        return self.file.name
