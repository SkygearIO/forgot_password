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
import os

from skygear.options import options as skyoptions


class Namespace:
    @property
    def appname(self):
        return os.getenv('FORGOT_PASSWORD_APPNAME', skyoptions.appname)

    @property
    def url_prefix(self):
        url_prefix = os.getenv('FORGOT_PASSWORD_URL_PREFIX',
            os.getenv('URL_PREFIX', skyoptions.skygear_endpoint))  # noqa
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        return url_prefix

    @property
    def sender(self):
        return os.getenv('FORGOT_PASSWORD_SENDER', 'no-reply@skygeario.com')

    @property
    def subject(self):
        return os.getenv('FORGOT_PASSWORD_SUBJECT',
                         'Reset password instructions')

    @property
    def smtp_host(self):
        return os.getenv('SMTP_HOST')

    @property
    def smtp_port(self):
        return int(os.getenv('SMTP_PORT', '25'))

    @property
    def smtp_mode(self):
        return os.getenv('SMTP_MODE', 'normal')

    @property
    def smtp_login(self):
        return os.getenv('SMTP_LOGIN')

    @property
    def smtp_password(self):
        return os.getenv('SMTP_PASSWORD')


options = Namespace()
