# Copyright 2021 - 2025 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
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

import json
from functools import partial
from typing import cast
from uuid import UUID

import pytest
import pytest_asyncio
from hexkit.correlation import correlation_id_var
from hexkit.protocols.dao import ResourceNotFoundError
from hexkit.providers.akafka.testutils import KafkaFixture
from httpx import Request as HttpxRequest
from jsonschema_path import SchemaPath
from openapi_core.contrib.requests import (
    RequestsOpenAPIRequest,
)
from openapi_core.validation.request.validators import V30RequestValidator
from openapi_core.validation.response.validators import V30ResponseValidator
from pytest_httpx import HTTPXMock
from requests import PreparedRequest, Request

from ns.adapters.outbound.sms_client import SmsAuthConfig, SmsClient
from ns.inject import prepare_core, prepare_event_subscriber
from ns.ports.outbound.dao import EventIdDaoPort
from tests.fixtures.config import get_config
from tests.fixtures.joint import JointFixture, JointFixtureDlq, joint_fixture_dlq
from tests.fixtures.utils import make_sms_notification

pytestmark = pytest.mark.asyncio()



SAMPLE_SMS_NOTIFICATION = {
    "phone": "+491234567890",
    "text": "Where are you, where are you, Yolanda?",
}

LOX24_SMS_RESPONSE_MOCK = {
    "method": "POST",
    "url": "https://api.lox24.eu/sms",
    "match_headers": {"X-LOX24-AUTH-TOKEN": "valid_token"},
    "match_json": {
        "phone": SAMPLE_SMS_NOTIFICATION["phone"],
        "text": SAMPLE_SMS_NOTIFICATION["text"],
        "sender_id": "GHGA",
    }, 
}

LOX24_STATUS_CODES = [
        {"status_code": 201, "exception": None, },
        {"status_code": 401, "exception": SmsClient.AccountError, },
        {"status_code": 402, "exception": SmsClient.AccountError, },
        {"status_code": 403, "exception": SmsClient.AccountError, },
        {"status_code": 400, "exception": SmsClient.ResourceError, },
        {"status_code": 404, "exception": SmsClient.ResourceError, },
        {"status_code": 500, "exception": SmsClient.SystemError, },
        {"status_code": 502, "exception": SmsClient.SystemError, },
        {"status_code": 503, "exception": SmsClient.SystemError, },
        {"status_code": 504, "exception": SmsClient.SystemError, },
        {"status_code": 501, "exception": SmsClient.GeneralSmsException, },
    ]

def validate_performed_requests(httpx_mock: HTTPXMock):
    """Validate that all requests arrived at the mock are valid according to the Lox24 OpenAPI spec."""
    with open("tests/fixtures/lox24_openapi.json") as f:
        spec_dict = json.loads(f.read())
    spec = SchemaPath.from_dict(spec_dict)

    request_validator = V30RequestValidator(spec)
    requests_made = httpx_mock.get_requests()

    def httpx_to_requests(httpx_request: HttpxRequest) -> PreparedRequest:
        """OpenAPI package can only validate request.Request not httpx.Request"""
        return Request(
            method=httpx_request.method,
            url=str(httpx_request.url),
            headers=dict(httpx_request.headers),
            data=httpx_request.content or httpx_request.data or httpx_request.stream or None
        ).prepare()

    for req in requests_made:
         openapi_request = RequestsOpenAPIRequest(httpx_to_requests(req))
         request_validator.validate(openapi_request)



TEST_CORRELATION_ID = UUID("6914c8cd-1f18-43da-ac6c-c43cca3f36cc")
TEST_EVENT_ID = UUID("f8b1c5d2-3e4f-4a5b-8c6d-7e8f9a0b1c2d")

@pytest.fixture(autouse=True)
def correlation_id_fixture():
    """Provides a new correlation ID for each test case."""
    # we cannot use an async fixture with set_correlation_id(),
    # because it would run in a different context from the test
    token = correlation_id_var.set(TEST_CORRELATION_ID)
    yield
    correlation_id_var.reset(token)

