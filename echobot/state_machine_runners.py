from contextvars import ContextVar
from typing import Optional
import logging
from pydantic import ValidationError, BaseModel

from django.db import transaction
from django.conf import settings

from tg_api import Update, SyncTgClient, Message
from django_tg_bot_framework import UnknownStateClassLocatorError, Router, BaseState, StateMachine, set_contextvar
from tg_api.tg_types import CallbackQuery

from .models import Conversation


logger = logging.getLogger('django_tg_bot_framework')


def restore_state_safely(router: Router, conversation: Conversation) -> BaseState | None:
    if not conversation.state_class_locator:
        return

    state_params = conversation.state_params or {}
    cleaned_state_params = {key: value for key, value in state_params.items() if key != 'state_class_locator'}

    try:
        return router.locate(
            conversation.state_class_locator,
            **cleaned_state_params,
        )
    except UnknownStateClassLocatorError:
        logger.warning(
            'Reset unknown state class locator %s for Conversation tg_chat_id=%s',
            conversation.state_class_locator,
            conversation.tg_chat_id,
        )
    except ValidationError as exc:
        logger.warning(
            'Reset invalid state %s for Conversation tg_chat_id=%s',
            exc.json(),
            conversation.tg_chat_id,
        )


class ConversationSummary(BaseModel):
    tg_username: str
    tg_user_id: int
    tg_chat_id: int

    @classmethod
    def from_update(cls, update: Update) -> Optional['ConversationSummary']:
        if update.message and update.message.from_:
            # In case regular message or reply keyboard
            return cls(
                tg_username=update.message.from_.username or '',
                tg_user_id=update.message.from_.id,
                tg_chat_id=update.message.chat.id,
            )

        if update.callback_query and update.callback_query.from_:
            # In case user pressed inline keyboard button
            return cls(
                tg_username=update.callback_query.from_.username or '',
                tg_user_id=update.callback_query.from_.id,
                tg_chat_id=update.callback_query.message.chat.id,
            )


def process_tg_update(update: Update, *, router: Router, conversation_var: ContextVar[Conversation]):
    conversation_summary = ConversationSummary.from_update(update)
    if not conversation_summary:
        return

    tg_username, tg_user_id, tg_chat_id = (
        conversation_summary.tg_username,
        conversation_summary.tg_user_id,
        conversation_summary.tg_chat_id,
    )

    with transaction.atomic(durable=True):

        conversation, created = Conversation.objects.select_for_update().get_or_create(
            tg_chat_id=tg_chat_id,
            defaults={
                'tg_user_id': tg_user_id,
                'tg_username': tg_username,
            },
        )

        if conversation.tg_username != tg_username or conversation.tg_user_id != tg_user_id:
            Conversation.objects.filter(tg_chat_id=tg_chat_id).update(
                tg_user_id=tg_user_id,
                tg_username=tg_username,
            )

        restored_state = restore_state_safely(router, conversation)

        state_machine = StateMachine(
            current_state=restored_state or router.locate('/'),
        )

        with set_contextvar(conversation_var, conversation):
            with SyncTgClient.setup(token=settings.ENV.TG.BOT_TOKEN):
                if not restored_state:
                    state_machine.reenter_state()

                state_machine.process(update)

        Conversation.objects.filter(tg_chat_id=tg_chat_id).update(
            state_class_locator=state_machine.current_state.state_class_locator,
            state_params=state_machine.current_state.dict(exclude={'state_class_locator'}),
        )
