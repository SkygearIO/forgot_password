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
import random
import string
import uuid

from skygear.utils.db import get_table
from sqlalchemy.sql import and_, desc, func, select


def get_verify_code(c, auth_id, code):
    """
    Get a previously created verify code from database.
    """
    code_table = get_table('_verify_code')

    # Query the table, will only return the newest code if multiple exists
    # for the same verification code
    stmt = select([code_table]) \
        .where(and_(code_table.c.auth_id == auth_id,
                    code_table.c.code == code)) \
        .order_by(desc(code_table.c.created_at))  # noqa
    result = c.execute(stmt)
    return result.fetchone()


def add_verify_code(c, auth_id, record_key, record_value, code):
    """
    Create a new verify code into the database.
    """
    code_table = get_table('_verify_code')
    values = {
        'id': str(uuid.uuid4()),
        'auth_id': auth_id,
        'record_key': record_key,
        'record_value': record_value,
        'code': code.strip(),
        'consumed': False,
        'created_at': func.now(),
    }
    c.execute(code_table.insert().values(**values))


def set_code_consumed(c, code_id):
    """
    Mark the specified verify code as consumed.
    """
    code_table = get_table('_verify_code')
    stmt = code_table.update().values(consumed=True) \
        .where(code_table.c.id == code_id)
    c.execute(stmt)


def generate_code(code_format):
    """
    Generate a verify code according to the specified code format.

    Return code string.
    """
    if code_format == 'numeric':
        return ''.join([random.choice(string.digits) for _ in range(6)])
    else:
        return ''.join([
            random.choice(string.digits + string.ascii_lowercase)
            for _ in range(8)
        ])


def verified_flag_name(record_key):
    """
    Return the name for verified flag for the corresponding record key.
    """
    return '{}_verified'.format(record_key)
