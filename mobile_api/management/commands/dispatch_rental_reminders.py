import json
from django.core.management.base import BaseCommand
from mobile_api.reminders import dispatch_reminders


class Command(BaseCommand):
    help = 'Preview rental reminders; use --send after configuring delivery and staff devices.'

    def add_arguments(self, parser):
        parser.add_argument('--send', action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(dispatch_reminders(dry_run=not options['send'])))
