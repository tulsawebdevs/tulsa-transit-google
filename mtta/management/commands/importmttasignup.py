from optparse import make_option
import logging
import os.path
import zipfile

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
        input_path = args[0]
        if os.path.isdir(input_path):
            is_folder = True
        elif zipfile.is_zipfile(input_path):
            is_folder = False
        else:
            raise CommandError(
                '%s is neither a folder or a .zip file' % input_path)
        name = options.get('name') or SignUp._unset_name
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
        signup = SignUp.objects.create(name=name)
        if is_folder:
            signup.import_folder(input_path)
        else:
            signup.import_zip(input_path)
        if signup.name == SignUp._unset_name:
            signup.name = 'Imported at %s' % timezone.now()
            signup.save()
        self.stdout.write("Successfully imported SignUpFeed %s\n" % (signup))
