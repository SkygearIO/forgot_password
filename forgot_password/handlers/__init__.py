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

from .template import TemplateProvider
from .forgot_password import add_templates as add_forgot_password_templates
from .forgot_password import register_op as register_forgot_password_op
from .reset_password import add_templates as add_reset_password_templates
from .reset_password import register_op as register_reset_password_op
from .reset_password import register_handlers \
    as register_reset_password_handlers


def register_handlers(**kwargs):
    settings = kwargs['settings']

    template_provider = TemplateProvider()
    add_forgot_password_templates(template_provider, settings)
    add_reset_password_templates(template_provider, settings)

    register_forgot_password_op(template_provider=template_provider, **kwargs)
    register_reset_password_op(template_provider=template_provider, **kwargs)
    register_reset_password_handlers(template_provider=template_provider,
                                     **kwargs)
