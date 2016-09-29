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

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.settings import settings
from skygear.utils.db import conn

from . import options  # noqa Register the options to skygear settings on import
from . import template
from .util import email as emailutil
from .util import user as userutil


forgetoptions = settings.forgot_password
logger = logging.getLogger(__name__)


def mail_is_configured():
    """
    Returns true if mail is configured
    """
    return bool(forgetoptions.smtp_host)


def forgot_password(email):
    """
    Lambda function to handle forgot password request.
    """
    if not mail_is_configured():
        logger.error('Mail server is not configured. Configure SMTP_HOST.')
        raise SkygearException('mail server is not configured',
                               skyerror.UnexpectedError)

    if email is None:
        raise SkygearException('email is not found',
                               skyerror.ResourceNotFound)

    with conn() as c:
        user = userutil.get_user_from_email(c, email)
        if not user:
            logger.debug('Unable to find user_id')
            raise SkygearException('user_id is not found',
                                   skyerror.ResourceNotFound)
        if not user.email:
            logger.debug('User does not have email address. This user cannot '
                         'reset password.')
            raise SkygearException('email is not found',
                                   skyerror.ResourceNotFound)

        logger.debug('Found user with email address.')

        user_record = userutil.get_user_record(c, user.id)
        code = userutil.generate_code(user)
        url_prefix = forgetoptions.url_prefix
        link = '{0}/reset-password?code={1}&user_id={2}'.format(
            url_prefix, code, user.id)

        template_params = {
            'appname': forgetoptions.appname,
            'link': link,
            'url_prefix': url_prefix,
            'email': user.email,
            'user_id': user.id,
            'code': code,
            'user': user,
            'user_record': user_record,
        }

        text = template.reset_email_text(**template_params)
        if text:
            logger.debug('Generated plain text reset password email.')

        html = template.reset_email_html(**template_params)
        if html:
            logger.debug('Generated html reset password email.')

        sender = forgetoptions.sender
        subject = forgetoptions.subject

        try:
            logger.debug('About to send email to user.')
            mailer = emailutil.Mailer(
                smtp_host=forgetoptions.smtp_host,
                smtp_port=forgetoptions.smtp_port,
                smtp_mode=forgetoptions.smtp_mode,
                smtp_login=forgetoptions.smtp_login,
                smtp_password=forgetoptions.smtp_password,
            )
            mailer.send_mail(sender, email, subject, text, html=html)
            logger.info('Successfully sent reset password email to user.')
        except Exception as ex:
            logger.exception('An error occurred sending reset password email '
                             'to user.')
            raise SkygearException(str(ex), skyerror.UnexpectedError)
        return {'status': 'OK'}


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
            logger.debug('User ID is not found or the code is not valid.')
            raise SkygearException('user_id is not found or code invalid',
                                   skyerror.ResourceNotFound)

        if not user.email:
            raise SkygearException('email is not found',
                                   skyerror.ResourceNotFound)

        logger.debug('Found user and the verification code is valid.')

        userutil.set_new_password(c, user.id, new_password)
        logger.info('Successfully reset password for user.')
        return {'status': 'OK'}


def reset_password_response(**kwargs):
    """
    A shorthand for returning the reset password form as a response.
    """
    body = template.reset_password_form(**kwargs)
    return skygear.Response(body, content_type='text/html')


def reset_password_handler(request):
    """
    A handler for handling reset password request.
    """
    code = request.values.get('code')
    user_id = request.values.get('user_id')

    with conn() as c:
        user = userutil.get_user_and_validate_code(c, user_id, code)
        if not user:
            logger.debug('User ID is not found or the code is not valid.')
            error_msg = 'User not found or code is invalid.'
            body = template.reset_password_error(error=error_msg)
            return skygear.Response(body, content_type='text/html')
        user_record = userutil.get_user_record(c, user.id)

    logger.debug('Found user and the verification code is valid.')

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


def init():
    skygear.op('user:forgot-password')(forgot_password)
    skygear.op('user:reset-password')(reset_password)
    skygear.handler('reset-password')(reset_password_handler)


if forgetoptions.enable:
    init()
