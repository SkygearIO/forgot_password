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
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import HTTPError

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.utils.db import conn

from . import template
from .util import email as emailutil
from .util import user as userutil


logger = logging.getLogger(__name__)


def register_forgot_password_lifecycle_event_handler(settings):
    """
    Register lifecycle event handler for forgot password plugin
    """
    def download_template(url, name):
        path_prefix = 'templates/forgot_password'
        path = '/'.join([path_prefix, name])

        Path(path_prefix).mkdir(parents=True, exist_ok=True)
        logger.info('Downloading {} from {}'.format(path, url))

        try:
            urlretrieve(url, path)
        except HTTPError as e:
            raise Exception('Failed to download {}: {}'.format(name, e.reason))

    @skygear.event("before-plugins-ready")
    def download_templates(config):
        if settings.email_text_url:
            download_template(settings.email_text_url,
                              'forgot_password_email.txt')

        if settings.email_html_url:
            download_template(settings.email_html_url,
                              'forgot_password_email.html')

        if settings.reset_html_url:
            download_template(settings.reset_html_url, 'reset_password.html')

        if settings.reset_success_html_url:
            download_template(settings.reset_success_html_url,
                              'reset_password_success.html')

        if settings.reset_error_html_url:
            download_template(settings.reset_error_html_url,
                              'reset_password_error.html')

        if settings.welcome_email_text_url:
            download_template(settings.welcome_email_text_url,
                              'welcome_email.txt')

        if settings.welcome_email_html_url:
            download_template(settings.welcome_email_html_url,
                              'welcome_email.html')


def register_forgot_password_op(settings, smtp_settings):
    """
    Register lambda function handling forgot password request
    """
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
            raise SkygearException('email is not found',
                                   skyerror.ResourceNotFound)

        with conn() as c:
            user = userutil.get_user_from_email(c, email)
            if not user:
                if not settings.secure_match:
                    return {'status': 'OK'}
                raise SkygearException('user_id is not found',
                                       skyerror.ResourceNotFound)
            if not user.email:
                raise SkygearException('email is not found',
                                       skyerror.ResourceNotFound)

            user_record = userutil.get_user_record(c, user.id)
            code = userutil.generate_code(user)

            url_prefix = settings.url_prefix
            if url_prefix.endswith('/'):
                url_prefix = url_prefix[:-1]

            link = '{0}/reset-password?code={1}&user_id={2}'.format(
                url_prefix, code, user.id)

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

            text = template.reset_email_text(**template_params)
            html = template.reset_email_html(**template_params)

            sender = settings.sender
            subject = settings.subject

            try:
                mailer = emailutil.Mailer(
                    smtp_host=smtp_settings.host,
                    smtp_port=smtp_settings.port,
                    smtp_mode=smtp_settings.mode,
                    smtp_login=smtp_settings.login,
                    smtp_password=smtp_settings.password,
                )
                mailer.send_mail(sender, user.email, subject, text, html=html)
                logger.info('Successfully sent reset password email to user.')
            except Exception as ex:
                logger.exception('An error occurred sending reset password'
                                 ' email to user.')
                raise SkygearException(str(ex), skyerror.UnexpectedError)

            return {'status': 'OK'}


def register_reset_password_op(settings):
    """
    Register lambda function handling reset password request
    """
    @skygear.op('user:reset-password')
    def reset_password(user_id, code, new_password):
        """
        Lambda function to handle reset password request.
        """
        if not user_id:
            raise SkygearException('user_id is not found',
                                   skyerror.ResourceNotFound)
        if not code:
            raise SkygearException('code is not found',
                                   skyerror.ResourceNotFound)

        with conn() as c:
            user = userutil.get_user_and_validate_code(c, user_id, code)
            if not user:
                raise SkygearException('user_id is not found or code invalid',
                                       skyerror.ResourceNotFound)

            if not user.email:
                raise SkygearException('email is not found',
                                       skyerror.ResourceNotFound)

            userutil.set_new_password(c, user.id, new_password)
            logger.info('Successfully reset password for user.')

            return {'status': 'OK'}


def reset_password_response(**kwargs):
    """
    A shorthand for returning the reset password form as a response.
    """
    body = template.reset_password_form(**kwargs)
    return skygear.Response(body, content_type='text/html')


def register_reset_password_handler(setting):
    """
    Register HTTP handler for reset password request
    """
    @skygear.handler('reset-password')
    def reset_password_handler(request):
        """
        A handler for handling reset password request.
        """
        code = request.values.get('code')
        user_id = request.values.get('user_id')

        with conn() as c:
            user = userutil.get_user_and_validate_code(c, user_id, code)
            if not user:
                error_msg = 'User not found or code is invalid.'
                body = template.reset_password_error(error=error_msg)
                return skygear.Response(body, content_type='text/html')
            user_record = userutil.get_user_record(c, user.id)

        template_params = {
            'user': user,
            'user_record': user_record,
            'code': code,
            'user_id': user_id,
        }

        if request.method == 'POST':
            password = request.values.get('password')
            if not password:
                return reset_password_response(
                    error='Password cannot be empty.',
                    **template_params
                )

            if password != request.values.get('confirm'):
                return reset_password_response(
                    error='Confirm password does not match new password.',
                    **template_params
                )

            with conn() as c:
                userutil.set_new_password(c, user.id, password)
                logger.info('Successfully reset password for user.')

                body = template.reset_password_success()
                return skygear.Response(body, content_type='text/html')

        return reset_password_response(**template_params)


def register_handlers(settings, smtp_settings):
    register_forgot_password_lifecycle_event_handler(settings)
    register_forgot_password_op(settings, smtp_settings)
    register_reset_password_op(settings)
    register_reset_password_handler(settings)
