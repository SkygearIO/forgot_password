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
_providers = {}


def register_provider_class(name, klass):
    global _providers

    _providers[name] = klass


def get_provider_class(name):
    global _providers
    if name not in _providers:
        msg = 'Provider `{}` is not installed.'.format(name)
        if _providers:
            msg += ' Available providers: {}.' \
                .format(", ".join(_providers.keys()))
        else:
            msg += ' No providers are configured.'
        raise KeyError(msg)
    return _providers[name]
