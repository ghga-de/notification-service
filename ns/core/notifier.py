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
"""Contains the concrete implementation of a NotifierPort"""

from email.message import EmailMessage
from string import Template

from ghga_event_schemas import pydantic_ as event_schemas

from ns.config import Config
from ns.ports.inbound.notifier import NotifierPort


class Notifier(NotifierPort):
    """Implementation of the Notifier Port"""

    def __init__(self, *, config: Config):
        """Initialize the Notifier with configured host, port, and so on"""
        self._config = config

    async def send_notification(self, *, notification: event_schemas.Notification):
        """Sends notifications based on the channel info provided (e.g. email addresses)"""
        raise NotImplementedError

    def _construct_email(self, *, notification: event_schemas.Notification):
        """Constructs an EmailMessage object from the contents of an email notification event"""
        message = EmailMessage()
        message["To"] = notification.recipient_email
        message["Cc"] = notification.email_cc
        message["Bcc"] = notification.email_bcc
        message["Subject"] = notification.subject

        # concatenate recipient name and plaintext body with generic greeting/closing
        plaintext_email = (
            f"Dear {notification.recipient_name},\n\n"
            + f"{notification.plaintext_body}\n\nWarm regards,\n\nThe GHGA Team"
        )
        message.set_content(plaintext_email)

        # create html version of email, replacing variables of $var format
        payload_as_dict = notification.dict()

        template = Template(self._config.email_template)

        try:
            html_email = template.substitute(payload_as_dict)
        except KeyError as err:
            raise self.VariableNotSuppliedError(variable=err.args[0]) from err
        except ValueError as err:
            raise self.BadTemplateFormat(problem=err.args[0]) from err

        # add the html version to the EmailMessage object
        message.add_alternative(html_email, subtype="html")

        return message
