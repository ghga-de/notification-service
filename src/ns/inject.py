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

"""DI functions."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from ghga_service_commons.utils.context import asyncnullcontext
from hexkit.providers.akafka.provider import KafkaEventSubscriber

from ns.adapters.inbound.akafka import EventSubTranslator
from ns.adapters.outbound.smtp_client import SmtpClient
from ns.config import Config
from ns.core.notifier import Notifier
from ns.ports.inbound.notifier import NotifierPort


@asynccontextmanager
async def prepare_core(*, config: Config) -> AsyncGenerator[NotifierPort, None]:
    """Constructs and initializes all core components and their outbound dependencies."""
    smtp_client = SmtpClient(config=config)
    notifier = Notifier(config=config, smtp_client=smtp_client)
    yield notifier


def prepare_core_with_override(
    *, config: Config, notifier_override: Optional[NotifierPort] = None
):
    """Resolve the notifier context manager based on config and override (if any)."""
    return (
        asyncnullcontext(notifier_override)
        if notifier_override
        else prepare_core(config=config)
    )


@asynccontextmanager
async def prepare_event_subscriber(
    *,
    config: Config,
    notifier_override: Optional[NotifierPort] = None,
) -> AsyncGenerator[KafkaEventSubscriber, None]:
    """Construct and initialize an event subscriber with all its dependencies.
    By default, the core dependencies are automatically prepared but you can also
    provide them using the notifier_override parameter.
    """
    async with prepare_core_with_override(
        config=config, notifier_override=notifier_override
    ) as notifier:
        event_sub_translator = EventSubTranslator(
            notifier=notifier,
            config=config,
        )

        async with KafkaEventSubscriber.construct(
            config=config, translator=event_sub_translator
        ) as event_subscriber:
            yield event_subscriber