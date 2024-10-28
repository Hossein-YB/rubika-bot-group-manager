from __future__ import annotations
from rubpy.types import Updates
from db.models import Messages, Users, Group, GroupSettings, GroupAdmin
from re import findall
from bot.tools import LINK_RE, MENTION


class MessageProcessor:

    async def manage_group_message(self, bot,  msg: Updates, setting: GroupSettings):
        pass

    async def check_link(self, bot, msg: Updates, setting: GroupSettings):
        link = findall(LINK_RE, msg.text, )
        mention = findall(MENTION, msg.text, )
        if link and setting.link:
            await msg.delete_messages()
        if mention and setting.mention:
            await msg.delete_messages()

    async def check_rubika_text(self, bot, msg: Updates, setting: GroupSettings):
        for i in bot.text.rubika_messages:
            if msg.text in i and setting.join:
                print(i)
                print(msg.text)
                await msg.delete_messages()
        return True

    async def message_update(self, bot,  msg: Updates):
        print(msg)
        user = await msg.get_author()
        group = await msg.get_object()
        setting = GroupSettings.get_or_none(GroupSettings.group_guid == group.group_guid)

        text = msg.text
        if await self.check_rubika_text(bot, msg, setting):
            return False

        file = msg.file_inline
        msg_type = 'text'
        if file:
            msg_type = msg.file_inline.type.lower()
            file = msg.file_inline.access_hash_rec

        u = Users.insert_user(user.user_guid, group.object_guid)
        m = Messages.insert_message(msg_type, group.object_guid, user.user_guid, text, file, )

        if not setting:
            return False

    async def chat_update(self, bot,  msg: Updates):
        print(msg)

