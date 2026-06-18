from django.core.management.base import BaseCommand
from chatbot.services.whatsapp import WhatsAppService


class Command(BaseCommand):
    help = 'Check if the WhatsApp Cloud API token is valid'

    def handle(self, *args, **options):
        svc = WhatsAppService()
        result = svc.verify_token()
        if result.get('valid'):
            data = result.get('data', {})
            name = data.get('display_phone_number', data.get('id', '?'))
            self.stdout.write(self.style.SUCCESS(f'Token OK — {name}'))
        elif 'error' in result:
            self.stdout.write(self.style.ERROR(f"Connection error: {result['error']}"))
        else:
            err = result.get('data', {}).get('error', {})
            code = err.get('code', '?')
            msg = err.get('message', '?')
            self.stdout.write(self.style.ERROR(f'Token INVALID — error {code}: {msg}'))
