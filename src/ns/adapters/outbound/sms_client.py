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
#

"""Contains the sms client adapter"""

import logging

from httpx import HTTPStatusError, Response, post
from pydantic import BaseModel, Field, PositiveFloat, SecretStr
from pydantic_settings import BaseSettings

from ns.ports.outbound.sms_client import SmsClientPort

log = logging.getLogger(__name__)


class SmsAuthConfig(BaseModel):
    """Model to encapsulate SMS authentication details."""

    auth_token: SecretStr = Field(default=..., description="The authentication token")


class SmsClientConfig(BaseSettings):
    """Configuration details for the SmsClient"""

    sms_host: str = Field(default=..., description="The SMS gateway host to connect to")
    sms_port: int = Field(
        default=..., description="The port for the SMS gateway connection"
    )
    sms_auth: SmsAuthConfig | None = Field(default=None, description="")

    sms_timeout: PositiveFloat | None = Field(
        default=60,
        description=(
            "The maximum amount of time (in seconds) to wait for a connection to the"
            + " SMS gateway. If set to `None`, the operation will wait indefinitely."
        ),
    )


class SmsClient(SmsClientPort):
    """Concrete implementation of an SmsClientPort"""

    def __init__(self, *, config: SmsClientConfig):
        """Assign config, which should contain all needed info"""
        self._config = config
        self._headers: dict[str, str] = {}
        self._response: Response | None = None

    def _add_auth_headers(self) -> None:
        """Add authentication headers to the request headers."""
        if self._config.sms_auth:
            self._headers['X-LOX24-AUTH-TOKEN'] = self._config.sms_auth.auth_token.get_secret_value()
        else:
            raise ValueError("SMS authentication configuration is missing.")
    
    def _raise_for_status(self) -> None:
        """Raise an exception if the response indicates an error."""
        if self._response:
            try:
                self._response.raise_for_status()
            except HTTPStatusError as e:
                match e.response.status_code:
                    case 400 | 404:
                        raise SmsClientPort.ResourceError() from e
                    case 401 | 402 | 403:
                        raise SmsClientPort.AccountError() from e
                    case 500 | 502 | 503 | 504:
                        raise SmsClientPort.SystemError() from e
                    case _:
                        raise SmsClientPort.GeneralSmsException(
                            error_info=str(e)
                        ) from e

    def send_sms_message(self, message: dict) -> None:
        """Send an SMS message using the configured SMS gateway."""
        self._add_auth_headers()
        json_data = {
            "phone": message["phone"],
            "text": message["text"],
            "sender_id": "GHGA"
        }
        log.info(f"Sending SMS to {json_data['phone']}")
        self._response = post(f"https://{self._config.sms_host}/sms", headers=self._headers, json=json_data, timeout=100)
        self._raise_for_status()
