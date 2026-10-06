"""Check chatbot configuration without printing credentials or using generation quota."""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from chatbot.services import configured_model


class Command(BaseCommand):
    help = 'Check rental assistant configuration; optionally check Gemini model metadata (no text generation).'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--check-provider', action='store_true')

    def handle(self, *args, **options):
        model = configured_model()
        if not model:
            raise CommandError('GEMINI_MODEL is invalid. Use a Gemini model ID without a URL.')
        self.stdout.write(f'Model: {model}')
        if not settings.GEMINI_API_KEY:
            self.stdout.write('API key: not configured. Local rental FAQs still work.')
            return
        self.stdout.write('API key: configured (value hidden).')
        if not options['check_provider']:
            return
        try:
            response = requests.get(
                f'https://generativelanguage.googleapis.com/v1beta/models/{model}',
                headers={'x-goog-api-key': settings.GEMINI_API_KEY},
                timeout=(3, 12), allow_redirects=False,
            )
        except requests.RequestException:
            raise CommandError('Could not reach Gemini. Check networking and try again.') from None
        if response.status_code != 200:
            raise CommandError(f'Gemini model metadata returned HTTP {response.status_code}. Check the key and model access.')
        self.stdout.write('Model metadata reachable. Generation quota and project billing tier were not checked.')
