from zipfile import is_zipfile

from celery.decorators import task
from django.utils import timezone

from mtta.models import SignUp
from ttg.models import MediaFile


@task(ignore_result=True)
def import_mtta_signup(media_file_id):
    media_file = MediaFile.objects.get(id=media_file_id)

    assert(is_zipfile(media_file.file))
    signup = SignUp.objects.create(name='Imported at %s' % timezone.now())
    signup.import_zip(media_file.file)
    feed = signup.copy_to_feed()
    gtfs_str = StringIO.StringIO()
    feed.export_gtfs(gtfs_file)
    gtfs_file = ContentFile(gtfs_str.getvalue())
    gtfs = MediaFile.objects.create(
        file_type=MediaFile.GTFS_FILE, source=MediaFile.GENERATED)
    filename = 'gtfs_%s' % timezone.now().strftime('%Y-%m-%d')
    gtfs.file.save(filename, gtfs_file)
