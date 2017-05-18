# Forgot Password Plugin for Skygear

## Installation

If your app is hosted on [Skygear Cloud](https://portal.skygear.io/), this
plugin is added to your cloudcode automatically. For local development
install this plugin as a package or a submodule in your project.

## Configuration

The plugin is configured by environment variables.

### Basic settings

* `FORGOT_PASSWORD_APP_NAME` - the app name that will appear in the built-in
  template. If you use a different template, you do not need to supply an
  app name. The default app name is the Skygear Server app name.
* `FORGOT_PASSWORD_URL_PREFIX` - the URL prefix for accessing the Skygear
  Server. The plugin requires this to generate the reset password link.
  The value should include protocol (e.g. `https://`).
* `FORGOT_PASSWORD_SENDER` - email will be sent from this email address.
* `FORGOT_PASSWORD_SUBJECT` - subject of the email sent.
* `FORGOT_PASSWORD_REPLY_TO` - "Reply-to" option of the email sent.
* `FORGOT_PASSWORD_SECURE_MATCH` - an option to require the plugin to return an
  error if the email on the request is not found; otherwise, the plugin will
  return OK if the email on the request is not found. The default value of this
  option is "NO".
* `FORGOT_PASSWORD_RESET_URL_LIFETIME` - an option specify the expiration
  duration of the forgot password url in the unit of seconds. The default value
  is `43200` (12 hours).
* `FORGOT_PASSWORD_SUCCESS_REDIRECT` - the url user will be redirect to when
  his / her password is reset successfully. If absent, the page generated from
  [template](#template) will be returned to user.
* `FORGOT_PASSWORD_ERROR_REDIRECT` - the url user will be redirect to when
  his/her password is failed to reset. If absent, the page generated from
  [template](#template) will be returned to user.

### SMTP settings

SMTP settings are required for the plugin to send outgoing email.

* `SMTP_HOST` - hostname of the mail server (required)
* `SMTP_PORT` - port number of the mail server (optional)
* `SMTP_MODE` - specify `tls` to use TLS transport (optional)
* `SMTP_LOGIN` - username for authentication (optional)
* `SMTP_PASSWORD` - password for authentication (optional)

### Notification email settings

Notification email settings defines the behaviour of sending notification email
to the user when his / her password is reset successfully.

* `FORGOT_PASSWORD_NOTIFICATION_EMAIL_ENABLE` - the option indicating whether
  the plugin will send notification email to user after password reset. The
  default value is "NO".
* `FORGOT_PASSWORD_NOTIFICATION_EMAIL_SENDER` - the sender of the notification
  email
* `FORGOT_PASSWORD_NOTIFICATION_EMAIL_SUBJECT` - the subject of the
  notification email
* `FORGOT_PASSWORD_NOTIFICATION_EMAIL_REPLY_TO` - the "Reply-to" option of the
  email

## Templates

This plugin provides basic HTML and email templates for handling forgot
password request. You can override the templates easily by creating
a `templates/forgot_password` folder in your cloud code project directory.

Please be reminded that both of text email template and HTML email template
will be sent to clients. Text template will serve as a fallback for email
clients not support html email.

You can also specify the corresponding environment variable indicating the url
of the template. The plugin will download the template before serving requests.

For example, if you want to change how the forgot password email looks, create
a text file and save it to
`templates/forgot_password/forgot_password_email.txt`. Under your project
directory.

Here are a list of templates you can override:

* `templates/forgot_password/forgot_password_email.txt` - text template for
  the email which are sent to the user requesting for password reset. The
  corresponding environment variable is `FORGOT_PASSWORD_EMAIL_TEXT_URL`.

* `templates/forgot_password/forgot_password_email.html` - HTML template for
  the email which are sent to the user requesting for password reset. If
  you provide a HTML template, you must also provide a text template. The
  corresponding environment variable is `FORGOT_PASSWORD_EMAIL_HTML_URL`.

* `templates/forgot_password/reset_password.html` - HTML form for user
  to enter a new password. The corresponding environment variable is
  `FORGOT_PASSWORD_RESET_HTML_URL`.

* `templates/forgot_password/reset_password_error.html` - HTML page
  to show when there is an error with the code and User ID of the request. The
  corresponding environment variable is `FORGOT_PASSWORD_RESET_ERROR_HTML_URL`.

* `templates/forgot_password/reset_password_success.html` - HTML page
  to show when the user has reset the password successfully. The corresponding
  environment variable is `FORGOT_PASSWORD_RESET_SUCCESS_HTML_URL`.

* `templates/forgot_password/notification_email.txt` - text template for the
  notification email sent when password is reset successfully. The
  corresponding environment variable is
  `FORGOT_PASSWORD_NOTIFICATION_EMAIL_TEXT_URL`.

* `templates/forgot_password/notification_email.html` - html template for the
  notification email sent when password is reset successfully. The
  corresponding environment variable is
  `FORGOT_PASSWORD_NOTIFICATION_EMAIL_HTML_URL`.

You can reference variable for generating HTML/email with dynamic values. Here
is an incomplete list of variables:

* `{{ user }} ` - information about the user, use `{{ user.email }}`
  for user email

* `{{ user_record }} ` - the user record, if your app save the user name
  to the user record as the field `name`, use `{{ user_record.name }}` to get
  the user name

* `{{ user_id }} ` - ID of the user

* `{{ code }} ` - Code for the user to verify account ownership

* `{{ expire_at }} ` - Expiration timestamp of the url

You can copy the [provided templates](forgot_password/templates) to your
project directory to get started.

For documentation of the templating language, see
[Jinja2](http://jinja.pocoo.org/docs/dev/templates/).
