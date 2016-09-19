import hashlib

import bcrypt
from skygear.options import options as skyoptions
from skygear.utils.db import get_table, has_table
from sqlalchemy.sql import func, select


def generate_code(user):
    """
    Generate a code that the user has to enter in order to reset
    password. The code is generated from user information. The code
    is invalidated when the password or last login date changes.
    """
    m = hashlib.sha1()
    m.update(skyoptions.masterkey.encode('utf-8'))
    m.update(user.id.encode('utf-8'))
    m.update(user.email.encode('utf-8'))
    if user.password:
        m.update(user.password.encode('utf-8'))
    if user.last_login_at:
        m.update(str(user.last_login_at).encode('utf-8'))

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


def get_user_and_validate_code(c, user_id, code):
    """
    Get user information from the database with the specified user ID and
    verification code.
    """
    if not user_id or not code:
        return None

    user = get_user(c, user_id)
    if code != generate_code(user):
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
