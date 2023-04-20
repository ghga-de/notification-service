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
"""Contains the smtp client port"""
from abc import ABC, abstractmethod
from email.message import EmailMessage


class SmtpClientPort(ABC):
    """Abstract description of an SMTP client that can send email"""

    class ConnectionError(RuntimeError):
        """To be raised when testing the connection fails"""

        def __init__(self):
            message = "Did not receive 250 status from connection test check."
            super().__init__(message)

    class FailedLoginError(RuntimeError):
        """Raised when we fail to log in"""

        def __init__(self):
            message = "Failed to log in."
            super().__init__(message)

    @abstractmethod
    def send_email_message(self, message: EmailMessage):
        """Sends an email message"""
        ...
