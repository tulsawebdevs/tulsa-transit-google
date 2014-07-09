import logging

from django.core.management.base import BaseCommand, CommandError

from mtta.models import SignUp


class Command(BaseCommand):
    args = '<signup_id>'
    help = 'Copy a Tulsa Transit (MTTA) Signup to GTFS'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('You must pass in the ID of the MTTA signup.')
        if len(args) > 1:
            raise CommandError('You can only copy one signup at a time.')
        signup_id = args[0]
        try:
            signup = SignUp.objects.get(id=signup_id)
        except SignUp.DoesNotExist:
            raise CommandError('No signup %s found.' % signup_id)
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
        feed = signup.copy_to_feed()
        self.stdout.write(
            "Successfully copied SignUpFeed %s to Feed %s\n" %
            (signup, feed))
