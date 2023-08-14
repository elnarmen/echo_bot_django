from django.db import models
from contextvars import ContextVar

from django_tg_bot_framework.models import (
    BaseStateMachineDump,
    TgUserProfileMixin,
)

# Will be initialized with current conversation object by state machine runner before states methods run.
conversation_var: ContextVar['Conversation'] = ContextVar('conversation_var')


class Conversation(BaseStateMachineDump, TgUserProfileMixin):
    tg_chat_id = models.CharField(
        'Id чата в Tg',
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Id чата в Tg, где пользователь общается с ботом.',
    )

    class Meta:
        verbose_name = "Диалог"
        verbose_name_plural = "Диалоги"
        constraints = [
            *BaseStateMachineDump._meta.constraints,
            *TgUserProfileMixin._meta.constraints,
        ]
