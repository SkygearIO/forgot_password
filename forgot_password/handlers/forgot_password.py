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
from collections import namedtuple
from datetime import datetime

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.models import Record, RecordID
from skygear.utils.context import current_context
from skygear.utils.db import conn

from .template import FileTemplate, StringTemplate
from .util import email as email_util
from .util import user as user_util

logger = logging.getLogger(__name__)


def add_templates(template_provider, settings):
    template_provider.add_template(
        FileTemplate('reset_email_text', 'forgot_password_email.txt',
                     download_url=settings.email_text_url))
    template_provider.add_template(
        FileTemplate('reset_email_html', 'forgot_password_email.html',
                     download_url=settings.email_html_url,
                     required=False))
    return template_provider


def register_op(**kwargs):
    """
    Register lambda function handling forgot password request
    """
    template_provider = kwargs['template_provider']
    settings = kwargs['settings']
    smtp_settings = kwargs['smtp_settings']

    def send_mail(sender,
                  email,
                  subject,
                  text_template_string=None,
                  html_template_string=None,
                  reply_to=None,
                  template_params={}):

        text_template = None
        html_template = None
        if text_template_string:
            text_template = StringTemplate('reset_email_text',
                                           text_template_string)
            html_template = StringTemplate('reset_email_html',
                                           html_template_string)
        else:
            text_template = template_provider.get_template('reset_email_text')
            html_template = template_provider.get_template('reset_email_html')

        try:
            mailer = email_util.Mailer(
                smtp_host=smtp_settings.host,
                smtp_port=smtp_settings.port,
                smtp_mode=smtp_settings.mode,
                smtp_login=smtp_settings.login,
                smtp_password=smtp_settings.password,
            )
            mailer.send_mail(sender,
                             email,
                             subject,
                             text_template.render(**template_params),
                             html=html_template.render(**template_params),
                             reply_to=reply_to)
        except Exception as ex:
            logger.exception('An error occurred sending reset password'
                             ' email to user.')
            raise SkygearException(str(ex), skyerror.UnexpectedError)

    @skygear.op('user:forgot-password')
    def forgot_password(email):
        """
        Lambda function to handle forgot password request.
        """
        if smtp_settings.host is None:
            logger.error('Mail server is not configured. Configure SMTP_HOST.')
            raise SkygearException(
                'mail server is not configured',
                skyerror.UnexpectedError
            )

        if email is None:
            raise SkygearException('email must be set',
                                   skyerror.InvalidArgument)

        with conn() as c:
            user = user_util.get_user_from_email(c, email)
            if not user:
                if not settings.secure_match:
                    return {'status': 'OK'}
                raise SkygearException('user_id must be set',
                                       skyerror.InvalidArgument)
            if not user.email:
                raise SkygearException('email must be set',
                                       skyerror.InvalidArgument)

            user_record = user_util.get_user_record(c, user.id)
            expire_at = round(datetime.utcnow().timestamp()) + \
                settings.reset_url_lifetime
            code = user_util.generate_code(user, expire_at)

            url_prefix = settings.url_prefix
            if url_prefix.endswith('/'):
                url_prefix = url_prefix[:-1]

            link = '{0}/reset-password?code={1}&user_id={2}&expire_at={3}'\
                .format(url_prefix, code, user.id, expire_at)

            template_params = {
                'appname': settings.app_name,
                'link': link,
                'url_prefix': url_prefix,
                'email': user.email,
                'user_id': user.id,
                'code': code,
                'user': user,
                'user_record': user_record,
            }

            send_mail(settings.sender,
                      user.email,
                      settings.subject,
                      reply_to=settings.reply_to,
                      template_params=template_params)

            return {'status': 'OK'}

    @skygear.op('user:forgot-password:test', key_required=True)
    def test_forgot_password_email(email,
                                   text_template=None,
                                   html_template=None):
        access_key_type = current_context().get('access_key_type')
        if not access_key_type or access_key_type != 'master':
            raise SkygearException(
                'master key is required',
                skyerror.AccessKeyNotAccepted
            )

        url_prefix = settings.url_prefix
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]

        dummy_user = namedtuple('User', ['id', 'email'])(
            'dummy-id',
            'dummy-user@example.com')

        dummy_record_id = RecordID('user', 'dummy-id')
        dummy_record = Record(dummy_record_id, dummy_record_id.key, None)

        template_params = {
            'appname': settings.app_name,
            'code': 'dummy-reset-code',
            'url_prefix': url_prefix,
            'link': '{}/example-reset-password-link'.format(url_prefix),
            'user_record': dummy_record,
            'user': dummy_user,
            'email': dummy_user.email,
            'user_id': dummy_user.id
        }

        send_mail(settings.sender,
                  email,
                  settings.subject,
                  reply_to=settings.reply_to,
                  text_template_string=text_template,
                  html_template_string=html_template,
                  template_params=template_params)

        return {'status': 'OK'}
