from django_tg_bot_framework import BaseState, Router, InteractiveState
from tg_api import (
    Message,
    SendMessageRequest,
    tg_types,
    SyncTgClient,
    raise_for_tg_response_status,
)

from .models import conversation_var


router = Router()


@router.register('/')
class RootState(InteractiveState):
    def enter_state(self) -> BaseState | None:
        SendMessageRequest(
            text='Вы перешли в состояние RootState `/`.',
            chat_id=conversation_var.get().tg_chat_id,
        ).send()

    def react_on_message(self, message: Message) -> BaseState | None:
        echo_text = message.text or '`пусто`'
        SendMessageRequest(
            text=f'Эхо: {echo_text}',
            chat_id=message.chat.id,
        ).send()

    def react_on_inline_keyboard(self, message: Message, pressed_button_payload: str) -> BaseState | None:
        echo_text = pressed_button_payload or '`пусто`'
        SendMessageRequest(
            text=f'Эхо: {echo_text}',
            chat_id=message.chat.id,
        ).send()


@router.register('/start/')
class StartCommandState(InteractiveState):
    def enter_state(self) -> BaseState | None:
        SendMessageRequest(
            text='Вы ввели команду `/start`. Пришлите любое сообщение, чтобы попасть в состояния RootState `/`.',
            chat_id=conversation_var.get().tg_chat_id,
        ).send()

    def react_on_message(self, message: Message) -> BaseState | None:
        echo_text = message.text or '`пусто`'
        SendMessageRequest(
            text=f'Состояние:\b{self.state_class_locator}\nЭхо:\n{echo_text}',
            chat_id=message.chat.id,
        ).send()
        return router.locate('/')

    def react_on_inline_keyboard(self, message: Message, pressed_button_payload: str) -> BaseState | None:
        echo_text = pressed_button_payload or '`пусто`'
        SendMessageRequest(
            text=f'Состояние:\b{self.state_class_locator}\nЭхо:\n{echo_text}',
            chat_id=message.chat.id,
        ).send()
