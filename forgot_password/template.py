import os

import jinja2


def jinja_env():
    return jinja2.Environment(loader=jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(os.path.abspath("templates/forgot_password")),
        jinja2.PackageLoader(__name__, 'templates'),
    ]))


def reset_email_text(**kwargs):
    template = jinja_env().get_template('forgot_password_email.txt')
    text = template.render(**kwargs)
    return text


def reset_email_html(**kwargs):
    try:
        template = jinja_env().get_template('forgot_password_email.html')
        html = template.render(**kwargs)
        return html
    except jinja2.TemplateNotFound:
        return None


def reset_password_form(**kwargs):
    template = jinja_env().get_template('reset_password.html')
    body = template.render(**kwargs)
    return body


def reset_password_success(**kwargs):
    template = jinja_env().get_template('reset_password_success.html')
    body = template.render(**kwargs)
    return body


def reset_password_error(**kwargs):
    template = jinja_env().get_template('reset_password_error.html')
    body = template.render(**kwargs)
    return body
