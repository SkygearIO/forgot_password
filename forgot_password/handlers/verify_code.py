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
import datetime
import logging
from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.options import options as skyoptions
from skygear.utils.context import current_user_id
from skygear.utils.db import conn

from ..providers import get_provider_class
from ..template import FileTemplate, TemplateProvider
from .util.schema import (schema_add_key_verified_acl,
                          schema_add_key_verified_flags)
from .util.user import fetch_user_record, get_user, save_user_record
from .util.verify_code import (add_verify_code, generate_code, get_verify_code,
                               set_code_consumed, verified_flag_name)

logger = logging.getLogger(__name__)


USER_VERIFIED_FLAG_NAME = 'is_verified'


def register(settings):  # noqa
    providers = {}
    templates = TemplateProvider()
    for record_key, key_settings in settings.keys.items():
        # Create verification provider.
        providers[record_key] = get_provider(key_settings.provider, record_key)

        # Create templates
        templates.add_template(
            FileTemplate('{}_success_html'.format(record_key),
                         'verify_success.html',
                         download_url=key_settings.success_html_url)
        )
        templates.add_template(
            FileTemplate('{}_error_html'.format(record_key),
                         'verify_error.html',
                         download_url=key_settings.error_html_url)
        )

    # Create the fallback error template
    templates.add_template(
        FileTemplate('error_html',
                     'verify_error.html',
                     download_url=settings.error_html_url)
    )

    @skygear.op('user:verify_code', user_required=True)
    def verify_code_lambda(code):
        """
        This lambda checks the user submitted code.
        """
        thelambda = VerifyCodeLambda(settings)
        return thelambda(current_user_id(), code)

    @skygear.op('user:verify_request', user_required=True)
    def verify_request_lambda(record_key):
        """
        This lambda allows client to request verification
        (i.e. send email or send SMS).
        """
        thelambda = VerifyRequestLambda(settings, providers)
        return thelambda(current_user_id(), record_key)

    @skygear.before_save('user', async=False)  # noqa: NOTE(cheungpat): W606
    def before_user_save_hook(record, original_record, db):
        """
        Checks the user record for data changes so that verified flag
        will be updated automatically upon record save.
        """
        record = update_flags(settings, record, original_record, db)
        return record

    @skygear.after_save('user', async=True)  # noqa: NOTE(cheungpat): W606
    def after_user_save_hook(record, original_record, db):
        """
        Performs action upon saving user record such as sending verifications.
        """
        send_signup_verification(settings, providers,
                                 record, original_record, db)
        send_update_verification(settings, providers,
                                 record, original_record, db)

    @skygear.handler('user:verify-code:form', method=['GET', 'POST'])
    def verify_code_handler(request):
        """
        HTML handler to allow verification through browser.
        """
        thehandler = VerifyCodeFormHandler(settings, providers, templates)
        return thehandler(request)

    @skygear.event('before-plugins-ready')
    def before_plugin_ready(*args, **kwargs):
        """
        Plugin event handler for updating schema and ACL before server is
        ready.
        """
        managed_flags = [verified_flag_name(k) for k in settings.keys.keys()]
        if settings.auto_update:
            managed_flags.append(USER_VERIFIED_FLAG_NAME)
        if settings.modify_schema:
            schema_add_key_verified_flags(managed_flags)
        if settings.modify_acl:
            schema_add_key_verified_acl(managed_flags)


def get_provider(provider_settings, key):
    """
    Convenient method for returning a provider.
    """
    klass = get_provider_class(provider_settings.name)
    return klass(key, provider_settings)


def should_user_be_verified(settings, user_record):
    """
    With a user record, determine if the user has become verified according
    to developer specified criteria.
    """
    verified_keys = set()
    for record_key in settings.keys.keys():
        if user_record.get(verified_flag_name(record_key), False):
            verified_keys.add(record_key)

    if settings.criteria == 'any':
        return len(verified_keys) > 0
    elif settings.criteria == 'all':
        return verified_keys == set(settings.keys.keys())
    else:
        criteria = settings.criteria.split(',')
        return verified_keys == set(criteria)


