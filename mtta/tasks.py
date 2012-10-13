from zipfile import is_zipfile
import StringIO

from celery.decorators import task
from django.core.files.base import ContentFile
from django.utils import timezone

from mtta.models import SignUp
from ttg.models import MediaFile


@task(ignore_result=True)
def import_mtta_signup(media_file_id):
    media_file = MediaFile.objects.get(id=media_file_id)

    signup = SignUp.objects.create(name='Imported at %s' % timezone.now())
    signup.import_zip(media_file.file)
    feed = signup.copy_to_feed()
    gtfs_str = StringIO.StringIO()
    feed.export_gtfs(gtfs_str)
    gtfs_file = ContentFile(gtfs_str.getvalue())
    gtfs = MediaFile.objects.create(
        file_type=MediaFile.GTFS_FILE, source=MediaFile.GENERATED)
    filename = 'gtfs_%s.zip' % timezone.now().strftime('%Y-%m-%d')
    gtfs.file.save(filename, gtfs_file)
