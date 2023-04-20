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

"""Test basic event consumption"""
import asyncio

import pytest
from hexkit.providers.akafka.testutils import kafka_fixture  # noqa: F401

from ns.adapters.outbound.smtp_client import SmtpClient
from ns.core.notifier import Notifier
from tests.fixtures.config import get_config
from tests.fixtures.joint import JointFixture, joint_fixture  # noqa: F401
from tests.fixtures.server import DummyServer
from tests.fixtures.utils import DummySmtpClient, get_free_port, make_notification


@pytest.mark.asyncio
async def test_basic_path(joint_fixture: JointFixture):  # noqa: F811
    """Verify that the event is correctly translated into a basic email object"""
    await joint_fixture.kafka.publish_event(
        payload={
            "recipient_email": "test@example.com",
            "email_cc": [],
            "email_bcc": [],
            "subject": "Test123",
            "recipient_name": "Yolanda Martinez",
            "plaintext_body": "Where are you, where are you, Yolanda?",
        },
        type_=joint_fixture.config.notification_event_type,
        topic=joint_fixture.config.notification_event_topic,
    )

    event_subscriber = await joint_fixture.container.kafka_event_subscriber()
    with pytest.raises(ConnectionRefusedError):
        # the connection error tells us that the smtp_client tried to connect, which
        # means that the consumer successfully passed the event through the notifier
        # and on to the client for emailing.
        await event_subscriber.run(forever=False)


@pytest.mark.parametrize(
    "notification_details",
    [
        {
            "recipient_email": "test@example.com",
            "email_cc": ["test2@test.com", "test3@test.com"],
            "email_bcc": ["test4@test.com", "test5@test.com"],
            "subject": "Test123",
            "recipient_name": "Yolanda Martinez",
            "plaintext_body": "Where are you, where are you, Yolanda?",
        }
    ],
)
@pytest.mark.asyncio
async def test_email_construction(notification_details):
    """Verify that the email is getting constructed properly from the template."""
    config = get_config()
    notification = make_notification(notification_details)

    dummy_smtp_client = DummySmtpClient()
    notifier = Notifier(config=config, smtp_client=dummy_smtp_client)
    await notifier.send_notification(notification=notification)

    msg = dummy_smtp_client.expected_email

    assert msg is not None

    plaintext_body = msg.get_body(preferencelist="plain")
    assert plaintext_body is not None

    plaintext_content = plaintext_body.get_content()  # type: ignore[attr-defined]
    expected_plaintext = "Dear Yolanda Martinez,\n\nWhere are you, where are you, Yolanda?\n\nWarm regards,\n\nThe GHGA Team"
    assert plaintext_content.strip() == expected_plaintext

    if msg.is_multipart():
        html_body = msg.get_body(preferencelist="html")
        assert html_body is not None

        html_content = html_body.get_content()  # type: ignore[attr-defined]
        assert html_content is not None

        expected_html = '<!DOCTYPE html><html><head></head><body style="color: #00393f;padding: 12px;"><h2>Dear Yolanda Martinez,</h2><p>Where are you, where are you, Yolanda?</p><p>Warm regards,</p><h3>The GHGA Team</h3></body></html>'
        assert html_content.strip() == expected_html


@pytest.mark.parametrize(
    "notification_details",
    [
        {
            "recipient_email": "test@example.com",
            "email_cc": ["test2@test.com", "test3@test.com"],
            "email_bcc": ["test4@test.com", "test5@test.com"],
            "subject": "Test123",
            "recipient_name": "Yolanda Martinez",
            "plaintext_body": "Where are you, where are you, Yolanda?",
        }
    ],
)
@pytest.mark.asyncio
async def test_transmission(notification_details):
    """Test that the email that the test server gets is what we expect"""
    config = get_config()
    notification = make_notification(notification_details)
    port_to_use = get_free_port()

    dummy_smtp_client = DummySmtpClient()
    smtp_client = SmtpClient(config=config, debugging=True)
    smtp_client.set_port(port_to_use)

    server = DummyServer(config=config)
    server.set_port(port_to_use)

    notifier = Notifier(config=config, smtp_client=dummy_smtp_client)

    # send the notification so it gets intercepted by the dummy client
    await notifier.send_notification(notification=notification)

    # tell the smtp client to send the message and compare that with what is received
    async with server.expect_email(expected_email=dummy_smtp_client.expected_email):
        smtp_client.send_email_message(dummy_smtp_client.expected_email)
        asyncio.get_running_loop().stop()

    # change login credentials so authentication fails
    server.set_credentials(login="bob@bobswebsite.com", password="notCorrect")
    with pytest.raises(SmtpClient.FailedLoginError):
        async with server.expect_email(expected_email=dummy_smtp_client.expected_email):
            smtp_client.send_email_message(dummy_smtp_client.expected_email)
            asyncio.get_running_loop().stop()
