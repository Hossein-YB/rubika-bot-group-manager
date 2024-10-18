from rubpy import Client, handlers, filters
from rubpy.types import Updates

from bot.utf8msg import Messages as MSG
from db.models import SudoBot, Group, GroupAdmin, GroupSettings

from bot.tools import LINK_RE, MENTION, error_writer
import re


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.text = MSG()
        self.sudo = SudoBot.get_main_su()  # guid sudo bot
        self.groups_id = Group.get_groups_list()  # bot groups
        self.admins_list = GroupAdmin.admins_list()  # a {group_guid={'admins': [], "creator": ""}, }
        print(
            f"{'#---#' * 20}\nsudo -> {self.sudo}\ngroup -> {self.groups_id}\ngroups admins ->"
            f" {self.admins_list}\n{'#---#' * 20}")
        super().__init__(session, *args, **kwargs)

    async def check_sender(self, msg: Updates, is_main=False):
        g_user = msg.author_guid
        group_admins = self.admins_list.get(msg.object_guid, None)

        if g_user == self.sudo:
            return True

        if not group_admins:
            return False

        if is_main and g_user == group_admins['creator']:
            return 'creator'

        if not is_main and g_user in group_admins['admins']:
            return True

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
        status = "وضعیت قفل های گروه به این ترتیب است:\n" + GroupSettings.get_group_status(msg.object_guid)
        return await msg.reply(status)

    async def ban_user(self, msg: Updates):
        check = await self.check_sender(msg)

        if not check:
            return False

        get_reply = await self.get_messages_by_id(msg.object_guid, msg.message.reply_to_message_id)
        get_reply = get_reply.messages[0] if len(get_reply.messages) > 0 else get_reply.messages
        user = await self.get_user_info(get_reply.author_object_guid)

        await self.delete_messages(msg.object_guid, [get_reply.message_id])
        await self.ban_group_member(msg.object_guid, user.user.user_guid)
        return await msg.reply(self.text.ban_user.format(user.user.first_name))

    async def delete_all_messages(self, msg: Updates):
        guid = msg.object_guid
        check = await self.check_sender(msg)

        if not check:
            return False

        await msg.reply("شروع پاکسازی ...")
        while True:
            messages = await self.get_messages_interval(guid, msg.message_id)
            if not messages.messages:
                break
            ids = []
            for message in messages.messages:
                ids.append(message.message_id)
            await self.delete_messages(guid, ids)

        return await self.send_message(guid, "تمام پیام ها پاک شدند")

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
        text = msg.message.text if msg.message.text else None
        m_type = msg.message.type.lower()

        g_guid = msg.object_guid
        g_user = msg.author_guid
        if g_guid not in self.groups_id:
            return False

        group_setting = GroupSettings.get_or_none(GroupSettings.group_guid == g_guid)
        if not group_setting:
            return False

        if group_setting.welcome and "از طریق لینک دعوت به گروه پیوست" in text:
            user = await msg.get_author(g_user)
            user_name = user.first_name
            await msg.repla(f"کاربر {user_name} به گروه خوش آمدید")

        if (
                (group_setting.chat and text and not msg.file_inline)
                or group_setting.all_lock
        ):
            return await msg.delete_messages()

        if (
                (group_setting.rubinostory and m_type == "rubinostory") or
                (group_setting.post and m_type == "rubinopost") or
                (group_setting.forwarded_from and msg.forwarded_from or msg.forwarded_no_link)
        ):
            return await msg.delete_messages()

        if msg.file_inline or msg.location or msg.sticker or msg.poll:
            if msg.file_inline:
                f_type = msg.file_inline.type.lower()
            else:
                f_type = msg.message.type.lower()
            setting = getattr(group_setting, f_type)
            if setting:
                return await msg.delete_messages()

        if text and (group_setting.link or group_setting.mention):
            links = re.findall(LINK_RE, text)
            mention = re.findall(MENTION, text)
            if links or mention:
                await msg.delete_messages()
            if links:
                await msg.delete_messages()
                await self.ban_group_member(g_guid, g_user)

        if (
                (
                        "را حذف کرد" in text or "گروه را ترک کرد" in text or "از طریق لینک دعوت به گروه پیوست" in text or "را اضافه کرد" in text)
        ):
            await msg.delete_messages()

    def run(self):
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
            handler=handlers.MessageUpdates(filters.RegexModel(pattern=re.compile('^حذف تاریخچه$')),
                                            filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^ارتقا مقام'), filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.delete_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^تنزل مقام'), filters.is_group, filters.object_guid in self.groups_id))

        self.add_handler(
            func=self.manage_group_setting,
            handler=handlers.MessageUpdates(filters.object_guid in self.groups_id))

        return super().run()
