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


def get_settings_parser():
    parser = SettingsParser('FORGOT_PASSWORD')

    parser.add_setting('app_name', default=skyoptions.appname)
    parser.add_setting('url_prefix', default=skyoptions.skygear_endpoint)
    parser.add_setting(
        'secure_match',
        atype=bool,
        required=False,
        resolve=False,
        default=False
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
