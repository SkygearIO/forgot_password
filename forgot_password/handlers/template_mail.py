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

from .template import StringTemplate
from .util import email as email_util

logger = logging.getLogger(__name__)


class TemplateMailSender:
    def __init__(self,
                 template_provider,
                 smtp_settings,
                 text_template_name,
                 html_template_name):
        self._template_provider = template_provider
        self._smtp_settings = smtp_settings
        self._text_template_name = text_template_name
        self._html_template_name = html_template_name

    @property
    def template_provider(self):
        return self._template_provider

    @property
    def smtp_settings(self):
        return self._smtp_settings

    @property
    def text_template_name(self):
        return self._text_template_name

    @property
    def html_template_name(self):
        return self._html_template_name

    @property
    def fallback_text_template(self):
        return self.template_provider.get_template(self.text_template_name)

    @property
    def fallback_html_template(self):
        return self.template_provider.get_template(self.html_template_name)

    def send(self, sender, email, subject,
             text_template_string=None,
             html_template_string=None,
             reply_to=None,
             template_params={}):
        """
        Send email using configured smtp settings and provided templates.

        The sender will use `text_template_string` and `html_template_string`
        if provided, instead of looking up the template provider.
        """

        if self.smtp_settings.host is None:
            logger.error('Mail server is not configured. Configure SMTP_HOST.')
            raise Exception('mail server is not configured')

        text_template = None
        html_template = None
        if text_template_string:
            text_template = StringTemplate(self.text_template_name,
                                           text_template_string)
            html_template = StringTemplate(self.html_template_name,
                                           html_template_string)
        else:
            text_template = self.fallback_text_template
            html_template = self.fallback_html_template

        mailer = email_util.Mailer(
            smtp_host=self.smtp_settings.host,
            smtp_port=self.smtp_settings.port,
            smtp_mode=self.smtp_settings.mode,
            smtp_login=self.smtp_settings.login,
            smtp_password=self.smtp_settings.password,
        )
        mailer.send_mail(sender,
                         email,
                         subject,
                         text_template.render(**template_params),
                         html=html_template.render(**template_params),
                         reply_to=reply_to)
