# Copyright 2018 Oursky Ltd.
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
import unittest
from unittest.mock import patch

from ... import providers


class MockProvider:
    pass


class TestProvidersRegistry(unittest.TestCase):
    @patch.dict(providers._providers, clear=True)
    def test_register_provider_class(self):
        providers.register_provider_class('mock', MockProvider)
        assert providers._providers == {'mock': MockProvider}

    @patch.dict(providers._providers, {'mock': MockProvider}, clear=True)
    def test_get_provider_class(self):
        klass = providers.get_provider_class('mock', MockProvider)
        assert klass == MockProvider
