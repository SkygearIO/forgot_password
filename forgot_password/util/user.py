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
import hashlib
from datetime import datetime

import bcrypt
from skygear.options import options as skyoptions
from skygear.utils.db import get_table, has_table
from sqlalchemy.sql import func, select


def generate_code(user, expire_at):
    """
    Generate a code that the user has to enter in order to reset
    password. The code is generated from user information. The code
    is invalidated when the password or last login date changes.
    """

    encoding = 'utf-8'

    m = hashlib.sha1()
    m.update(skyoptions.masterkey.encode(encoding))
    m.update(user.id.encode(encoding))
    m.update(user.email.encode(encoding))
    m.update(str(expire_at).encode(encoding))
    if user.password:
        m.update(user.password.encode(encoding))
    if user.last_login_at:
        m.update(str(user.last_login_at).encode(encoding))

    return m.hexdigest()[:8]


def get_user(c, user_id):
    """
    Get user information from the database with the specified user ID.
    """
    users = get_table('_user')
    stmt = select([
            users.c.id,
            users.c.email,
            users.c.password,
            users.c.last_login_at,
        ]) \
        .where(users.c.id == user_id)
    result = c.execute(stmt)
    return result.fetchone()


def get_user_record(c, user_id):
    """
    Get user record from the database with the specified user ID.
    """
    if not has_table('user'):
        return None

    users = get_table('user')
    stmt = select([users]).where(users.c._id == user_id)
    result = c.execute(stmt)
    return result.fetchone()


def get_user_from_email(c, email):
    """
    Get user information from the database with the specified user email.
    """
    users = get_table('_user')
    stmt = select([
            users.c.id,
            users.c.email,
            users.c.password,
            users.c.last_login_at,
        ]) \
        .where(users.c.email == email)
    result = c.execute(stmt)
    return result.fetchone()


def get_user_and_validate_code(c, user_id, code, expire_at):
    """
    Get user information from the database with the specified user ID and
    verification code.
    """
    if not user_id or not code:
        return None

    if datetime.utcnow().timestamp() > expire_at:
        return None

    user = get_user(c, user_id)
    if code != generate_code(user, expire_at):
        return None
    return user


def set_new_password(c, user_id, new_password):
    """
    Set the password of a user to a new password.
    """
    encoded_password = new_password.encode('utf-8')
    hashed = bcrypt.hashpw(encoded_password, bcrypt.gensalt()).decode()
    users = get_table('_user')
    stmt = users.update() \
        .where(users.c.id == user_id) \
        .values(password=hashed) \
        .values(token_valid_since=func.now()) \
        .values(last_login_at=func.now()) \
        .values(last_seen_at=func.now())
    return c.execute(stmt)
