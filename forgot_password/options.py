import os

from skygear.options import options as skyoptions


class Namespace:
    @property
    def appname(self):
        return os.getenv('FORGOT_PASSWORD_APPNAME', skyoptions.appname)

    @property
    def url_prefix(self):
        url_prefix = os.getenv('FORGOT_PASSWORD_URL_PREFIX',
            os.getenv('URL_PREFIX', skyoptions.skygear_endpoint))  # noqa
        if url_prefix.endswith('/'):
            url_prefix = url_prefix[:-1]
        return url_prefix

    @property
    def sender(self):
        return os.getenv('FORGOT_PASSWORD_SENDER', 'no-reply@skygeario.com')

    @property
    def subject(self):
        return os.getenv('FORGOT_PASSWORD_SUBJECT',
                         'Reset password instructions')

    @property
    def smtp_host(self):
        return os.getenv('SMTP_HOST')

    @property
    def smtp_port(self):
        return int(os.getenv('SMTP_PORT', '25'))

    @property
    def smtp_mode(self):
        return os.getenv('SMTP_MODE', 'normal')

    @property
    def smtp_login(self):
        return os.getenv('SMTP_LOGIN')

    @property
    def smtp_password(self):
        return os.getenv('SMTP_PASSWORD')


options = Namespace()
