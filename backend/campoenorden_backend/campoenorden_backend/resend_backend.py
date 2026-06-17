import json
import os
import urllib.error
import urllib.request

from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """
    Django email backend using Resend's HTTP API.
    Requires RESEND_API_KEY env var and a verified sender in resend.com.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = os.environ.get('RESEND_API_KEY', '')

    def send_messages(self, email_messages):
        if not self.api_key:
            if not self.fail_silently:
                raise RuntimeError('RESEND_API_KEY is not set')
            return 0

        sent = 0
        for msg in email_messages:
            try:
                payload = json.dumps({
                    'from': msg.from_email,
                    'to': list(msg.to),
                    'subject': msg.subject,
                    'text': msg.body,
                }).encode()

                req = urllib.request.Request(
                    'https://api.resend.com/emails',
                    data=payload,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json',
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp.read()
                sent += 1
            except urllib.error.HTTPError as exc:
                body = exc.read().decode(errors='replace')
                if not self.fail_silently:
                    raise RuntimeError(f'Resend API error {exc.code}: {body}') from exc
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
