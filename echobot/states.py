from django_tg_bot_framework import BaseState, Router, InteractiveState
from tg_api import (
    Message,
    SendMessageRequest,
)
from apps.tg_bot_conversation.models import conversation_var


router = Router()


@router.register('/start/')
class FirstState(InteractiveState):
    def enter_state(self) -> BaseState | None:
        SendMessageRequest(
            text='''Вы находитесь в стейте FirstState. 
Напишите что нибудь, чтобыперейти в EchoBot.''',
            chat_id=conversation_var.get().tg_chat_id,
        ).send()

    def react_on_message(self, message: Message) -> BaseState | None:
        return router.locate('/second/')


@router.register('/second/')
class EchoBot(InteractiveState):
    def enter_state(self) -> BaseState | None:
        SendMessageRequest(
            text=f'Вы перешли в эхо бота. Пишите',
            chat_id=conversation_var.get().tg_chat_id,
        ).send()

    def react_on_message(self, message: Message) -> BaseState | None:
        if message.text == '/start':
            return router.locate('/start/')
        SendMessageRequest(
            text=message.text,
            chat_id=conversation_var.get().tg_chat_id,
        ).send()
