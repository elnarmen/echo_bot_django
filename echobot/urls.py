from functools import partial

from django.urls import path
from django.conf import settings
from django_tg_bot_framework.views import process_webhook_call

from .states import router
from apps.tg_bot_conversation.models import conversation_var
from apps.tg_bot_conversation.statemachine_runners import process_tg_update

app_name = 'tg_bot'

tg_bot_token = settings.TG_BOT_TOKEN

urlpatterns = [
    path(
        '',
        process_webhook_call,
        kwargs={
            'process_update': partial(
                process_tg_update,
                router=router,
                conversation_var=conversation_var,
                tg_bot_token=tg_bot_token
            ),
        },
        name='process_webhook_call',
    ),
]
