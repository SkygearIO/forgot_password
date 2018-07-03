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
  his/her password is failed to reset. Error message is passed via query string
  with key "error". If absent, the page generated from [template](#template)
  will be returned to user.

### SMTP settings

SMTP settings are required for the plugin to send outgoing email.

* `SMTP_HOST` - hostname of the mail server (required)
* `SMTP_PORT` - port number of the mail server (optional)
* `SMTP_MODE` - specify `tls` to use TLS transport (optional)
* `SMTP_LOGIN` - username for authentication (optional)
* `SMTP_PASSWORD` - password for authentication (optional)

### Welcome email settings

Welcome email settings defines the behaviour of sending welcome email
to the newly signed up users.

* `FORGOT_PASSWORD_WELCOME_EMAIL_ENABLE` - the option indicating whether
  the plugin will send welcome email to user after sign up. The
  default value is "NO".
* `FORGOT_PASSWORD_WELCOME_EMAIL_SENDER` - the sender of the welcome
  email
* `FORGOT_PASSWORD_WELCOME_EMAIL_SUBJECT` - the subject of the
  welcome email
* `FORGOT_PASSWORD_WELCOME_EMAIL_REPLY_TO` - the "Reply-to" option of the
  welcome email

### Verify user settings

This settings change the behaviour of verifying the user data:

* `VERIFY_URL_PREFIX` - the URL prefix for accessing the Skygear
  Server. The plugin requires this to generate the reset password link.
  The value should include protocol (e.g. `https://`).

* `VERIFY_KEYS` - The name of the user record fields which data can be verified.
  Specify multiple keys by separating them with comma. For example, if the
  user record contains the `phone` field and `email` field, specify
  `phone,email`.

* `VERIFY_AUTO_UPDATE` - Specify `true` to automatically update the `verified`
  flag of the user when the user becomes verified. Default is `false`.

* `VERIFY_AUTO_SEND_SIGNUP` - Specify `true` to automatically send verification
  to the user when the user signs up. Default is `false`.

* `VERIFY_AUTO_SEND_UPDATE` - Specify `true` to automatically send verification
  to the user when the user record has updated the fields that can be verified.
  Default is `false`.

* `VERIFY_REQUIRED` - Specify `true` if the user verification is required
  to access resources. When `true`, verification is also sent to the user
  when they sign up. Default is `false`.

* `VERIFY_CRITERIA` - Specify `all` so that all fields in `VERIFY_KEYS` has to
  be verified for the user to be considered verified. You can also specify
  a list of fields as criteria. Default is `any`, which means any verified keys
  will result in the user being considered verified.

* `VERIFY_MODIFY_SCHEMA` - When `true`, the plugin creates the necessary
  record fields. Default is `true`.

* `VERIFY_MODIFY_ACL` - When `true`, the plugin creates the recommended
  record fields access control. Default is `true`.

* `VERIFY_ERROR_REDIRECT` - Specify the redirect URL when there is an error
  to verify user data. Override `VERIFY_ERROR_HTML_URL`.

* `VERIFY_ERROR_HTML_URL` - Specify the URL of the HTML content template when there
  is an error to verify user data.

The following settings control the behaviour when verifying individual record
keys. These settings should be prefixed with `VERIFY_KEYS_<key_name>_`. For
example, set the code format for `phone` record field with
`VERIFY_KEYS_PHONE_CODE_FORMAT`.

* `CODE_FORMAT` - Specify `numeric` for numeric code. Specify `complex` for
  alphanumeric codes (higher security). Default is `numeric`.

* `EXPIRY` - Number of seconds after which the code is considered invalid.
  Specify `0` to disable code expiry (strongly discouraged). Default is 24
  hours.

* `SUCCESS_REDIRECT` - Specify the redirect URL when user data is verified.
  Override `SUCCESS_HTML_URL`.

* `SUCCESS_HTML_URL` - Specify the URL of the HTML content template when user
  data is verified.

* `ERROR_REDIRECT` - Specify the redirect URL when there is an error
  to verify user data. Override `ERROR_HTML_URL`.

* `ERROR_HTML_URL` - Specify the URL of the HTML content template when there
  is an error to verify user data.

* `PROVIDER` - Specify the name of the verification provider, see below.

Provider has provider-specific configuration, which should be prefixed with
`VERIFY_KEYS_<key>_PROVIDER_`. For example, set
`VERIFY_KEYS_EMAIL_PROVIDER_SUBJECT` to set the subject line of the verification
email that is sent to the user's `email` address.

For provider `smtp`:

* `SMTP_HOST` - Specify SMTP hostname or IP address. Default to `SMTP_HOST`.
* `SMTP_PORT` - Specify SMTP port. Default to `SMTP_PORT`.
* `SMTP_MODE` - Specify SMTP mode. Default to `SMTP_MODE`.
* `SMTP_LOGIN` - Specify SMTP login name. Default to `SMTP_LOGIN`.
* `SMTP_PASSWORD` - Specify SMTP login password. Default to `SMTP_PASSWORD`.
* `SMTP_SENDER` - Specify SMTP sender address. Default to `SMTP_SENDER`.
* `SMTP_REPLY_TO` - Specify SMTP reply-to address. Default to `SMTP_REPLY_TO`.
* `SUBJECT` - Specify email subject line.
* `EMAIL_TEXT_URL` - Specify the URL of the plaintext content template.
* `EMAIL_HTML_URL` - Specify the URL of the HTML content template (optional).

For provider `twilio`:

* `TWILIO_ACCOUNT_SID` - Specify Twilio account SID.
  Default to `TWILIO_ACCOUNT_SID`.
* `TWILIO_AUTH_TOKEN` - Specify Twilio auth token.
  Default to `TWILIO_AUTH_TOKEN`.
* `TWILIO_FROM` - Specify SMS sender phone number. Default to `TWILIO_FROM`.
* `SMS_TEXT_URL` - Specify the URL of the SMS content template.

For provider `nexmo`:

* `NEXMO_API_KEY` - Specify Nexmo API key. Default to `NEXMO_API_KEY`.
* `NEXMO_API_SECRET` - Specify Nemxo API secret. Default to `NEXMO_API_SECRET`.
* `NEXMO_FROM` - Specify SMS sender phone number. Default to `NEXMO_FROM`.
* `SMS_TEXT_URL` - Specify the URL of the SMS content template.

## Templates

This plugin provides basic HTML and email templates for handling forgot
password request. You can override the templates easily by creating
a `templates/forgot_password` folder in your cloud code project directory.

Please be reminded that both of text email template and HTML email template
will be sent to clients. Text template will serve as a fallback for email
clients not support html email.

You can also specify the corresponding environment variable indicating the url
of the template. The plugin will download the template before sending the
email.

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

* `templates/forgot_password/welcome_email.txt` - text template for the
  welcome email sent when the user is signed up successfully. The
  corresponding environment variable is
  `FORGOT_PASSWORD_WELCOME_EMAIL_TEXT_URL`.

* `templates/forgot_password/welcome_email.html` - html template for the
  welcome email sent when the user is signed up successfully. The
  corresponding environment variable is
  `FORGOT_PASSWORD_WELCOME_EMAIL_HTML_URL`.

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
