# Copyright 2016 Oursky Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

from .. import register_provider_class
from ...template import FileTemplate
from ...handlers.util.email import Mailer


logger = logging.getLogger(__name__)
try:
    # Available in py-skygear v1.6
    from skygear.utils.logging import setLoggerTag
    setLoggerTag(logger, 'auth_plugin')
except ImportError:
    pass


class SMTPProvider:
    def __init__(self, key, settings, text_template=None, html_template=None,
                 **kwargs):
        self.settings = settings
        if not text_template:
            text_template = FileTemplate('verify_{}_text'.format(key),
                                         'verify_email.txt',
                                         download_url=settings.email_text_url)
        self.text_template = text_template
        if not html_template:
            html_template = FileTemplate('verify_{}_html'.format(key),
                                         'verify_email.html',
                                         download_url=settings.email_html_url,
                                         required=False)
        self.html_template = html_template

    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('smtp_host', atype=str)
        parser.add_setting('smtp_port', atype=int, default=25)
        parser.add_setting('smtp_mode', atype=str, default='normal')
        parser.add_setting('smtp_login', atype=str, required=False)
        parser.add_setting('smtp_password', atype=str, required=False)
        parser.add_setting('smtp_sender_name', atype=str,
                           default='')
        parser.add_setting('smtp_sender', atype=str,
                           default='no-reply@skygeario.com')
        parser.add_setting('smtp_reply_to_name', atype=str,
                           default='')
        parser.add_setting('smtp_reply_to', atype=str,
                           default='no-reply@skygeario.com')
        parser.add_setting('subject', atype=str, resolve=False,
                           default='User Verification')
        parser.add_setting('email_text_url', atype=str, resolve=False,
                           required=False, default='')
        parser.add_setting('email_html_url', atype=str, resolve=False,
                           required=False, default='')
        return parser

    @property
    def smtp_settings(self):
        kwargs = {}
        for var_name in ['smtp_host', 'smtp_port', 'smtp_mode',
                         'smtp_login', 'smtp_password']:
            var_value = getattr(self.settings, var_name, None)
            if var_value:
                kwargs[var_name] = var_value
        return kwargs

    @property
    def _client(self):
        return Mailer(**self.smtp_settings)

    def send(self, recipient, template_params=None):
        template_params = template_params or {}
        text_body = self.text_template.render(**template_params)
        html_body = self.html_template.render(**template_params) \
            if self.html_template else None
        self._client.send_mail(
            (self.settings.smtp_sender_name, self.settings.smtp_sender),
            recipient,
            self.settings.subject,
            text_body,
            html_body,
            (self.settings.smtp_reply_to_name, self.settings.smtp_reply_to),
        )


register_provider_class('smtp', SMTPProvider)
