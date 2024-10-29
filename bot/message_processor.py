from __future__ import annotations

import re

from rubpy.types import Updates
from db.models import Messages, Users, Group, GroupSettings, GroupAdmin
from re import findall
from bot.tools import LINK_RE, MENTION


class MessageProcessor:

    async def get_info_username(self, bot, msg: Updates, mention):
        info = await bot.get_info(username=mention)
        if info.type.lower() == "user":
            return True
        else:
            return False

    async def check_link(self, bot, msg: Updates, setting: GroupSettings, user, group):
        link = findall(LINK_RE, msg.text, )
        mention = findall(MENTION, msg.text, )
        del_status = False
        if link and setting.link:
            del_status = True
        if mention and setting.mention:
            st = await self.get_info_username(bot, msg, mention[0])
            del_status = True
            if st and not setting.user_username:
                del_status = False

        if del_status:
            await msg.delete_messages()
            await bot.ban_group_member(group, user.user_guid)
            return await msg.reply(bot.text.delete_user.format(user.first_name, bot.text.send_link,))

    async def check_rubika_text(self, bot, msg: Updates, setting: GroupSettings):
        t = "|".join(bot.text.rubika_messages)
        f = re.findall(f"({t})", msg.text)
        if f and setting.join:
            await msg.delete_messages()

    async def check_files(self, bot, msg: Updates, setting: GroupSettings, user, group, file, msg_type):
        n = getattr(setting, msg_type)
        if n:
            await msg.delete_messages()
            await msg.reply(bot.text.delete_message_t.format(user.first_name, msg_type))

    async def del_post(self, bot, msg: Updates, setting, user, msg_type):
        n = getattr(setting, msg_type)
        if n:
            await msg.delete_messages()
            await msg.reply(bot.text.delete_message_t.format(user.first_name, msg_type))

    async def manage_group(self, bot,  msg: Updates):
        user = await msg.get_author()
        message_id = msg.message_id
        group = msg.object_guid
        setting = GroupSettings.get_or_none(GroupSettings.group_guid == group)

        text = msg.text

        if text:
            if await self.check_rubika_text(bot, msg, setting):
                return False

        file = msg.file_inline

        msg_type = msg.message.type.lower()
        print(msg_type)
        if file:
            msg_type = msg.file_inline.type.lower()
            file = msg.file_inline.access_hash_rec

        if msg_type in ['rubinopost', 'rubinostory']:
            text = f"rubinopost or story"
            return await self.del_post(bot, msg, setting, user, msg_type)

        u = Users.insert_user(user.user_guid, group)
        m = Messages.insert_message(message_id, msg_type, group, user.user_guid, text, file, )

        if not setting:
            return False

        if await bot.check_sender(msg, is_admin=True):
            return False

        if text:
            await self.check_link(bot, msg, setting, user, group)

        if file:
            await self.check_files(bot, msg, setting, user, group, file, msg_type)


