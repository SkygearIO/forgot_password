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
from skygear.settings import SettingsParser, add_parser, settings

parser = SettingsParser('FORGOT_PASSWORD')

parser.add_setting('enable', atype=bool, default=False)
parser.add_setting('appname', env_var='APP_NAME')
parser.add_setting('url_prefix', default='http://127.0.0.1:3000')
parser.add_setting('sender', default='no-reply@skygeario.com')
parser.add_setting('smtp_host', required=False)
parser.add_setting('smtp_port', atype=int, default=25)
parser.add_setting('smtp_mode', default='normal')
parser.add_setting('smtp_login', required=False)
parser.add_setting('smtp_password', required=False)

if not hasattr(settings, 'forgot_password'):
    add_parser('forgot_password', parser)
