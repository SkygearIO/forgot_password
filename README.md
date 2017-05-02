# Forgot Password Plugin for Skygear

## Installation

If your app is hosted on [Skygear Cloud](https://portal.skygear.io/), this
plugin is added to your cloudcode automatically. For local development
install this plugin as a package or a submodule in your project.

## Configuration

The plugin is configured by environment variables.

### SMTP settings

SMTP settings are required for the plugin to send outgoing email.

* `SMTP_HOST` - hostname of the mail server (required)
* `SMTP_PORT` - port number of the mail server (optional)
* `SMTP_MODE` - specify `tls` to use TLS transport (optional)
* `SMTP_LOGIN` - username for authentication (optional)
* `SMTP_PASSWORD` - password for authentication (optional)

### Other settings

* `FORGOT_PASSWORD_APP_NAME` - the app name that will appear in the built-in
  template. If you use a different template, you do not need to supply an
  app name. The default app name is the Skygear Server app name.
* `FORGOT_PASSWORD_URL_PREFIX` - the URL prefix for accessing the Skygear
  Server. The plugin requires this to generate the reset password link.
  The value should include protocol (e.g. `https://`).
* `FORGOT_PASSWORD_SENDER` - email will be sent from this email address.
* `FORGOT_PASSWORD_SUBJECT` - subject of the email sent.
* `FORGOT_PASSWORD_SECURE_MATCH` - an option to require the plugin to return an
  error if the email on the request is not found; otherwise, the plugin will
  return OK if the email on the request is not found. The default value of this
  option is "NO".

## Templates

This plugin provides basic HTML and email templates for handling forgot
password request. You can override the templates easily by creating
a `templates/forgot_password` folder in your cloudcode project directory.

For example, if you want to change how the forgot password email looks, create
a text file and save it to
`templates/forgot_password/forgot_password_email.txt`. Under your project
directory.

Here are a list of templates you can override:

* `templates/forgot_password/forgot_password_email.txt` - text template for
  the email which are sent to the user requesting for password reset.

* `templates/forgot_password/forgot_password_email.html` - HTML template for
  the email which are sent to the user requesting for password reset. If
  you provide a HTML template, you must also provide a text template.

* `templates/forgot_password/reset_password.html` - HTML form for user
  to enter a new password.

* `templates/forgot_password/reset_password_error.html` - HTML page
  to show when there is an error with the code and User ID of the request.

* `templates/forgot_password/reset_password_success.html` - HTML page
  to show when the user has reset the password successfully.

You can reference variable for generating HTML/email with dynamic values. Here
is an incomplete list of variables:

* `{{ user }} ` - information about the user, use `{{ user.email }}`
  for user email

* `{{ user_record }} ` - the user record, if your app save the user name
  to the user record as the field `name`, use `{{ user_record.name }}` to get
  the user name

* `{{ user_id }} ` - ID of the user

* `{{ code }} ` - Code for the user to verify account ownership

You can copy the [provided templates](forgot_password/templates) to your
project directory to get started.

For documentation of the templating language, see
[Jinja2](http://jinja.pocoo.org/docs/dev/templates/).
