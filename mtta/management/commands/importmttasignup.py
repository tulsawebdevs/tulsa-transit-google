from optparse import make_option
import logging
import os.path
import shutil
import tempfile
import zipfile

from django.db import connection
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mtta.models import SignUp


class Command(BaseCommand):
    args = '<path/to/import>'
    help = 'Import a Tulsa Transit (MTTA) Signup (data+schedule)'
    option_list = BaseCommand.option_list + (
        make_option(
            '-n', '--name', type='string', dest='name',
            help='Set the name of the imported signup'),)

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('You must pass in the path to the signup.')
        if len(args) > 1:
            raise CommandError('You can only import one signup at a time.')

        # Parse input type
        input_path = args[0]
        if os.path.isdir(input_path):
            is_folder = True
        elif zipfile.is_zipfile(input_path):
            is_folder = False
        else:
            raise CommandError(
                '%s is neither a folder or a .zip file' % input_path)
        name = options.get('name') or SignUp._unset_name

        # Setup logging
        verbosity = int(options.get('verbosity', 1))
        if verbosity == 0:
            level = logging.WARNING
        elif verbosity == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        logger = logging.getLogger('mtta.models')
        handler = logging.StreamHandler(self.stdout)
        handler.setLevel(level)
        logger.addHandler(handler)
        logger.setLevel(level)

        # Disable database query logging
        if settings.DEBUG:
            connection.use_debug_cursor = False

        # Extract zip files to temp folder
        tmp_path = None
        if not is_folder:
            tmp_path = tempfile.mkdtemp(prefix='mtta')
            self.stdout.write(
                "Extracting %s to %s..." % (input_path, tmp_path))
            z = zipfile.ZipFile(input_path)
            z.extractall(tmp_path)
            input_path = tmp_path

        # Import the signup
        signup = SignUp.objects.create(name=name)
        signup.import_folder(input_path)

        # Set the name to the current time
        if signup.name == SignUp._unset_name:
            signup.name = 'Imported at %s' % timezone.now()
            signup.save()

        # Remove temporary files
        if tmp_path:
            self.stdout.write("Removing temporary folder %s" % tmp_path)
            shutil.rmtree(tmp_path)

        self.stdout.write("Successfully imported SignUpFeed %s\n" % (signup))
