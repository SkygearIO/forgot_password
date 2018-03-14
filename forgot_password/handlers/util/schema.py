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
from skygear.container import SkygearContainer
from skygear.error import SkygearException
from skygear.options import options as skyoptions


def schema_add_key_verified_flags(flag_names):
    """
    Add the fields into Skygear DB user record.

    This function adds the specified fields into the user record schema. It
    is expected that all fields have boolean data type.
    """
    if not flag_names:
        return

    container = SkygearContainer(
        api_key=skyoptions.masterkey
    )

    # Fetch schema first. If no changes are required, we will not try
    # to update the schema.
    resp = container.send_action("schema:fetch", {
    }, plugin_request=True)
    if "error" in resp:
        raise SkygearException.from_dict(resp["error"])

    for field in resp['result']['record_types']['user']['fields']:
        if field['name'] in flag_names:
            flag_names.remove(field['name'])

    # `flag_names` now contain the list of fields to create. Proceed
    # to create the field list and save the new fields to user record
    # schema.
    fields = [
        {
            'name': flag_name,
            'type': 'boolean'
        }
        for flag_name in flag_names
    ]

    resp = container.send_action("schema:create", {
        "record_types": {
            'user': {
                'fields': fields
            }
        }
    }, plugin_request=True)
    if "error" in resp:
        raise SkygearException.from_dict(resp["error"])


def schema_add_key_verified_acl(flag_names):
    """
    Add field ACL to disallow owner from modifying verified flags.
    """
    container = SkygearContainer(
        api_key=skyoptions.masterkey
    )

    # Fetch the current field ACL. If no changes are required, we will
    # not try to update the field ACL.
    resp = container.send_action("schema:field_access:get",
                                 {},
                                 plugin_request=True)
    if "error" in resp:
        raise SkygearException.from_dict(resp["error"])

    # Create the new ACL settings. This is accomplished by first
    # copying the existing field ACLs, ignoring the entries we need
    # to enforce.
    new_acls = []
    for acl in resp['result']['access']:
        if acl['record_type'] == 'user' \
                and acl['record_field'] in flag_names \
                and acl['user_role'] == '_owner':
            continue
        new_acls.append(acl)

    for flag_name in flag_names:
        new_acls.append({
            'record_type': 'user',
            'record_field': flag_name,
            'user_role': '_owner',
            'writable': False,
            'readable': True,
            'comparable': True,
            'discoverable': True,
        })

    if not new_acls:
        return

    # Update the field ACL.
    resp = container.send_action("schema:field_access:update", {
        "access": new_acls
    }, plugin_request=True)
    if "error" in resp:
        raise SkygearException.from_dict(resp["error"])
