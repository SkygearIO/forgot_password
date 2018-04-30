import logging

from twilio.rest import Client

from .. import register_provider_class
from ...template import FileTemplate


logger = logging.getLogger(__name__)


class TwilioProvider:
    def __init__(self, key, settings, template=None, **kwargs):
        self.key = key
        self.settings = settings
        if not template:
            template = FileTemplate('verify_{}_text'.format(key),
                                    'verify_sms.txt',
                                    download_url=settings.sms_text_url)
        self.template = template

    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('twilio_account_sid', atype=str, required=True)
        parser.add_setting('twilio_auth_token', atype=str, required=True)
        parser.add_setting(
            'twilio_from',
            atype=str,
            required=True
        )
        parser.add_setting(
            'sms_text_url',
            atype=str,
            resolve=False,
            required=False
        )
        return parser

    @property
    def account_sid(self):
        return getattr(self.settings, 'twilio_account_sid')

    @property
    def auth_token(self):
        return getattr(self.settings, 'twilio_auth_token')

    @property
    def _client(self):
        return Client(self.account_sid, self.auth_token)

    def _message(self, recipient, template_params):
        return {
            'from_': self.settings.twilio_from,
            'to': recipient,
            'body': self.template.render(**template_params)
        }

    def send(self, recipient, template_params=None):
        msg = self._message(recipient, template_params or {})
        self._client.messages.create(**msg)
        logger.info('Sent SMS to `%s`. msg=%s', recipient, msg)


register_provider_class('twilio', TwilioProvider)
