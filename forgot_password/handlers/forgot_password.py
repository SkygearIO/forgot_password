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
from datetime import datetime

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.utils.db import conn

from .template import Template
from .util import email as email_util
from .util import user as user_util

logger = logging.getLogger(__name__)


def add_templates(template_provider, settings):
    template_provider.add_template(
        Template('reset_email_text', 'forgot_password_email.txt',
                 download_url=settings.email_text_url))
    template_provider.add_template(
        Template('reset_email_html', 'forgot_password_email.html',
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

            text = template_provider.\
                get_template('reset_email_text').\
                render(**template_params)
            html = template_provider.\
                get_template('reset_email_html').\
                render(**template_params)

            sender = settings.sender
            reply_to = settings.reply_to
            subject = settings.subject

            try:
                mailer = email_util.Mailer(
                    smtp_host=smtp_settings.host,
                    smtp_port=smtp_settings.port,
                    smtp_mode=smtp_settings.mode,
                    smtp_login=smtp_settings.login,
                    smtp_password=smtp_settings.password,
                )
                mailer.send_mail(sender, user.email, subject, text,
                                 html=html, reply_to=reply_to)
                logger.info('Successfully sent reset password email to user.')
            except Exception as ex:
                logger.exception('An error occurred sending reset password'
                                 ' email to user.')
                raise SkygearException(str(ex), skyerror.UnexpectedError)

            return {'status': 'OK'}
