from rubpy import Client, handlers, filters
from rubpy.types import Updates
from db.models import BotSettings, Group, GroupAdmin, GroupSettings

from bot.tools import LINK_RE, MENTION
import re


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.dnd = None
        self.sudo = BotSettings.get_sudo()
        self.groups_id = Group.get_groups_list()
        self.groups_admins_list = GroupAdmin.get_groups_admins_list()
        self.group_delete_messages = []
        
        print(
            f"{'#---#' * 20}\nsudo -> {self.sudo}\ngroup -> {self.groups_id}\ngroups admins -> {self.groups_admins_list}\n{'#---#' * 20}")
        
        super().__init__(session, *args, **kwargs)

    async def normalize_admins(self, guid):
        admins = self.groups_admins_list.get(guid, None)
        if admins:
            admins = admins['admins']
        else:
            admins = []
        return admins

    async def check_sender(self, msg: Updates):
        sender = msg.author_guid
        guid_group = msg.object_guid

        if sender == self.sudo:
            return True

        if not guid_group:
            return False

        group = self.groups_admins_list.get(guid_group, {'admins': []})
        if sender in group['admins']:
            return True
        else:
            return False

    async def check_creator(self,  msg: Updates):
        sender = msg.author_guid
        guid_group = msg.object_guid

        if sender == self.sudo:
            return True

        if not guid_group:
            return False

        group = self.groups_admins_list.get(guid_group, {'creator': ''})
        if sender is group['creator']:
            return True
        else:
            return False

    async def help_bot(self, msg: Updates, *args, **kwargs):
        check = await self.check_sender(msg)

        if not check:
            return False

        with open("./bot/help.txt", "r", encoding='utf-8') as f:
            help = f.read()
        return await msg.reply(help)

    async def set_sudo_admin_bot(self, msg: Updates, *args, **kwargs):
        guid = msg.author_guid
        if self.sudo:
            ad = await self.get_user_info(self.sudo)
            return await msg.reply(f"مدیر از قبل تنظیم شده است\n{ad.user.username}")

        if BotSettings.insert_sudo(guid):
            self.sudo = guid
            await msg.reply("مدیر تنظیم شد.")
        else:
            await msg.reply("مشکلی رخ داد.")

    async def add_group_bot(self, msg: Updates, *args, **kwargs):
        sender = msg.author_guid
        guid_group = msg.object_guid
        check = await self.check_sender(msg)

        if not check:
            return False

        if guid_group in self.groups_id and guid_group in self.groups_admins_list:
            return await msg.reply(f"گروه از قبل برای ربات تنظیم شده است.")

        if Group.insert_group(guid_group):
            self.groups_id.append(guid_group)
            GroupSettings.insert_group(guid_group)
            await msg.reply("گروه تنظیم شد.\nقفل های فعال لینک و منشن.\nدر حال دریافت مدیران ...")
        else:
            await msg.reply("گروه از قبل تنظیم شده است.\nدر حال به روزرسانی مدیران ...")

        return await self.update_group_admin(msg)

    async def update_group_admin(self, msg: Updates, *args, **kwargs):
        guid_group = msg.object_guid
        sender = msg.author_guid
        creator = None

        check = await self.check_creator(msg)

        if not check:
            return False

        admins = await self.get_group_admin_members(guid_group)
        new_group_admin = {'admins': [], 'creator': None}
        for admin in admins.in_chat_members:
            is_sudo = False
            if admin.join_type == "Creator":
                new_group_admin['creator'] = admin.member_guid
                is_sudo = True
            GroupAdmin.insert_group_admin(admin.member_guid, guid_group, is_sudo)
            new_group_admin['admins'].append(admin.member_guid)
        self.groups_admins_list[guid_group] = new_group_admin
        print(self.groups_admins_list)
        await msg.reply("به روز رسانی با موفقیت انجام شد.")

    async def get_lock_list(self, msg: Updates, *args, **kwargs):
        check = await self.check_creator(msg)

        if not check:
            return False

        text = "لیست قفل های ربات:"
        for i in GroupSettings.names.keys():
            text += f"\n`قفل {i}`\t بازکردن {i}"
        await msg.reply(text)

    async def unlock_all(self, msg: Updates, *args, **kwargs):
        check = await self.check_creator(msg)

        if not check:
            return False

        GroupSettings.update_all(msg.object_guid, 0)
        return await msg.reply("همه قفل ها باز شدند")

    async def group_status(self, msg: Updates, *args, **kwargs):
        check = await self.check_sender(msg)

        if not check:
            return False
        status = "وضعیت قفل های گروه به این ترتیب است:\n" + GroupSettings.get_group_status(msg.object_guid)
        return await msg.reply(status)

    async def lock_group_setting(self, msg: Updates, *args, **kwargs):
        check = await self.check_sender(msg)

        if not check:
            return False

        lock_name = msg.message.text.replace("قفل", "").strip()
        en_lock_name = GroupSettings.names.get(lock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=True)
            await msg.reply(f"قفل {lock_name} فعال شد.")

    async def unlock_group_setting(self, msg: Updates, *args, **kwargs):
        check = await self.check_sender(msg)

        if not check:
            return False
        unlock_name = msg.message.text.replace("بازکردن", "").strip()
        en_lock_name = GroupSettings.names.get(unlock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=False)
            await msg.reply(f"قفل {unlock_name} غیر فعال شد.")

    async def ban_user(self, msg: Updates, *args, **kwargs):
        check = await self.check_sender(msg)

        if not check:
            return False

        user = await self.get_messages_by_id(msg.object_guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)

        await self.ban_group_member(msg.object_guid, user.user.user_guid)
        return await msg.reply(f"کاربر {user.user.first_name} با از گروه اخراج شد.")

    async def delete_all_messages(self, msg: Updates, *args, **kwargs):
        guid = msg.object_guid
        check = await self.check_sender(msg)

        if not check:
            return False

        if guid not in self.group_delete_messages:
            self.group_delete_messages.append(guid)
        else:
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

    async def set_new_admin(self, msg: Updates, *args, **kwargs):
        check = await self.check_creator(msg)

        if not check:
            return False

        guid = msg.object_guid
        user = await self.get_messages_by_id(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.insert_group_admin(user.user.user_guid, guid)
        self.groups_admins_list["admins"].append(user.user.user_guid)
        return await msg.reply(f"کاربر به لیست ادمین های ربات در گروه اضافه شد\nتعداد مدیران ربات در این گروه{len(self.groups_admins_list['admins'])}")

    async def delete_admin(self, msg: Updates, *args, **kwargs):
        check = await self.check_creator(msg)
        if not check:
            return False
        guid = msg.object_guid

        user = await self.get_messages_by_id(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.delete_group_admin(user.user.user_guid, guid)
        self.groups_admins_list["admins"].remove(user.user.user_guid)
        return await msg.reply(f"کاربر از لیست ادمین های ربات در گروه حذف شد\nتعداد مدیران ربات در این گروه{len(self.groups_admins_list['admins'])}")

    async def manage_group_setting(self, msg: Updates, *args, **kwargs):
        text = msg.message.text if msg.message.text else None
        m_type = msg.message.type.lower()

        guid = msg.object_guid
        sender = msg.author_guid

        admins = await self.normalize_admins(guid)
        if not admins or sender in admins or sender == self.sudo:
            return False

        group_setting = GroupSettings.get_or_none(GroupSettings.group_guid == guid)
        if not group_setting:
            return False

        if group_setting.welcome and "از طریق لینک دعوت به گروه پیوست" in text:
            user = await msg.get_author(sender)
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
                await self.ban_group_member(guid, sender)

        if (
                ("را حذف کرد" in text or "گروه را ترک کرد" in text or "از طریق لینک دعوت به گروه پیوست" in text or "را اضافه کرد" in text)
        ):
            await msg.delete_messages()

    def run(self):
        self.add_handler(
            func=self.help_bot,
            handler=handlers.MessageUpdates(filters.RegexModel('^راهنما$')))
        
        self.add_handler(
            func=self.set_sudo_admin_bot,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^setsudo$'), filters.is_private))
        
        self.add_handler(
            func=self.add_group_bot,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^setgroup$'), filters.is_group))
        
        self.add_handler(
            func=self.update_group_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^به روزرسانی مدیران$'), filters.is_group))
        
        self.add_handler(
            func=self.lock_group_setting,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^قفل '), filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.get_lock_list,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^لیست قفل ها$'), filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.unlock_group_setting,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^بازکردن '), filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.unlock_all,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^بازکردن همه'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.delete_all_messages,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^پاک کردن پیام ها'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.group_status,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^وضعیت'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.ban_user,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^بن'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^ارتقا مقام'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(filters.RegexModel(pattern='^تنزل مقام'), filters.is_group, filters.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.manage_group_setting,
            handler=handlers.MessageUpdates(filters.object_guid in self.groups_id))

        return super().run()
