import os

import pyzmail


def smtp_params():
    """
    Get SMTP settings from environment variables. The return value is
    a dict to supply to pyzmail.
    """
    SMTP_VARS = [
        'SMTP_HOST', 'SMTP_PORT', 'SMTP_MODE', 'SMTP_LOGIN', 'SMTP_PASSWORD'
        ]

    # get each SMTP settings from environment variables
    params = {}
    for var_name in SMTP_VARS:
        var_value = os.getenv(var_name)
        if not var_value:
            continue

        params[var_name.lower()] = var_value

    return params


def mail_is_configured():
    return bool(os.getenv('SMTP_HOST'))


def send_mail(sender, to, subject, text, html=None):
    """
    Send email to user.
    """
    encoding = 'utf-8'
    text_args = (text, encoding)
    html_args = (html, encoding) if html else None
    payload, mail_from, rcpt_to, msg_id = pyzmail.compose_mail(
        sender, [to], subject, encoding, text_args, html=html_args)

    ret = pyzmail.send_mail(payload, mail_from, rcpt_to, **smtp_params())
    if ret:
        raise Exception('Unable to send email to the receipient.')
