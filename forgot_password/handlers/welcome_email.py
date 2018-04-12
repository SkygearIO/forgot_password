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
import time
from collections import namedtuple

import skygear
from skygear import error as skyerror
from skygear.error import SkygearException
from skygear.models import Record, RecordID
from skygear.utils.context import current_context

from ..template import FileTemplate
from .template_mail import TemplateMailSender
from .util import user as user_util

logger = logging.getLogger(__name__)


def add_templates(template_provider, settings):
    template_provider.add_template(
        FileTemplate('welcome_email_text', 'welcome_email.txt',
                     download_url=settings.text_url))
    template_provider.add_template(
        FileTemplate('welcome_email_html', 'welcome_email.html',
                     download_url=settings.html_url,
                     required=False))
    return template_provider


def register_hooks_and_ops(**kwargs):
    """
    Register DB hooks for sending welcome email
    """

    template_provider = kwargs['template_provider']
    settings = kwargs['settings']
    smtp_settings = kwargs['smtp_settings']
    welcome_email_settings = kwargs['welcome_email_settings']
    mail_sender = TemplateMailSender(template_provider,
                                     smtp_settings,
                                     'welcome_email_text',
                                     'welcome_email_html')

    if not welcome_email_settings.enable:
        #  No need to register
        return

    register_hooks(mail_sender, settings, welcome_email_settings)
    register_ops(mail_sender, settings, welcome_email_settings)


def register_hooks(mail_sender, settings, welcome_email_settings):
    @skygear.after_save('user', async=True)  # noqa: NOTE(cheungpat): W606
    def user_after_save(record, original_record, db):
        if original_record:
            # ignore for old users
            return

        # FIXME: remove this when skygear maintain the same session between
        #        db hooks and record save
        #        Issue: https://github.com/SkygearIO/py-skygear/issues/142
        time.sleep(1)
        user_id = record.id.key
        user = user_util.get_user(db, user_id)

        if not user:
            logger.error('Cannot find user object with ID: {}'.format(user_id))
            return

        if not user.email:
            logger.info('User does not have an email')
            return

        url_prefix = settings.url_prefix
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]

        template_params = {
            'appname': settings.app_name,
            'url_prefix': url_prefix,
            'email': user.email,
            'user_id': user.id,
            'user': user,
            'user_record': record,
        }

        try:
            mail_sender.send(welcome_email_settings.sender,
                             user.email,
                             welcome_email_settings.subject,
                             reply_to=welcome_email_settings.reply_to,
                             template_params=template_params)
        except Exception as ex:
            logger.exception('An error occurred when sending welcome email '
                             'to user {}: {}'.format(user.id, str(ex)))


def register_ops(mail_sender, settings, welcome_email_settings):
    @skygear.op('user:welcome-email:test', key_required=True)
    def test_welcome_email(email,
                           text_template=None,
                           html_template=None,
                           subject=None,
                           sender=None,
                           reply_to=None):
        access_key_type = current_context().get('access_key_type')
        if not access_key_type or access_key_type != 'master':
            raise SkygearException(
                'master key is required',
                skyerror.AccessKeyNotAccepted
            )

        url_prefix = settings.url_prefix
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]

        dummy_user = namedtuple('User', ['id', 'email'])(
            'dummy-id',
            'dummy-user@example.com')

        dummy_record_id = RecordID('user', 'dummy-id')
        dummy_record = Record(dummy_record_id, dummy_record_id.key, None)

        template_params = {
            'appname': settings.app_name,
            'url_prefix': url_prefix,
            'email': dummy_user.email,
            'user_id': dummy_user.id,
            'user': dummy_user,
            'user_record': dummy_record,
        }

        email_sender = sender if sender else welcome_email_settings.sender
        email_subject = subject if subject else welcome_email_settings.subject
        email_reply_to = reply_to if reply_to \
            else welcome_email_settings.reply_to

        try:
            mail_sender.send(email_sender,
                             email,
                             email_subject,
                             reply_to=email_reply_to,
                             text_template_string=text_template,
                             html_template_string=html_template,
                             template_params=template_params)
        except Exception as ex:
            logger.exception('An error occurred when '
                             'testing welcome email: {}'.format(str(ex)))
            raise SkygearException(str(ex), skyerror.UnexpectedError)

        return {'status': 'OK'}
