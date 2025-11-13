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
"""Contains the smtp client port"""

from abc import ABC, abstractmethod


class SmsClientPort(ABC):
    """Abstract description of an SMS client that can send messages"""
    
    class SystemError(RuntimeError):
        """Raised when we fail to log in"""

        def __init__(self):
            message = "Contact the LOX24 support"
            super().__init__(message)

    class ResourceError(RuntimeError):
        """Raised when we fail to log in"""

        def __init__(self):
            message = "Failed to authenticate."
            super().__init__(message)
    class AccountError(RuntimeError):
        """Raised when we fail to log in"""

        def __init__(self):
            message = "Failed to authenticate."
            super().__init__(message)

    class GeneralSmsException(Exception):
        """Raised by other errors (not failed connection or failed login)"""

        def __init__(self, error_info: str):
            message = (
                f"Encountered an issue while attempting to send SMS: {error_info}"
            )
            super().__init__(message)

    @abstractmethod
    def send_sms_message(self, message: dict):
        """Sends an SMS message"""
        ...
