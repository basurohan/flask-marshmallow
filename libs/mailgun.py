import os
from typing import List
from requests import Response, post

FAILED_LOAD_API_KEY = 'Failed to load Mailgun API Key.'
FAILED_LOAD_MAILGUN_DOMAIN = 'Failed to load Mailgun Domain.'
ERROR_SENDING_EMAIL = 'Error sending email'


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN')
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
    FROM_TITLE = 'Stores API'
    FROM_EMAIL = 'postmaster@sandbox7943aa6efa834fa687f213e57020e322.mailgun.org'

    @classmethod
    def send_email(cls, email: List[str], subject: str, text: str, html: str) -> Response:
        if cls.MAILGUN_DOMAIN is None:
            raise MailGunException(FAILED_LOAD_MAILGUN_DOMAIN)

        if cls.MAILGUN_API_KEY is None:
            raise MailGunException(FAILED_LOAD_API_KEY)

        response = post(
            f'https://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages',
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                'from': f'{cls.FROM_TITLE} <{cls.FROM_EMAIL}>',
                'to': email,
                'subject': subject,
                'text': text,
                'html': html
            },
        )

        if response.status_code != 200:
            raise MailGunException(ERROR_SENDING_EMAIL)

        return response