class VerifyCodeLambda:
    """
    This lambda handles the client submission for verification code.
    """
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, auth_id, code_str):
        with conn() as c:
            code = get_verify_code(c, auth_id, code_str)
            if not code:
                msg = 'the code `{}` is not valid ' \
                      'for user `{}`'.format(code_str, auth_id)
                raise SkygearException(msg, skyerror.InvalidArgument)

        user_record = fetch_user_record(auth_id)
        if not user_record:
            msg = 'user `{}` not found'.format(auth_id)
            raise SkygearException(msg, skyerror.ResourceNotFound)

        if user_record.get(code.record_key) != code.record_value:
            msg = 'the user data has since been modified, ' \
                'a new verification is required'
            raise SkygearException(msg, skyerror.InvalidArgument)

        expiry = self.settings.keys[code.record_key].expiry
        if expiry:
            expire_at = code.created_at + datetime.timedelta(seconds=expiry)
            if expire_at < datetime.datetime.now():
                msg = 'the code has expired'
                raise SkygearException(msg, skyerror.InvalidArgument)

        with conn() as c:
            set_code_consumed(c, code.id)

        user_record[verified_flag_name(code.record_key)] = True
        save_user_record(user_record)


class VerifyRequestLambda:
    """
    This lambda handles the client request for verification. Usually
    a email or SMS will be sent.
    """
    def __init__(self, settings, providers):
        self.settings = settings
        self.providers = providers

    def is_valid_record_key(self, record_key):
        return record_key not in self.settings.keys

    def get_code(self, record_key):
        return generate_code(self.settings.keys[record_key].code_format)

    def get_template_params(self, record_key, user, user_record, code_str):
        url_prefix = skyoptions.skygear_endpoint
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        link = '{0}/user/verify-code/form?code={1}&auth_id={2}'\
            .format(url_prefix, code_str, user.id)

        template_params = {
            'appname': skyoptions.appname,
            'link': link,
            'record_key': record_key,
            'record_value': user_record.get(record_key),
            'user_id': user.id,
            'code': code_str,
            'user': user,
            'user_record': user_record
        }
        return template_params

    def call_provider(self, record_key, user, user_record, code_str):
        """
        Call the provider, meaning sending verification.
        """
        provider = self.providers[record_key]
        template_params = self.get_template_params(
            record_key, user, user_record, code_str
        )
        value_to_verify = user_record.get(record_key)
        provider.send(value_to_verify, template_params)

    def __call__(self, auth_id, record_key):
        if self.is_valid_record_key(record_key):
            msg = 'record_key `{}` is not configured to verify'.format(
                record_key
            )
            raise SkygearException(msg, skyerror.InvalidArgument)

        with conn() as c:
            user = get_user(c, auth_id)
            if not user:
                msg = 'user `{}` not found'.format(auth_id)
                raise SkygearException(msg, skyerror.ResourceNotFound)

        user_record = fetch_user_record(auth_id)
        if not user_record:
            msg = 'user `{}` not found'.format(auth_id)
            raise SkygearException(msg, skyerror.ResourceNotFound)

        value_to_verify = user_record.get(record_key)
        if not value_to_verify:
            msg = 'there is nothing to verify for record_key `{}` ' \
                  'with auth_id `{}`'.format(record_key, auth_id)
            raise SkygearException(msg, skyerror.InvalidArgument)

        code_str = self.get_code(record_key)

        with conn() as c:
            add_verify_code(c, auth_id, record_key, value_to_verify,
                            code_str)

            logger.info('Added new verify code `{}` for user `{}`.'.format(
                code_str, auth_id
            ))
        self.call_provider(record_key, user, user_record, code_str)


