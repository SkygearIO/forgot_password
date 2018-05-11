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
import re
import unittest
from unittest.mock import patch

from ..email import Mailer


class MockProvider1:
    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('mock_api_key', atype=str, required=True)


class MockProvider2:
    @classmethod
    def configure_parser(cls, key, parser):
        parser.add_setting('mock_auth_token', atype=str, required=True)


class TestSendMailSenderName(unittest.TestCase):

    @patch('pyzmail.send_mail2')
    def test_sender_and_reply_to_name(self, mock):
        mailer = Mailer()

        mailer.send_mail(
            ("Skygear", "no-reply@skygeario.com"),
            "user@skygeario.com",
            "User Verification",
            "You received this email because myapp would like to verify your"
            " email address.",
            "<p>You received this email because myapp would like to verify"
            " your email address.</p>",
            ("Skygear Admin", "admin@skygeario.com"),
        )
        args, kwargs = mock.call_args
        send_to_regex = re.compile(
            'From: Skygear <no-reply@skygeario.com>'
        )
        reply_to_regex = re.compile(
            'Reply-To: Skygear Admin <admin@skygeario.com>'
        )
        assert send_to_regex.search(args[0]) is not None
        assert reply_to_regex.search(args[0]) is not None
        assert args[1] == 'no-reply@skygeario.com'
        assert args[2] == ['user@skygeario.com']

    @patch('pyzmail.send_mail2')
    def test_no_sender_and_reply_to_name(self, mock):
        mailer = Mailer()

        mailer.send_mail(
            ("", "no-reply@skygeario.com"),
            "user@skygeario.com",
            "User Verification",
            "You received this email because myapp would like to verify your"
            " email address.",
            "<p>You received this email because myapp would like to verify"
            " your email address.</p>",
            ("", "admin@skygeario.com"),
        )
        args, kwargs = mock.call_args
        send_to_regex = re.compile(
            'From: no-reply@skygeario.com'
        )
        reply_to_regex = re.compile(
            'Reply-To: admin@skygeario.com'
        )
        assert send_to_regex.search(args[0]) is not None
        assert reply_to_regex.search(args[0]) is not None
        assert args[1] == 'no-reply@skygeario.com'
        assert args[2] == ['user@skygeario.com']

    @patch('pyzmail.send_mail2')
    def test_no_reply(self, mock):
        mailer = Mailer()

        mailer.send_mail(
            ("", "no-reply@skygeario.com"),
            "user@skygeario.com",
            "User Verification",
            "You received this email because myapp would like to verify your"
            " email address.",
            "<p>You received this email because myapp would like to verify"
            " your email address.</p>",
            ("", ""),
        )
        args, kwargs = mock.call_args
        send_to_regex = re.compile(
            'From: no-reply@skygeario.com'
        )
        reply_to_regex = re.compile(
            'Reply-To:'
        )
        assert send_to_regex.search(args[0]) is not None
        assert reply_to_regex.search(args[0]) is None
        assert args[1] == 'no-reply@skygeario.com'
        assert args[2] == ['user@skygeario.com']

    @patch('pyzmail.send_mail2')
    def test_none_sender_and_reply_to_name(self, mock):
        mailer = Mailer()

        mailer.send_mail(
            (None, "no-reply@skygeario.com"),
            "user@skygeario.com",
            "User Verification",
            "You received this email because myapp would like to verify your"
            " email address.",
            "<p>You received this email because myapp would like to verify"
            " your email address.</p>",
            (None, "admin@skygeario.com"),
        )
        args, kwargs = mock.call_args
        send_to_regex = re.compile(
            'From: no-reply@skygeario.com'
        )
        reply_to_regex = re.compile(
            'Reply-To: admin@skygeario.com'
        )
        assert send_to_regex.search(args[0]) is not None
        assert reply_to_regex.search(args[0]) is not None
        assert args[1] == 'no-reply@skygeario.com'
        assert args[2] == ['user@skygeario.com']
