# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
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
#
"""Contains a limited test server and testing functionality for local email verification."""
from contextlib import asynccontextmanager
from email import message_from_bytes
from email.message import EmailMessage, Message

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
from aiosmtpd.smtp import AuthResult, Envelope

from ns.config import Config


class Authenticator:
    """Basic authenticator so we can test error handling for failed authentication"""

    def __init__(self, user: str, password: str):
        self._user = user
        self._password = password

    def __call__(self, server, session, envelope, mechanism, auth_data):
        login = str(auth_data.login, encoding="utf-8")
        password = str(auth_data.password, encoding="utf-8")

        if login == self._user and password == self._password:
            return AuthResult(success=True)

        return AuthResult(success=False, handled=False)


class CustomHandler(Sink):
    """Single use handler"""

    def __init__(self):
        self.email_received: Envelope
        super().__init__()

    async def handle_DATA(self, server, session, envelope):
        """Handler function for email message which closes controller upon use"""
        self.email_received = envelope

        return "250 Ok"


def compare_payloads(received: Message, expected: EmailMessage):
    """Compare the corresponding parts for a multipart email"""
    expected_payload = expected.get_payload()
    received_payload = received.get_payload()
    # I don't think we'll have an issue with non-unique content types.
    # If we do, you could look for something like the content-id as a UID
    for part in expected_payload:
        content_type = part.get_content_type()
        for corresponding in received_payload:
            if corresponding.get_content_type() == content_type:
                assert part.as_bytes() == corresponding.as_bytes()


def check_emails(received: Envelope, expected: EmailMessage):
    """Compares two emails"""
    assert received is not None
    assert expected is not None
    message_received = message_from_bytes(received.content)  # type: ignore
    assert message_received["To"] == expected["To"]
    assert message_received["Cc"] == expected["Cc"]
    assert message_received["From"] == expected["From"]
    assert message_received["Subject"] == expected["Subject"]
    assert message_received.preamble == expected.preamble
    assert (
        message_received.get_content_disposition() == expected.get_content_disposition()
    )
    assert expected.is_multipart() == message_received.is_multipart()
    if expected.is_multipart():
        compare_payloads(received=message_received, expected=expected)
    else:
        standardized_expected = expected.get_payload().replace("\r\n", "\n")
        standardized_received = message_received.get_payload().replace("\r\n", "\n")
        assert standardized_expected == standardized_received


class EmailRecorder:
    """Listens for one email"""

    def __init__(self, *, expected_email: EmailMessage, controller: Controller):
        self._expected_email = expected_email
        self._controller = controller

    async def __aenter__(self):
        try:
            self._controller.start()

        except RuntimeError as err:
            self._controller.stop()
            raise RuntimeError(err.args[0]) from err

    async def __aexit__(self, *args):
        if self._controller.loop.is_running():
            self._controller.stop()


class DummyServer:
    """Test server for making sure emails are received as intended"""

    def __init__(self, *, config: Config):
        """assign config"""
        self._config = config
        self._login = self._config.login_user
        self._password = self._config.login_password
        self._host = self._config.smtp_host
        self._port = self._config.smtp_port

    def set_credentials(self, *, login: str, password: str):
        """Change the login and password"""
        self._login = login
        self._password = password

    def set_host(self, host: str):
        """Set the host name"""
        self._host = host

    def set_port(self, port: int):
        """Set the port after init"""
        self._port = port

    def _record_email(
        self, *, expected_email: EmailMessage, controller: Controller
    ) -> EmailRecorder:
        """Returns an async context manager with custom controller/handler"""
        return EmailRecorder(expected_email=expected_email, controller=controller)

    @asynccontextmanager
    async def expect_email(self, expected_email: EmailMessage):
        """Yields an async context manager with a single-use SMTP message handler,
        and compares the received message envelope with the original EmailMessage"""
        handler = CustomHandler()
        controller = Controller(
            handler,
            self._host,
            self._port,
            auth_require_tls=False,
            authenticator=Authenticator(self._login, self._password),
        )

        async with self.record_email(
            expected_email=expected_email, controller=controller
        ) as email_recorder:
            yield email_recorder

        check_emails(received=handler.email_received, expected=expected_email)
