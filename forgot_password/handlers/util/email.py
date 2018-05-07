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

import pyzmail

logger = logging.getLogger(__name__)


class Mailer:
    def __init__(self, **smtp_params):
        self.smtp_params = smtp_params

    def send_mail(self, sender, to, subject, text, html=None, reply_to=None):
        """
        Send email to user.

        Arguments:
        sender - (string or tuple) email or a tuple of the form
            ('Name', 'sender@example.com')
        to - (string) - recipient address
        subject - (str) The subject of the message
        text - (tuple or None) The text version of the message
        html - (tuple or None) The HTML version of the message
        reply_to - (string or tuple) email or a tuple of the form
            ('Name', 'reply@example.com')
        """
        encoding = 'utf-8'
        text_args = (text, encoding)
        html_args = (html, encoding) if html else None
        headers = []

        reply_to_tuple = self._convert_email_tuple(reply_to)
        sender_tuple = self._convert_email_tuple(sender)

        if reply_to_tuple and reply_to_tuple[1]:
            # only append header when there is reply to email
            reply_to_value = pyzmail.generate.format_addresses(
                [reply_to_tuple, ], header_name='Reply-To', charset=encoding
            )
            headers.append(('Reply-To', reply_to_value))

        payload, mail_from, rcpt_to, msg_id = pyzmail.compose_mail(
            sender_tuple, [to], subject, encoding, text_args,
            html=html_args, headers=headers)

        try:
            pyzmail.send_mail2(payload,
                               mail_from,
                               rcpt_to,
                               **self.smtp_params)
        except Exception:
            logger.exception('Unable to send email to the receipient.')
            raise Exception('Unable to send email to the receipient.')

    def _convert_email_tuple(self, email):
        """
        Convert email to tuple format or None, email accepts string or tuple.
        """
        if not email:
            return None

        if isinstance(email, str):
            return ('', email)

        # pyzmail only accepts empty string for false value
        return tuple(x if x else '' for x in email)
