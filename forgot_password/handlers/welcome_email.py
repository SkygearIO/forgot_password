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

import skygear

from .template import FileTemplate
from .util import email as email_util
from .util import user as user_util

logger = logging.getLogger(__name__)


def send_email(template_provider,
               user,
               user_record,
               settings,
               smtp_settings,
               welcome_email_settings):
    if not smtp_settings.host:
        logger.error('Mail server is not configured. '
                     'Ignore sending notification email')
        return

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
        get_template('welcome_email_text').\
        render(**email_params)
    html = template_provider.\
        get_template('welcome_email_html').\
        render(**email_params)

    sender = welcome_email_settings.sender
    reply_to = welcome_email_settings.reply_to
    subject = welcome_email_settings.subject

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
        logger.info('Successfully sent welcome email '
                    'to user {}'.format(user.id))
    except Exception as ex:
        logger.error('An error occurred sending welcome '
                     'email to user {}: {}'.format(user.id, str(ex)))


def add_templates(template_provider, settings):
    template_provider.add_template(
        FileTemplate('welcome_email_text', 'welcome_email.txt',
                     download_url=settings.text_url))
    template_provider.add_template(
        FileTemplate('welcome_email_html', 'welcome_email.html',
                     download_url=settings.html_url,
                     required=False))
    return template_provider


def register_hooks(**kwargs):
    """
    Register DB hooks for sending welcome email
    """

    template_provider = kwargs['template_provider']
    settings = kwargs['settings']
    smtp_settings = kwargs['smtp_settings']
    welcome_email_settings = kwargs['welcome_email_settings']

    if not welcome_email_settings.enable:
        #  No need to register
        return

    @skygear.after_save('user', async=True)
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

        send_email(template_provider, user, record,
                   settings, smtp_settings, welcome_email_settings)
