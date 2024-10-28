import asyncio.exceptions
import re

from rubpy import Client, handlers, filters
from rubpy.enums import ParseMode
from rubpy.types import Updates

from bot.utf8msg import Messages as MSG
from bot.message_processor import MessageProcessor
from bot.tools import LINK_RE, MENTION, error_writer

from db.models import SudoBot, Group, GroupAdmin, GroupSettings, Users, Messages


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.message_processor = MessageProcessor()
        self.text = MSG()
        self.sudo = SudoBot.get_main_su()  # guid sudo bot
        self.groups_id = Group.get_groups_list()  # bot groups
        self.admins_list = GroupAdmin.admins_list()  # a {group_guid={'admins': [], "creator": ""}, }
        print(
            f"{'#---#' * 20}\nsudo -> {self.sudo}\ngroup -> {self.groups_id}\ngroups admins ->"
            f" {self.admins_list}\n{'#---#' * 20}")
        super().__init__(session, *args, **kwargs)

    async def check_sender(self, msg: Updates, is_creator=False, is_admin=False):
        g_user = msg.author_guid
        group_admins = self.admins_list.get(msg.object_guid, None)

        if g_user == self.sudo:
            return True

        if not group_admins:
            raise ValueError("admin list is Empty.")

        if is_creator:
            if g_user == group_admins['creator']:
                return True

        if is_admin:
            if g_user in group_admins['admins']:
                return True

        return False

    async def help_bot(self, msg: Updates):
        return await msg.reply(self.text.hellp)

    async def add_new_group(self, msg: Updates):
        g_user = msg.author_guid
        g_group = msg.object_guid
        check = await self.check_sender(msg, True)

        if not check:
            return False
        try:
            if Group.insert_group(g_group):
                GroupSettings.insert_group(g_group)
                self.groups_id.append(g_group)
                await msg.reply(self.text.group_added)
            else:
                await msg.reply(self.text.group_exists)
        except Exception as e:
            error_writer(e, "add_group")
            return await msg.reply(self.text.error_add_group)

        return await self.update_group_admin(msg)

    async def update_group_admin(self, msg: Updates):
        g_group = msg.object_guid
        g_user = msg.author_guid
        is_sudo = False

        check = await self.check_sender(msg, True)
        if not check:
            return False

        admins = await self.get_group_admin_members(g_group)
        new_group_admin = {'admins': [], 'creator': ''}

        for admin in admins.in_chat_members:
            if admin.join_type.lower() == "creator":
                new_group_admin['creator'] = admin.member_guid
                is_sudo = True
            GroupAdmin.insert_group_admin(admin.member_guid, g_group, is_sudo)
            new_group_admin['admins'].append(admin.member_guid)

        self.admins_list[g_group] = new_group_admin
        await msg.reply(self.text.update_admins)

    async def get_lock_list(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False

        text = self.text.lock_list
        for i in GroupSettings.names.keys():
            text += self.text.add_lock.format(i, i)

        await msg.reply(text)

    async def lock_group_setting(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False

        lock_name = msg.message.text.replace(self.text.lock, "").strip()
        en_lock_name = GroupSettings.names.get(lock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=True)
            await msg.reply(self.text.active_lock.format(lock_name))

    async def unlock_group_setting(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False
        unlock_name = msg.message.text.replace(self.text.un_lock, "").strip()
        en_lock_name = GroupSettings.names.get(unlock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=False)
            await msg.reply(self.text.deactive_lock.format(unlock_name))

    async def unlock_all(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False

        GroupSettings.update_all(msg.object_guid, 0)
        return await msg.reply("همه قفل ها باز شدند")

    async def group_status(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False
        t1 = t2 = ''
        status = self.text.group_status + GroupSettings.get_group_status(msg.object_guid)
        admins = await self.get_group_admin_members(msg.object_guid)
        for admin in admins.in_chat_members:
            if admin.join_type.lower() == 'creator':
                t1 += f"\n<a href='https://rubika.ir/{admin.username}'>{admin.first_name}</a>"
            else:
                t2 += f"\n<a href='https://rubika.ir/{admin.username}'>{admin.first_name}</a>"

        status = status + self.text.group_creator + t1
        status = status + self.text.group_admins + t2
        return await self.send_message(msg.object_guid, status, reply_to_message_id=msg.message_id,
                                       parse_mode=ParseMode.HTML)

    async def ban_user(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check or not msg.message.reply_to_message_id:
            return False

        get_reply = await self.get_messages_by_id(msg.object_guid, msg.message.reply_to_message_id)
        get_reply = get_reply.messages[0] if len(get_reply.messages) > 0 else get_reply.messages
        user = await self.get_user_info(get_reply.author_object_guid)
        if not user:
            return await msg.reply(self.text.cant_find_user)

        if user in self.admins_list[msg.object_guid]['admins']:
            return await msg.reply(self.text.cant_ban_admin)

        await self.delete_messages(msg.object_guid, [get_reply.message_id])
        await self.ban_group_member(msg.object_guid, user.user.user_guid)
        return await msg.reply(self.text.ban_user.format(user.user.first_name))

    async def delete_all_messages(self, msg: Updates):
        guid = msg.object_guid
        text = msg.text.replace("حذف", '').strip()

        if not text.isnumeric():
            return False
        text = int(text)
        if text == 0 or not text:
            return False

        check = await self.check_sender(msg)

        if not check:
            return False
        num = 0
        await msg.reply(self.text.start_delete)
        while True:
            messages = await self.get_messages_interval(guid, msg.message_id)
            if not messages.messages:
                break
            ids = []
            for message in messages.messages:
                ids.append(message.message_id)
            await self.delete_messages(guid, ids)
            num += len(ids)
            if num == text:
                break
        return await self.send_message(guid, self.text.delete_message.format(num))

    async def set_new_admin(self, msg: Updates):

        check = await self.check_sender(msg, True)
        if not check:
            return False

        guid = msg.object_guid
        user = await self.get_messages_by_id(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.insert_group_admin(user.user.user_guid, guid)
        self.admins_list[msg.object_guid]["admins"].append(user.user.user_guid)
        return await msg.reply(
            f"کاربر به لیست ادمین های ربات در گروه اضافه شد\nتعداد مدیران ربات در این گروه{len(self.admins_list[msg.object_guid]['admins'])}")

    async def delete_admin(self, msg: Updates):
        check = await self.check_sender(msg, True)
        if not check:
            return False
        guid = msg.object_guid
        user = await self.get_messages_by_id(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.delete_group_admin(user.user.user_guid, guid)
        self.admins_list[msg.object_guid]["admins"].remove(user.user.user_guid)
        return await msg.reply(
            f"کاربر از لیست ادمین های ربات در گروه حذف شد\nتعداد مدیران ربات در این گروه{len(self.admins_list[msg.object_guid]['admins'])}")

    async def manage_group_setting(self, msg: Updates):
        await self.message_processor.message_manager(self, msg)

    async def run(self):
        self.add_handler(
            func=self.help_bot,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^راهنما$'))))

        self.add_handler(
            func=self.add_new_group,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^setgroup$')),
                                            filters.is_group))

        self.add_handler(
            func=self.update_group_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^بروزرسانی مدیران$')),
                                            filters.is_group))

        self.add_handler(
            func=self.get_lock_list,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^لیست قفل ها$')),
                                            filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.lock_group_setting,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^قفل ')),
                                            filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.unlock_group_setting,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^بازکردن ')),
                                            filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.unlock_all,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^بازکردن همه$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.group_status,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^وضعیت$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.ban_user,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^بن$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.delete_all_messages,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^حذف \d*$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^ارتقا مدیر$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.delete_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^عزل مدیر$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.manage_group_setting,
            handler=handlers.MessageUpdates(filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.manage_group_setting,
            handler=handlers.ChatUpdates(filters.object_guid in self.groups_id))

        await self.start()
        while True:
            try:
                await self.get_updates()
            except asyncio.exceptions.TimeoutError as e:
                pass

