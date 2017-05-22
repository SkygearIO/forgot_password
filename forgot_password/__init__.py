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


from skygear.settings import add_parser as add_setting_parser

from .settings import \
    get_settings_parser, \
    get_smtp_settings_parser
from .handlers import register_handlers


def includeme(settings):
    register_handlers(settings.forgot_password,
                      settings.forgot_password_smtp)


add_setting_parser('forgot_password', get_settings_parser())
add_setting_parser('forgot_password_smtp', get_smtp_settings_parser())
