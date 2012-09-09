from datetime import datetime
from optparse import make_option
import logging

from django.core.management.base import BaseCommand, CommandError

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
        input_folder = args[0]
        name = options.get('name') or 'Imported at %s' % datetime.now()
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
        signup.import_folder(input_folder)
        self.stdout.write("Successfully imported SignUpFeed %s\n" % (signup))
