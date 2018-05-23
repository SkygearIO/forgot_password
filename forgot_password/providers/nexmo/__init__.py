import logging

import nexmo

from .. import register_provider_class
from ...template import FileTemplate


logger = logging.getLogger(__name__)
try:
    # Available in py-skygear v1.6
    from skygear.utils.logging import setLoggerTag
    setLoggerTag(logger, 'auth_plugin')
except ImportError:
    pass


class NexmoProvider:
    def __init__(self, key, settings, template=None, **kwargs):
        self.settings = settings
        if not template:
            template = FileTemplate('verify_{}_text'.format(key),
                                    'verify_sms.txt',
                                    download_url=settings.sms_text_url)
        self.template = template

    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('nexmo_api_key', atype=str, required=True)
        parser.add_setting('nexmo_api_secret', atype=str, required=True)
        parser.add_setting(
            'nexmo_from',
            atype=str,
            required=False,
            default='Skygear'
        )
        parser.add_setting(
            'sms_text_url',
            atype=str,
            resolve=False,
            required=False
        )
        return parser

    @property
    def api_key(self):
        return getattr(self.settings, 'nexmo_api_key')

    @property
    def api_secret(self):
        return getattr(self.settings, 'nexmo_api_secret')

    @property
    def _client(self):
        return nexmo.Client(key=self.api_key, secret=self.api_secret)

    def _message(self, recipient, template_params):
        return {
            'from': self.settings.nexmo_from,
            'to': recipient,
            'text': self.template.render(**template_params)
        }

    def send(self, recipient, template_params=None):
        msg = self._message(recipient, template_params or {})
        response = self._client.send_message(msg)
        response = response['messages'][0]
        success = (response['status'] == '0')
        if success:
            logger.info('Sent SMS to `%s`. msg=%s', recipient, msg)
        else:
            raise Exception('unable to send SMS')


register_provider_class('nexmo', NexmoProvider)
