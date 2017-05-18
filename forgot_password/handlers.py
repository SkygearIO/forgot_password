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
from skygear.utils.db import conn

from .template import Template, TemplateProvider
from .util import email as email_util
from .util import user as user_util

logger = logging.getLogger(__name__)


class IllegalArgumentError(ValueError):
    pass


ResetPasswordRequestParams = namedtuple(
    'ResetPasswordRequestParams',
    ['code', 'user_id', 'expire_at', 'user', 'user_record'])


def build_template_provider(settings, notification_email_settings):
    return TemplateProvider(
        Template('reset_email_text', 'forgot_password_email.txt',
                 download_url=settings.email_text_url),
        Template('reset_email_html', 'forgot_password_email.html',
                 download_url=settings.email_html_url,
                 required=False),
        Template('reset_password_form', 'reset_password.html',
                 download_url=settings.reset_html_url),
        Template('reset_password_success', 'reset_password_success.html',
                 download_url=settings.reset_success_html_url),
        Template('reset_password_error', 'reset_password_error.html',
                 download_url=settings.reset_error_html_url),
        Template('notification_email_text', 'notification_email.txt',
                 download_url=notification_email_settings.text_url),
        Template('notification_email_html', 'notification_email.html',
                 download_url=notification_email_settings.html_url,
                 required=False))


def register_forgot_password_op(template_provider,
                                settings,
                                smtp_settings,
                                notification_email_settings):
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


def register_reset_password_op(template_provider,
                               settings,
                               smtp_settings,
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


def reset_password_response_form(template_provider, **kwargs):
    """
    A shorthand for returning the reset password form as a response.
    """
    body = template_provider.\
        get_template('reset_password_form').\
        render(**kwargs)
    return skygear.Response(body, content_type='text/html')


def send_notification_email(template_provider,
                            user,
                            user_record,
                            settings,
                            smtp_settings,
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

        text = template_provider.\
            get_template('notification_email_text').\
            render(**email_params)
        html = template_provider.\
            get_template('notification_email_html').\
            render(**email_params)

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


def validate_reset_password_request_password_params(request):
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


def response_reset_password_url_error(template_provider, settings, **kwargs):
    if settings.error_redirect:
        return redirect_response(settings.error_redirect)
    body = template_provider.\
        get_template('reset_password_error').\
        render(error='Invalid URL')
    return skygear.Response(body, status=400, content_type='text/html')


def response_reset_password_error(template_provider, settings, **kwargs):
    if settings.error_redirect:
        return redirect_response(settings.error_redirect)
    return reset_password_response_form(template_provider,
                                        **kwargs)


def register_reset_password_handler(template_provider,
                                    settings,
                                    smtp_settings,
                                    notification_email_settings):
    """
    Register HTTP handler for reset password request
    """
    @skygear.handler('reset-password', method=['GET', 'POST'])
    def reset_password_form_handler(request):
        """
        A handler for reset password requests.
        """
        with conn() as c:
            try:
                params = validate_reset_password_request_parameters(c, request)
            except IllegalArgumentError:
                return response_reset_password_url_error(template_provider,
                                                         settings)

            template_params = {
                'user': params.user,
                'user_record': params.user_record,
                'code': params.code,
                'user_id': params.user_id,
                'expire_at': params.expire_at,
            }

            if request.method != 'POST':
                return reset_password_response_form(template_provider,
                                                    **template_params)

            # Handle form submission
            try:
                password = \
                    validate_reset_password_request_password_params(request)
            except IllegalArgumentError as ex:
                return response_reset_password_error(template_provider,
                                                     settings,
                                                     error=str(ex),
                                                     **template_params)

            user_util.set_new_password(c, params.user.id, password)
            logger.info('Successfully reset password for user.')

            # send notification email
            if notification_email_settings.enable:
                send_notification_email(template_provider,
                                        params.user,
                                        params.user_record,
                                        settings,
                                        smtp_settings,
                                        notification_email_settings)

            if settings.success_redirect:
                return redirect_response(settings.success_redirect)

            body = template_provider.\
                get_template('reset_password_success').\
                render()
            return skygear.Response(body, content_type='text/html')


def register_handlers(settings, smtp_settings, notification_email_settings):
    template_provider = build_template_provider(settings,
                                                notification_email_settings)
    register_forgot_password_op(template_provider,
                                settings,
                                smtp_settings,
                                notification_email_settings)
    register_reset_password_op(template_provider,
                               settings,
                               smtp_settings,
                               notification_email_settings)
    register_reset_password_handler(template_provider,
                                    settings,
                                    smtp_settings,
                                    notification_email_settings)
