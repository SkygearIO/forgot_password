import logging

import pyzmail

logger = logging.getLogger(__name__)


class Mailer:
    def __init__(self, **smtp_params):
        self.smtp_params = smtp_params

    def send_mail(self, sender, to, subject, text, html=None):
        """
        Send email to user.
        """
        encoding = 'utf-8'
        text_args = (text, encoding)
        html_args = (html, encoding) if html else None
        payload, mail_from, rcpt_to, msg_id = pyzmail.compose_mail(
            sender, [to], subject, encoding, text_args, html=html_args)

        try:
            pyzmail.send_mail2(payload,
                               mail_from,
                               rcpt_to,
                               **self.smtp_params)
        except Exception as e:
            logger.exception('Unable to send email to the receipient.')
            raise Exception('Unable to send email to the receipient.')
