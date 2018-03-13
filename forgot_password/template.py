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
import os
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlretrieve

import jinja2

logger = logging.getLogger(__name__)


class TemplateNotFound(Exception):
    def __init__(self, template_name):
        self._template_name = template_name

    @property
    def template_name(self):
        return self._template_name

    def __str__(self):
        return 'Cannot find template: {}'.format(self.template_name)


class FileTemplateDownloadError(Exception):
    def __init__(self, template_name, url, reason):
        self._template_name = template_name
        self._url = url
        self._reason = reason

    @property
    def template_name(self):
        return self._template_name

    @property
    def url(self):
        return self._url

    @property
    def reason(self):
        return self._reason

    def __str__(self):
        return 'Cannot download {} from {}: {}'.format(self.template_name,
                                                       self.url,
                                                       self.reason)


class BaseTemplate:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def get(self):
        """
        Get the template content.
        This method is expected to be overridden by subclasses.
        """
        return None

    def render(self, **kwargs):
        """
        Render template content.
        """
        template_content = self.get()
        return template_content.render(**kwargs) if template_content else None


class FileTemplate(BaseTemplate):
    @classmethod
    def get_download_dir_path(cls):
        return Path(tempfile.gettempdir()).joinpath('forgot_password',
                                                    'templates')

    @classmethod
    def get_jinja_env(cls):
        return jinja2.Environment(loader=jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(str(cls.get_download_dir_path())),
            jinja2.FileSystemLoader(
                os.path.abspath("templates/forgot_password")),
            jinja2.PackageLoader('forgot_password', 'templates'),
        ]))

    def __init__(self, name, file_name, download_url=None, required=True):
        super(FileTemplate, self).__init__(name)
        self._file_name = file_name
        self._download_url = download_url
        self._required = required

    @property
    def file_name(self):
        return self._file_name

    @property
    def download_url(self):
        return self._download_url

    @property
    def required(self):
        return self._required

    def download(self):
        """
        Download template file from the URL.
        """
        dir_path = self.get_download_dir_path()
        file_path = dir_path.joinpath(self.file_name)

        dir_path.mkdir(parents=True, exist_ok=True)

        try:
            logger.info('Downloading {} from {}'.format(self.file_name,
                                                        self.download_url))
            urlretrieve(self.download_url, str(file_path))
        except URLError as ex:
            logger.error('Failed to download {} from {}: {}'.format(
                self.file_name, self.download_url, ex.reason))
            raise FileTemplateDownloadError(self.file_name,
                                            self.download_url,
                                            ex.reason)

    def get(self):
        """
        Get the template content.
        """
        dir_path = self.get_download_dir_path()
        file_path = dir_path.joinpath(self.file_name)

        if self.download_url and not file_path.exists():
            self.download()

        try:
            return self.get_jinja_env().get_template(self.file_name)
        except jinja2.TemplateNotFound as ex:
            if self.required:
                raise TemplateNotFound(self.name)
            return None


class StringTemplate(BaseTemplate):
    @classmethod
    def get_jinja_env(cls):
        return jinja2.Environment(loader=jinja2.BaseLoader())

    def __init__(self, name, content):
        super(StringTemplate, self).__init__(name)
        self._content = content

    @property
    def content(self):
        return self._content

    def get(self):
        """
        Get the template content.
        """
        if not self.content:
            return None
        return self.get_jinja_env().from_string(self.content)


class TemplateProvider:
    def __init__(self, *args):
        self._templates = {}
        for each_template in args:
            self.add_template(each_template)

    def add_template(self, template):
        name = template.name
        self._templates[name] = template

    def get_template(self, name):
        try:
            return self._templates[name]
        except KeyError:
            raise TemplateNotFound(name)
