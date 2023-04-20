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

"""Contains a port for the notifier"""
from abc import ABC, abstractmethod

from ghga_event_schemas import pydantic_ as event_schemas


class NotifierPort(ABC):
    """Describes a notifier service in basic detail"""

    class InvalidEmailError(RuntimeError):
        """Raised when there's no valid email for sending with"""

        def __init__(self, *, email: str):
            message = (
                f"No valid sender email address configured. '{email}' isn't valid."
            )
            super().__init__(message)

    class TemplateConfigNotProvided(RuntimeError):
        """Raised when the required template is not configured"""

        def __init__(self, *, descriptor: str):
            message = f"The {descriptor} template is not configured!"
            super().__init__(message)

    class VariableNotSuppliedError(KeyError):
        """Raised when a template references a variable that isn't supplied"""

        def __init__(self, *, variable: str):
            message = f"Nothing supplied for template variable {variable}"
            super().__init__(message)

    class BadTemplateFormat(ValueError):
        """Raised when the html template contains improperly formatted content"""

        def __init__(self, *, problem: str):
            message = f"Problem with HTML template: {problem}"
            super().__init__(message)

    @abstractmethod
    async def send_notification(self, *, notification: event_schemas.Notification):
        """Sends out notifications based on the event details"""
        ...
