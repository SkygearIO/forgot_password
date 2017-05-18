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
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlretrieve

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.utils.db import conn

from . import template
from .util import email as email_util
from .util import user as user_util

logger = logging.getLogger(__name__)


class IllegalArgumentError(ValueError):
    pass


ResetPasswordRequestParams = namedtuple(
    'ResetPasswordRequestParams',
    ['code', 'user_id', 'expire_at', 'user', 'user_record'])


def download_template(url, name):
    path_prefix = 'templates/forgot_password'
    path = '/'.join([path_prefix, name])

    Path(path_prefix).mkdir(parents=True, exist_ok=True)
    logger.info('Downloading {} from {}'.format(path, url))

    try:
        urlretrieve(url, path)
    except HTTPError as e:
        raise Exception('Failed to download {}: {}'.format(name, e.reason))


def register_forgot_password_lifecycle_event_handler(
        settings, notification_email_settings):

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

        if notification_email_settings.text_url:
            download_template(notification_email_settings.text_url,
                              'notification_email.txt')

        if notification_email_settings.html_url:
            download_template(notification_email_settings.html_url,
                              'notification_email.html')


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

            text = template.reset_email_text(**template_params)
            html = template.reset_email_html(**template_params)

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


def register_reset_password_op(settings, smtp_settings,
                               notification_email_settings):
    """
    Register lambda function handling reset password request
    """
    @skygear.op('user:reset-password')
    def reset_password(user_id, code, expire_at, new_password):
        """
        Lambda function to handle reset password request.
        """
        if not user_id:
            raise SkygearException('user_id must be set',
                                   skyerror.InvalidArgument)
        if not code:
            raise SkygearException('code must be set',
                                   skyerror.InvalidArgument)

        if not expire_at:
            raise SkygearException('expire_at must be set',
                                   skyerror.InvalidArgument)

        with conn() as c:
            user = user_util.get_user_and_validate_code(c,
                                                        user_id,
                                                        code,
                                                        expire_at)
            if not user:
                raise SkygearException('user_id is not found or code invalid',
                                       skyerror.ResourceNotFound)

            if not user.email:
                raise SkygearException('email must be set',
                                       skyerror.ResourceNotFound)

            user_util.set_new_password(c, user.id, new_password)
            logger.info('Successfully reset password for user.')

            user_record = user_util.get_user_record(c, user.id)

            # send notification email
            if notification_email_settings.enable:
                send_notification_email(user, user_record, settings,
                                        smtp_settings,
                                        notification_email_settings)

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


def reset_password_error_response():
    """
    A shorthand for returning the reset password error response.
    """
    body = template.reset_password_error(error='Invalid URL')
    return skygear.Response(body, status=400, content_type='text/html')


def send_notification_email(user, user_record, settings, smtp_settings,
                            notification_email_settings):
    if not smtp_settings.host:
        logger.error('Mail server is not configured. '
                     'Ignore sending notification email')
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

        text = template.notification_email_text(**email_params)
        html = template.notification_email_html(**email_params)

        sender = notification_email_settings.sender
        reply_to = notification_email_settings.reply_to
        subject = notification_email_settings.subject

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
            logger.info('Successfully sent notification email '
                        'to user.')
        except Exception as ex:
            logger.error('An error occurred sending notification '
                         'email to user: {}'.format(str(ex)))


def validate_reset_password_request_parameters(db_connection, request):
    """
    Validation of reset password request parameters
    """
    code = request.values.get('code')
    user_id = request.values.get('user_id')
    expire_at_arg = request.values.get('expire_at')

    if not code:
        raise IllegalArgumentError('code must be set')

    if not user_id:
        raise IllegalArgumentError('user_id must be set')

    if not expire_at_arg:
        raise IllegalArgumentError('expire_at must be set')

    try:
        expire_at = int(expire_at_arg)
    except ValueError:
        raise IllegalArgumentError('expire_at is malformed')

    user = user_util.get_user_and_validate_code(db_connection, user_id,
                                                code, expire_at)

    if not user:
        raise IllegalArgumentError('cannot find the specified user')

    if not user.email:
        raise IllegalArgumentError('the specified user does not have an email')

    user_record = user_util.get_user_record(db_connection, user.id)

    return ResetPasswordRequestParams(code=code, user_id=user_id,
                                      expire_at=expire_at,
                                      user=user, user_record=user_record)


def validate_reset_password_request_password_parameters(request):
    """
    Validation of reset password request password parameters
    """
    password = request.values.get('password')
    password_confirm = request.values.get('confirm')

    if not password:
        raise IllegalArgumentError('password cannot be empty')

    if password != password_confirm:
        raise IllegalArgumentError(
            'confirm password does not match the password')

    return password


def register_reset_password_handler(settings, smtp_settings,
                                    notification_email_settings):
    """
    Register HTTP handler for reset password request
    """
    @skygear.handler('reset-password', method=['GET', 'POST'])
    def reset_password_form_handler(request):
        """
        A handler for reset password requests.
        """
        if settings.error_redirect:
            response_url_error = response_reset_password_error = \
                lambda **kwargs: redirect_response(settings.error_redirect)
        else:
            response_url_error = reset_password_error_response
            response_reset_password_error = reset_password_response_form

        with conn() as c:
            try:
                params = validate_reset_password_request_parameters(c, request)
            except IllegalArgumentError:
                return response_url_error()

        template_params = {
            'user': params.user,
            'user_record': params.user_record,
            'code': params.code,
            'user_id': params.user_id,
            'expire_at': params.expire_at,
        }

        if request.method != 'POST':
            return reset_password_response_form(**template_params)

        # Handle form submission
        try:
            password = \
                validate_reset_password_request_password_parameters(request)
        except IllegalArgumentError as ex:
            return response_reset_password_error(error=str(ex),
                                                 **template_params)

        with conn() as c:
            user_util.set_new_password(c, params.user.id, password)
            logger.info('Successfully reset password for user.')

            # send notification email
            if notification_email_settings.enable:
                send_notification_email(params.user, params.user_record,
                                        settings,
                                        smtp_settings,
                                        notification_email_settings)

            if settings.success_redirect:
                return redirect_response(settings.success_redirect)

            body = template.reset_password_success()
            return skygear.Response(body, content_type='text/html')


def register_handlers(settings, smtp_settings, notification_email_settings):
    register_forgot_password_lifecycle_event_handler(
        settings, notification_email_settings)
    register_forgot_password_op(settings, smtp_settings)
    register_reset_password_op(settings, smtp_settings,
                               notification_email_settings)
    register_reset_password_handler(settings, smtp_settings,
                                    notification_email_settings)
