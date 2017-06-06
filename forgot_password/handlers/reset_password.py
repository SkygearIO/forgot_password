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

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.utils.db import conn

from .template import Template
from .util import user as user_util

logger = logging.getLogger(__name__)


class IllegalArgumentError(ValueError):
    pass


ResetPasswordRequestParams = namedtuple(
    'ResetPasswordRequestParams',
    ['code', 'user_id', 'expire_at', 'user', 'user_record'])


def redirect_response(url):
    """
    A shorthand for returning a http redirect response.
    """
    return skygear.Response(status=302, headers=[('Location', url)])


def response_form(template_provider, **kwargs):
    """
    A shorthand for returning the reset password form as a response.
    """
    body = template_provider.\
        get_template('reset_password_form').\
        render(**kwargs)
    return skygear.Response(body, content_type='text/html')


def validate_request_parameters(db_connection, request):
    """
    Validates reset password request parameters.
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


def validate_request_password_params(request):
    """
    Validate of reset password request password parameters.
    """
    password = request.values.get('password')
    password_confirm = request.values.get('confirm')

    if not password:
        raise IllegalArgumentError('password cannot be empty')

    if password != password_confirm:
        raise IllegalArgumentError(
            'confirm password does not match the password')

    return password


def response_url_error(template_provider, settings, **kwargs):
    if settings.error_redirect:
        return redirect_response(settings.error_redirect)
    body = template_provider.\
        get_template('reset_password_error').\
        render(error='Invalid URL')
    return skygear.Response(body, status=400, content_type='text/html')


def response_error(template_provider, settings, **kwargs):
    if settings.error_redirect:
        return redirect_response(settings.error_redirect)
    return response_form(template_provider, **kwargs)


def add_templates(template_provider, settings):
    template_provider.add_template(
        Template('reset_password_form', 'reset_password.html',
                 download_url=settings.reset_html_url))
    template_provider.add_template(
        Template('reset_password_success', 'reset_password_success.html',
                 download_url=settings.reset_success_html_url))
    template_provider.add_template(
        Template('reset_password_error', 'reset_password_error.html',
                 download_url=settings.reset_error_html_url))
    return template_provider


def register_op(**kwargs):
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

            return {'status': 'OK'}


def register_handlers(**kwargs):
    """
    Register HTTP handler for reset password request
    """
    template_provider = kwargs['template_provider']
    settings = kwargs['settings']

    @skygear.handler('reset-password', method=['GET', 'POST'])
    def reset_password_form_handler(request):
        """
        A handler for reset password requests.
        """
        with conn() as c:
            try:
                params = validate_request_parameters(c, request)
            except IllegalArgumentError:
                return response_url_error(template_provider, settings)

            template_params = {
                'user': params.user,
                'user_record': params.user_record,
                'code': params.code,
                'user_id': params.user_id,
                'expire_at': params.expire_at,
            }

            if request.method != 'POST':
                return response_form(template_provider, **template_params)

            # Handle form submission
            try:
                password = validate_request_password_params(request)
            except IllegalArgumentError as ex:
                return response_error(template_provider,
                                      settings,
                                      error=str(ex),
                                      **template_params)

            user_util.set_new_password(c, params.user.id, password)
            logger.info('Successfully reset password for user.')

            if settings.success_redirect:
                return redirect_response(settings.success_redirect)

            body = template_provider.\
                get_template('reset_password_success').\
                render()
            return skygear.Response(body, content_type='text/html')
