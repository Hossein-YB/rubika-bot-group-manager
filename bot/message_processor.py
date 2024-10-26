from __future__ import annotations
from rubpy.types import Updates
from db.models import Messages, Users


class MessageProcessor:
    async def check_rubika_text(self, bot, msg: Updates):
        if msg.text in bot.text.rubika_messages:
           await msg.delete_messages()

    async def message_manager(self, bot,  msg: Updates):
        user = await msg.get_author()
        group = await msg.get_object()
        text = msg.text
        if await self.check_rubika_text(bot, msg):
            return False

        file = msg.file_inline
        msg_type = 'text'
        if file:
            msg_type = msg.file_inline.type.lower()
            file = msg.file_inline.access_hash_rec

        u = Users.insert_user(user.user_guid, group.object_guid)
        m = Messages.insert_message(msg_type, group.object_guid, user.user_guid, text, file, )



