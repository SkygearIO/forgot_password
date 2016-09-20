import logging
import os

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.options import options as skyoptions
from skygear.utils.db import conn

from . import template
from .util import email as emailutil
from .util import user as userutil


logger = logging.getLogger(__name__)


@skygear.op('user:forgot-password')
def forgot_password(email):
    """
    Lambda function to handle forgot password request.
    """
    if not emailutil.mail_is_configured():
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
        appname = os.getenv('FORGOT_PASSWORD_APPNAME', skyoptions.appname)
        url_prefix = os.getenv('FORGOT_PASSWORD_URL_PREFIX',
            os.getenv('URL_PREFIX', skyoptions.skygear_endpoint))  # noqa
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        link = '{0}/reset-password?code={1}&user_id={2}'.format(
            url_prefix, code, user.id)

        template_params = {
            'appname': appname,
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

        sender = os.getenv('FORGOT_PASSWORD_SENDER', 'no-reply@skygeario.com')
        subject = os.getenv('FORGOT_PASSWORD_SUBJECT',
                            'Reset password instructions')

        try:
            logger.debug('About to send email to user.')
            emailutil.send_mail(sender, email, subject, text, html=html)
            logger.info('Successfully sent reset password email to user.')
        except Exception as ex:
            logger.exception('An error occurred sending reset password email '
                             'to user.')
            raise SkygearException(str(ex), skyerror.UnexpectedError)
        return {'status': 'OK'}


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