async def test_sms_notification(joint_fixture: JointFixture, httpx_mock: HTTPXMock):
    """Basic test"""
    assert not joint_fixture.config.kafka_enable_dlq 
    httpx_mock.add_response(**LOX24_SMS_RESPONSE_MOCK, status_code=201)
    notification_event = make_sms_notification(SAMPLE_SMS_NOTIFICATION)

    await joint_fixture.kafka.publish_event(
        payload=notification_event.model_dump(),
        type_="sms_notification",
        topic=joint_fixture.config.notification_topic,
        event_id=TEST_EVENT_ID,
    )

    await joint_fixture.event_subscriber.run(forever=False)
    requests_made = httpx_mock.get_requests()
    assert len(requests_made) == 1
    request = requests_made[0]
    assert request.headers["host"] == "api.lox24.eu"
    assert request.method == "POST"
    request_data = json.loads(request.content.decode())
    assert request_data["phone"] == SAMPLE_SMS_NOTIFICATION["phone"]
    assert request_data["text"] == SAMPLE_SMS_NOTIFICATION["text"]

@pytest.mark.parametrize(
    "response",
    LOX24_STATUS_CODES
)
async def test_failures(response: dict, httpx_mock: HTTPXMock, joint_fixture: JointFixture):
    """Test that in case of a failure not SMS is sent"""
    assert joint_fixture.config.kafka_enable_dlq == False

    httpx_mock.add_response(**{**LOX24_SMS_RESPONSE_MOCK, "status_code": response["status_code"]})
    notification_event = make_sms_notification(SAMPLE_SMS_NOTIFICATION)

    await joint_fixture.kafka.publish_event(
        payload=notification_event.model_dump(),
        type_="sms_notification",
        topic=joint_fixture.config.notification_topic,
        event_id=TEST_EVENT_ID,
    )

    # Consume the event, which should throw an exception
    if response["exception"]:
        with pytest.raises(response["exception"]):
            await joint_fixture.event_subscriber.run(forever=False)
    else:
        await joint_fixture.event_subscriber.run(forever=False)
    # Assert a request has been made
    assert len(httpx_mock.get_requests()) == 1

    validate_performed_requests(httpx_mock)


@pytest.mark.parametrize(
    "response",
    LOX24_STATUS_CODES
)
async def test_dlq(response: dict, httpx_mock: HTTPXMock, joint_fixture_dlq: JointFixtureDlq):
    """Test that in case of a failure not SMS is sent"""
    assert joint_fixture_dlq.config.kafka_enable_dlq 

    httpx_mock.add_response(**{**LOX24_SMS_RESPONSE_MOCK, "status_code": response["status_code"]})
    notification_event = make_sms_notification(SAMPLE_SMS_NOTIFICATION)

    await joint_fixture_dlq.kafka.publish_event(
        payload=notification_event.model_dump(),
        type_="sms_notification",
        topic=joint_fixture_dlq.config.notification_topic,
        event_id=TEST_EVENT_ID,
    )

    async with joint_fixture_dlq.kafka.record_events(in_topic=joint_fixture_dlq.config.kafka_dlq_topic) as recorder:
        # Consume the event, which should error and get sent to the DLQ
        #with pytest.raises(response["exception"]):
        await joint_fixture_dlq.event_subscriber.run(forever=False)

    # Assert a request has been made
    assert len(httpx_mock.get_requests()) == 1

    validate_performed_requests(httpx_mock)

    # Assert that event has been added to the DLQ
    match response["status_code"]:
        case 201:
            assert len(recorder.recorded_events) == 0
        case _:
            assert len(recorder.recorded_events) == 1
            event = recorder.recorded_events[0]
            assert event.key == "test"
            assert event.payload == notification_event.model_dump()
