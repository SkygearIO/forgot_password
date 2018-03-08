# Copyright 2018 Oursky Ltd.
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
import os
import unittest
from unittest.mock import patch

from .. import get_verify_settings_parser, providers


class MockProvider1:
    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('mock_api_key', atype=str, required=True)


class MockProvider2:
    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('mock_auth_token', atype=str, required=True)


SETTINGS_PHONE_MOCK = {
    'VERIFY_AUTO_UPDATE': 'true',
    'VERIFY_AUTO_SEND_SIGNUP': 'true',
    'VERIFY_AUTO_SEND_UPDATE': 'true',
    'VERIFY_REQUIRED': 'true',
    'VERIFY_CRITERIA': 'any',
    'VERIFY_ERROR_REDIRECT': 'http://example.com/error_redirect',
    'VERIFY_ERROR_HTML_URL': 'http://example.com/error_html_url',
    'VERIFY_KEYS': 'phone',
    'VERIFY_KEYS_PHONE_CODE_FORMAT': 'numeric',
    'VERIFY_KEYS_PHONE_SUCCESS_REDIRECT':
        'http://example.com/success_redirect',
    'VERIFY_KEYS_PHONE_ERROR_REDIRECT':
        'http://example.com/error_redirect',
    'VERIFY_KEYS_PHONE_SUCCESS_HTML_URL':
        'http://example.com/success_html_url',
    'VERIFY_KEYS_PHONE_ERROR_HTML_URL':
        'http://example.com/error_html_url',
    'VERIFY_KEYS_PHONE_PROVIDER': 'mock',
    'VERIFY_KEYS_PHONE_PROVIDER_MOCK_API_KEY': 'some-api-key',
}


SETTINGS_PHONE_EMAIL_MOCK = {
        'VERIFY_KEYS': 'phone,email',
        'VERIFY_KEYS_PHONE_CODE_FORMAT': 'numeric',
        'VERIFY_KEYS_PHONE_EXPIRY': '60',
        'VERIFY_KEYS_PHONE_PROVIDER': 'mock1',
        'VERIFY_KEYS_PHONE_PROVIDER_MOCK_API_KEY': 'some-api-key',
        'VERIFY_KEYS_EMAIL_CODE_FORMAT': 'complex',
        'VERIFY_KEYS_EMAIL_EXPIRY': '30',
        'VERIFY_KEYS_EMAIL_PROVIDER': 'mock2',
        'VERIFY_KEYS_EMAIL_PROVIDER_MOCK_AUTH_TOKEN': 'some-auth-token',
}


class TestVerifySettingsParser(unittest.TestCase):
    @patch.dict(os.environ, SETTINGS_PHONE_MOCK)
    @patch.dict(providers._providers, {'mock': MockProvider1}, clear=True)
    def test_single_key(self):
        parser = get_verify_settings_parser()
        ns = parser.parse_settings()
        assert ns.auto_update
        assert ns.auto_send_signup
        assert ns.auto_send_update
        assert ns.required
        assert ns.criteria == 'any'
        assert ns.error_redirect == 'http://example.com/error_redirect'
        assert ns.error_html_url == 'http://example.com/error_html_url'
        assert set(ns.keys.keys()) == set(['phone'])
        assert ns.keys['phone'].code_format == 'numeric'
        assert ns.keys['phone'].success_redirect == \
            'http://example.com/success_redirect'
        assert ns.keys['phone'].error_redirect == \
            'http://example.com/error_redirect'
        assert ns.keys['phone'].success_html_url == \
            'http://example.com/success_html_url'
        assert ns.keys['phone'].error_html_url == \
            'http://example.com/error_html_url'
        assert ns.keys['phone'].provider.name == 'mock'
        assert ns.keys['phone'].provider.mock_api_key == 'some-api-key'

    @patch.dict(os.environ, SETTINGS_PHONE_EMAIL_MOCK)
    @patch.dict(providers._providers,
                {'mock1': MockProvider1, 'mock2': MockProvider2},
                clear=True)
    def test_multiple_keys(self):
        parser = get_verify_settings_parser()
        ns = parser.parse_settings()
        assert set(ns.keys.keys()) == set(['phone', 'email'])
        assert ns.keys['phone'].code_format == 'numeric'
        assert ns.keys['phone'].expiry == 60
        assert ns.keys['phone'].provider.name == 'mock1'
        assert ns.keys['phone'].provider.mock_api_key == 'some-api-key'
        assert ns.keys['email'].code_format == 'complex'
        assert ns.keys['email'].expiry == 30
        assert ns.keys['email'].provider.name == 'mock2'
        assert ns.keys['email'].provider.mock_auth_token == 'some-auth-token'
