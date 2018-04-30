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


from skygear.options import options as skyoptions
from skygear.settings import SettingsParser

from .providers import get_provider_class


def get_settings_parser():
    parser = SettingsParser('FORGOT_PASSWORD')

    # TODO(cheungpat): py-skygear will have support for specifying
    # a callable in default param. When that happens, the app name
    # and endpoint should be specified via a function.
    # parser.add_setting('app_name', default=skyoptions.appname)
    # parser.add_setting('url_prefix', default=skyoptions.skygear_endpoint)
    parser.add_setting('app_name',
                       default=getattr(skyoptions, 'appname', None),
                       required=False)
    parser.add_setting('url_prefix',
                       default=getattr(skyoptions, 'skygear_endpoint', None),
                       required=False)
    parser.add_setting(
        'secure_match',
        atype=bool,
        required=False,
        resolve=False,
        default=False
    )
    parser.add_setting(
        'sender_name',
        resolve=False,
        required=False,
        default=''
    )
    parser.add_setting(
        'sender',
        resolve=False,
        default='no-reply@skygeario.com'
    )
    parser.add_setting(
        'subject',
        resolve=False,
        default='Reset password instructions'
    )
    parser.add_setting(
        'reply_to_name',
        resolve=False,
        required=False,
        default=''
    )
    parser.add_setting('reply_to', resolve=False, required=False)
    parser.add_setting(
        'reset_url_lifetime',
        atype=int,
        resolve=False,
        required=False,
        default=43200
    )
    parser.add_setting('success_redirect', resolve=False, required=False)
    parser.add_setting('error_redirect', resolve=False, required=False)
    parser.add_setting('email_text_url', resolve=False, required=False)
    parser.add_setting('email_html_url', resolve=False, required=False)
    parser.add_setting('reset_html_url', resolve=False, required=False)
    parser.add_setting('reset_success_html_url', resolve=False, required=False)
    parser.add_setting('reset_error_html_url', resolve=False, required=False)

    return parser


def get_smtp_settings_parser():
    parser = SettingsParser('SMTP')

    parser.add_setting('host', resolve=False, required=False)
    parser.add_setting('port', resolve=False, default=25, atype=int)
    parser.add_setting('mode', resolve=False, default='normal')
    parser.add_setting('login', resolve=False, default='')
    parser.add_setting('password', resolve=False, default='')

    return parser


def get_welcome_email_settings_parser():
    parser = SettingsParser('FORGOT_PASSWORD_WELCOME_EMAIL')

    parser.add_setting(
        'enable',
        atype=bool,
        resolve=False,
        required=False,
        default=False
    )
    parser.add_setting(
        'sender_name',
        resolve=False,
        required=False,
        default=''
    )
    parser.add_setting(
        'sender',
        resolve=False,
        default='no-reply@skygeario.com'
    )
    parser.add_setting(
        'subject',
        resolve=False,
        default='Welcome!'
    )
    parser.add_setting(
        'reply_to_name',
        resolve=False,
        required=False,
        default=''
    )
    parser.add_setting('reply_to', resolve=False, required=False)
    parser.add_setting('text_url', resolve=False, required=False)
    parser.add_setting('html_url', resolve=False, required=False)

    return parser


def get_verify_settings_keys_type():
    """
    Returns a type function for parsing verify keys settings.

    This function returns a function that can be used by parser for converting
    a set of verify keys (in array of strings) into settings mapping.

    For example, if `VERIFY_KEYS=phone,email`, the parser will call type
    function with `phone,email` as value. The type function will create
    separate parsers according to how many keys are defined. In this
    example, `VERIFY_KEYS_PHONE_*` and `VERIFY_KEYS_EMAIL_*` environment
    variables are parsed into settings.
    """
    def fn(value):
        result = {}

        keys = value.split(',') if isinstance(value, str) else []
        for key in keys:
            parser = get_verify_settings_parser_for_key(key)
            result[key] = parser.parse_settings()
        return result
    return fn


def get_verify_settings_provider_type(key):
    """
    Returns a type function for parsing provider settings

    This function returns a function that can be used by parser for converting
    a provider name (in string) into settings mapping.

    For example, if `VERIFY_KEYS_EMAIL_PROVIDER=smtp`, the parser will call
    type function with `smtp` as value. The type function will create
    separate parsers according to the specified provider.
    """
    def fn(value):
        parser = get_verify_settings_parser_for_key_and_provider(key, value)
        ns = parser.parse_settings()
        setattr(ns, 'name', value)
        return ns
    return fn


def get_verify_settings_parser():
    """
    Returns a parser for parsing verify settings.
    """
    parser = SettingsParser('VERIFY')

    parser.add_setting(
        'keys',
        atype=get_verify_settings_keys_type(),
        resolve=False,
        required=False,
        default={}
    )
    parser.add_setting(
        'auto_update',
        atype=bool,
        resolve=False,
        required=False,
        default=False
    )
    parser.add_setting(
        'auto_send_signup',
        atype=bool,
        resolve=False,
        required=False,
        default=False
    )
    parser.add_setting(
        'auto_send_update',
        atype=bool,
        resolve=False,
        required=False,
        default=False
    )
    parser.add_setting(
        'required',
        atype=bool,
        resolve=False,
        required=False,
        default=False
    )
    parser.add_setting(
        'criteria',
        atype=str,
        resolve=False,
        required=False,
        default=None
    )
    parser.add_setting(
        'modify_schema',
        atype=bool,
        resolve=False,
        default=True
    )
    parser.add_setting(
        'modify_acl',
        atype=bool,
        resolve=False,
        default=True
    )
    parser.add_setting(
        'error_redirect',
        atype=str,
        resolve=False,
        required=False
    )
    parser.add_setting(
        'error_html_url',
        atype=str,
        resolve=False,
        required=False
    )
    return parser


def get_verify_settings_parser_for_key(key):
    """
    Returns a parser for parsing verify settings for a specified key.
    """
    parser = SettingsParser('VERIFY_KEYS_{}'.format(key.upper()))

    parser.add_setting(
        'code_format',
        atype=str,
        resolve=False,
        required=False,
        default='numeric'
    )
    parser.add_setting(
        'expiry',
        atype=int,
        resolve=False,
        required=False,
        default=60*60*24  # 1 day
    )
    parser.add_setting(
        'success_redirect',
        atype=str,
        resolve=False,
        required=False
    )
    parser.add_setting(
        'error_redirect',
        atype=str,
        resolve=False,
        required=False
    )
    parser.add_setting(
        'success_html_url',
        atype=str,
        resolve=False,
        required=False
    )
    parser.add_setting(
        'error_html_url',
        atype=str,
        resolve=False,
        required=False
    )
    parser.add_setting(
        'provider',
        atype=get_verify_settings_provider_type(key),
        resolve=False,
        required=True
    )

    return parser


def get_verify_settings_parser_for_key_and_provider(key, provider):
    """
    Returns a parser for parsing verify settings for a specified key and
    provider.
    """
    parser = SettingsParser(
        'VERIFY_KEYS_{}_PROVIDER'.format(key.upper(), provider.upper())
    )
    provider_class = get_provider_class(provider)
    provider_class.configure_parser(key, parser)
    return parser
