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
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlretrieve

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.utils.db import conn

from . import template
from .util import email as emailutil
from .util import user as userutil

logger = logging.getLogger(__name__)


def download_template(url, name):
    path_prefix = 'templates/forgot_password'
    path = '/'.join([path_prefix, name])

    Path(path_prefix).mkdir(parents=True, exist_ok=True)
    logger.info('Downloading {} from {}'.format(path, url))

    try:
        urlretrieve(url, path)
    except HTTPError as e:
        raise Exception('Failed to download {}: {}'.format(name, e.reason))


def register_forgot_password_lifecycle_event_handler(settings,
                                                     welcome_email_settings):
    """
    Register lifecycle event handler for forgot password plugin
    """
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

        if welcome_email_settings.text_url:
            download_template(welcome_email_settings.text_url,
                              'welcome_email.txt')

        if welcome_email_settings.html_url:
            download_template(welcome_email_settings.html_url,
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
            expire_at = round(datetime.utcnow().timestamp()) + \
                        settings.reset_url_lifetime
            code = userutil.generate_code(user, expire_at)

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

            text = template.reset_email_text(**template_params)
            html = template.reset_email_html(**template_params)

            sender = settings.sender
            reply_to = settings.reply_to
            subject = settings.subject

            try:
                mailer = emailutil.Mailer(
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


def register_reset_password_op(settings, smtp_settings, welcome_email_settings):
    """
    Register lambda function handling reset password request
    """
    @skygear.op('user:reset-password')
    def reset_password(user_id, code, expire_at, new_password):
        """
        Lambda function to handle reset password request.
        """
        if not user_id:
            raise SkygearException('user_id is not found',
                                   skyerror.ResourceNotFound)
        if not code:
            raise SkygearException('code is not found',
                                   skyerror.ResourceNotFound)

        if not expire_at:
            raise SkygearException('expire_at is not found',
                                   skyerror.ResourceNotFound)

        with conn() as c:
            user = userutil.get_user_and_validate_code(c,
                                                       user_id,
                                                       code,
                                                       expire_at)
            if not user:
                raise SkygearException('user_id is not found or code invalid',
                                       skyerror.ResourceNotFound)

            if not user.email:
                raise SkygearException('email is not found',
                                       skyerror.ResourceNotFound)

            userutil.set_new_password(c, user.id, new_password)
            logger.info('Successfully reset password for user.')

            user_record = userutil.get_user_record(c, user.id)

            # send welcome email
            if welcome_email_settings.enable:
                send_welcome_email(user, user_record, settings,
                                   smtp_settings,
                                   welcome_email_settings)

            return {'status': 'OK'}


def redirect_response(url):
    """
    A shorthand for returning a http redirect response.
    """
    return skygear.Response(status=302, headers=[('Location', url)])


def reset_password_response_form(**kwargs):
    """
    A shorthand for returning the reset password form as a response.
    """
    body = template.reset_password_form(**kwargs)
    return skygear.Response(body, content_type='text/html')


def reset_password_success_response():
    """
    A shorthand for returning the reset password success response.
    """
    body = template.reset_password_success()
    return skygear.Response(body, content_type='text/html')


def send_welcome_email(user, user_record, settings, smtp_settings,
                       welcome_email_settings):
    if not smtp_settings.host:
        logger.error('Mail server is not configured. '
                     'Ignore sending welcome email')
    else:
        url_prefix = settings.url_prefix
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]

        email_params = {
            'appname': settings.app_name,
            'url_prefix': url_prefix,
            'email': user.email,
            'user_id': user.id,
            'user': user,
            'user_record': user_record,
        }

        text = template.welcome_email_text(**email_params)
        html = template.welcome_email_html(**email_params)

        sender = welcome_email_settings.sender
        reply_to = welcome_email_settings.reply_to
        subject = welcome_email_settings.subject

        try:
            mailer = emailutil.Mailer(
                smtp_host=smtp_settings.host,
                smtp_port=smtp_settings.port,
                smtp_mode=smtp_settings.mode,
                smtp_login=smtp_settings.login,
                smtp_password=smtp_settings.password,
            )
            mailer.send_mail(sender, user.email, subject, text,
                             html=html, reply_to=reply_to)
            logger.info('Successfully sent welcome email '
                        'to user.')
        except Exception as ex:
            logger.error('An error occurred sending welcome '
                         'email to user: {}'.format(str(ex)))


def register_reset_password_handler(settings, smtp_settings,
                                    welcome_email_settings):
    """
    Register HTTP handler for reset password request
    """
    @skygear.handler('reset-password')
    def reset_password_handler(request):
        """
        A handler for handling reset password request.
        """
        if settings.error_redirect:
            url_error_response = redirect_response(settings.error_redirect)
        else:
            url_error_response = skygear.Response(
                template.reset_password_error(error='Invalid URL'),
                content_type='text/html')

        try:
            expire_at = int(request.values.get('expire_at'))
        except:
            return url_error_response

        code = request.values.get('code')
        user_id = request.values.get('user_id')

        with conn() as c:
            user = userutil.get_user_and_validate_code(c,
                                                       user_id,
                                                       code,
                                                       expire_at)

            if not user:
                return url_error_response

            user_record = userutil.get_user_record(c, user.id)

        template_params = {
            'user': user,
            'user_record': user_record,
            'code': code,
            'user_id': user_id,
            'expire_at': expire_at,
        }

        if request.method == 'POST':
            password = request.values.get('password')
            if not password:
                if settings.error_redirect:
                    return redirect_response(settings.error_redirect)
                return reset_password_response_form(
                    error='Password cannot be empty.',
                    **template_params)

            if password != request.values.get('confirm'):
                if settings.error_redirect:
                    return redirect_response(settings.error_redirect)
                return reset_password_response_form(
                    error='Confirm password does not match new password.',
                    **template_params)

            with conn() as c:
                userutil.set_new_password(c, user.id, password)
                logger.info('Successfully reset password for user.')

                # send welcome email
                if welcome_email_settings.enable:
                    send_welcome_email(user, user_record, settings,
                                       smtp_settings,
                                       welcome_email_settings)

                if settings.success_redirect:
                    return redirect_response(settings.success_redirect)
                return reset_password_success_response()

        return reset_password_response_form(**template_params)


def register_handlers(settings, smtp_settings, welcome_email_settings):
    register_forgot_password_lifecycle_event_handler(settings,
                                                     welcome_email_settings)
    register_forgot_password_op(settings, smtp_settings)
    register_reset_password_op(settings, smtp_settings, welcome_email_settings)
    register_reset_password_handler(settings, smtp_settings,
                                    welcome_email_settings)