def update_flags(settings, record, original_record, db):
    """
    Update the verified flag on user record.
    """
    for record_key in settings.keys.keys():
        changed = False
        if not original_record:
            changed = True
        elif original_record.get(record_key, None) != \
                record.get(record_key, None):
            changed = True

        if changed:
            record[verified_flag_name(record_key)] = False

    if settings.auto_update:
        is_verified = should_user_be_verified(settings, record)
        record[USER_VERIFIED_FLAG_NAME] = is_verified
    return record


def send_signup_verification(settings, providers, record, original_record, db):
    """
    Send sign up verification according to developer-specified settings.
    """
    if not settings.auto_send_signup and not settings.required:
        return

    if original_record:
        return

    for record_key in settings.keys.keys():
        if record.get(record_key, None):
            thelambda = VerifyRequestLambda(settings, providers)
            thelambda(record.id.key, record_key)


def send_update_verification(settings, providers, record, original_record, db):
    """
    Send update verification according to developer-specified settings.
    """
    if not settings.auto_send_update:
        return

    if not original_record:
        return

    def is_changed(x, y):
        return x.get(record_key, None) != y.get(record_key, None)

    thelambda = VerifyRequestLambda(settings, providers)
    for record_key in settings.keys.keys():
        if is_changed(record, original_record):
            thelambda(record.id.key, record_key)


def response_url_redirect(url, **kwargs):
    parsed_url = urlparse(url)

    query_list = parse_qsl(parsed_url.query)
    for key, value in kwargs.items():
        query_list.append((key, value))

    new_url = ParseResult(parsed_url.scheme,
                          parsed_url.netloc,
                          parsed_url.path,
                          parsed_url.params,
                          urlencode(query_list),
                          parsed_url.fragment)

    return skygear.Response(status=302,
                            headers=[('Location', new_url.geturl())])


class VerifyCodeFormHandler:
    """
    Handler for serving browser-based verify code submission.
    """
    def __init__(self, settings, providers, templates):
        self.settings = settings
        self.providers = providers
        self.templates = templates

    def get_success_template(self, record_key):
        template_name = '{}_success_html'.format(record_key)
        return self.templates.get_template(template_name)

    def get_error_template(self, record_key=None):
        if not record_key:
            return self.templates.get_template('error_html')
        template_name = '{}_error_html'.format(record_key)
        return self.templates.get_template(template_name)

    def response_redirect(url, **kwargs):
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in ['auth_id']
        }
        return response_url_redirect(url, **filtered_kwargs)

    def response_success(self, record_key, **kwargs):
        key_settings = self.settings.keys[record_key]
        if key_settings.success_redirect:
            return self.response_redirect(key_settings.success_redirect,
                                          **kwargs)

        body = self.get_success_template(record_key).render(**kwargs)
        return skygear.Response(body, content_type='text/html')

    def response_error(self, record_key=None, **kwargs):
        if record_key:
            key_settings = self.settings.keys[record_key]
            error_redirect = key_settings.error_redirect
            template = self.get_error_template(record_key)
        else:
            error_redirect = self.settings.error_redirect
            template = self.get_error_template()

        if error_redirect:
            return self.response_redirect(error_redirect, **kwargs)

        body = template.render(**kwargs)
        return skygear.Response(body, status=400, content_type='text/html')

    def __call__(self, request):
        auth_id = request.values.get('auth_id')
        code_str = request.values.get('code')

        code = None
        try:
            if not auth_id:
                raise Exception('missing auth_id')

            if not code_str:
                raise Exception('missing code_str')

            with conn() as c:
                code = get_verify_code(c, auth_id, code_str)
                if not code:
                    raise Exception('code not found')

            thelambda = VerifyCodeLambda(self.settings)
            thelambda(auth_id, code_str)
            return self.response_success(code.record_key)

        except Exception as ex:
            logger.exception('error occurred fixme')
            record_key = code.record_key if code else None
            return self.response_error(record_key=record_key, error=ex)
