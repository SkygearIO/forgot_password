import logging

from .. import register_provider_class


class DebugProvider:
    def __init__(self, key, settings, **kwargs):
        self.key = key
        self.settings = settings

    @classmethod
    def configure_parser(cls, key, parser):
        return parser

    def send(self, recipient, template_params=None):
        msg = 'DebugProvider: Requested to send to `%s`. template_params=%s'
        logging.info(msg, recipient, str(template_params))


register_provider_class('debug', DebugProvider)
