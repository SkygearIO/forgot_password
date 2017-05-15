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

import jinja2


def jinja_env():
    return jinja2.Environment(loader=jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(os.path.abspath("templates/forgot_password")),
        jinja2.PackageLoader(__name__, 'templates'),
    ]))


def reset_email_text(**kwargs):
    template = jinja_env().get_template('forgot_password_email.txt')
    text = template.render(**kwargs)
    return text


def reset_email_html(**kwargs):
    try:
        template = jinja_env().get_template('forgot_password_email.html')
        html = template.render(**kwargs)
        return html
    except jinja2.TemplateNotFound:
        return None


def reset_password_form(**kwargs):
    template = jinja_env().get_template('reset_password.html')
    body = template.render(**kwargs)
    return body


def reset_password_success(**kwargs):
    template = jinja_env().get_template('reset_password_success.html')
    body = template.render(**kwargs)
    return body


def reset_password_error(**kwargs):
    template = jinja_env().get_template('reset_password_error.html')
    body = template.render(**kwargs)
    return body


def welcome_email_text(**kwargs):
    template = jinja_env().get_template('welcome_email.txt')
    text = template.render(**kwargs)
    return text


def welcome_email_html(**kwargs):
    try:
        template = jinja_env().get_template('welcome_email.html')
        html = template.render(**kwargs)
        return html
    except jinja2.TemplateNotFound:
        return None
