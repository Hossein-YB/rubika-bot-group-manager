from rubpy import Client, handlers, Message
from rubpy import models
from bot.connection import CConnection
from bot.tools import LINK_RE, MENTION
from db.models import Admin, Group, GroupAdmin, GroupSettings, Music
import re


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.dnd = None
        self.sudo = Admin.get_sudo()
        self.groups_id = Group.get_groups_list()
        self.groups_admins_list = GroupAdmin.get_groups_admins_list()
        self.group_delete_messages = []
        print(
            f"{'#---#' * 20}\nsudo -> {self.sudo}\ngroup -> {self.groups_id}\ngroups admins -> {self.groups_admins_list}\n{'#---#' * 20}")
        super().__init__(session, *args, **kwargs)

    async def upload(self, file: bytes, *args, **kwargs):
        return await self._connection.c_upload_file(file=file, *args, **kwargs)

    async def connect(self):
        self._connection = CConnection(client=self)

        if self._auth and self._private_key is not None:
            get_me = await self.get_me()
            self._guid = get_me.user.user_guid

        information = self._session.information()
        self._logger.info(f'the session information was read {information}')
        if information:
            self._auth = information[1]
            self._guid = information[2]
            self._private_key = information[4]
            if isinstance(information[3], str):
                self._user_agent = information[3] or self._user_agent

        return self

    async def normalize_admins(self, guid):
        admins = self.groups_admins_list.get(guid, None)
        if admins:
            admins = admins['admins']
        else:
            admins = []
        return admins

    async def help_bot(self, msg: Message):

        sender = msg.author_guid
        if msg.is_group and sender != self.sudo:
            guid = msg.object_guid
            admins = await self.normalize_admins(guid)
            if not admins or sender not in admins:
                return False
        with open("./bot/help.txt", "r", encoding='utf-8') as f:
            help = f.read()
        await msg.reply(help)

    async def set_sudo_admin_bot(self, msg: Message):
        guid = msg.author_guid
        if self.sudo:
            ad = await self.get_user_info(self.sudo)
            return await msg.reply(f"مدیر از قبل تنظیم شده است\n{ad.user.username}")

        if Admin.insert_admin(guid):
            self.sudo = guid
            await msg.reply("مدیر تنظیم شد.")
        else:
            await msg.reply("مشکلی رخ داد.")

    async def add_group_bot(self, msg: Message):
        sender = msg.author_guid
        if sender != self.sudo:
            return False
        guid_group = msg.object_guid
        if guid_group in self.groups_id and guid_group in self.groups_admins_list:
            return await msg.reply(f"گروه از قبل برای ربات تنظیم شده است.")

        if Group.insert_group(guid_group):
            self.groups_id.append(guid_group)
            GroupSettings.insert_group(guid_group)
            await msg.reply("گروه تنظیم شد.\nقفل های فعال لینک و منشن.\nدر حال دریافت مدیران ...")
        else:
            await msg.reply("گروه از قبل تنظیم شده است.\nدر حال به روزرسانی مدیران ...")

        return await self.update_group_admin(msg)

    async def update_group_admin(self, msg: Message):
        guid_group = msg.object_guid
        sender = msg.author_guid
        creator = None

        if self.groups_admins_list.get(guid_group, None):
            creator = self.groups_admins_list.get(guid_group, None)['creator']

        if sender != self.sudo or not sender != creator:
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

    async def get_lock_list(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False
        text = "لیست قفل های ربات:"
        for i in GroupSettings.names.keys():
            text += f"\n`!قفل {i}`\t !بازکردن {i}"
        await msg.reply(text)

    async def unlock_all(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False
        GroupSettings.update_all(guid, 0)
        return await msg.reply("همه قفل ها باز شدند")

    async def group_status(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False
        status = "وضعیت قفل های گروه به این ترتیب است:\n" + GroupSettings.get_group_status(guid)
        return await msg.reply(status)

    async def lock_group_setting(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False

        lock_name = msg.message.text.replace("!قفل", "").strip()
        en_lock_name = GroupSettings.names.get(lock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=True)
            await msg.reply(f"قفل {lock_name} فعال شد.")

    async def unlock_group_setting(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False
        unlock_name = msg.message.text.replace("!بازکردن", "").strip()
        en_lock_name = GroupSettings.names.get(unlock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=False)
            await msg.reply(f"قفل {unlock_name} غیر فعال شد.")

    async def ban_user(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
            return False

        user = await self.get_messages_by_ID(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)

        await self.ban_group_member(guid, user.user.user_guid)
        return await msg.reply(f"کاربر {user.user.first_name} با از گروه اخراج شد.")

    async def delete_all_messages(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or sender not in admins or sender != self.sudo:
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

    async def set_new_admin(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        creator = None

        if self.groups_admins_list.get(guid, None):
            creator = self.groups_admins_list.get(guid, None)

        if sender != self.sudo or sender != creator['creator']:
            return False

        user = await self.get_messages_by_ID(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.insert_group_admin(user.user.user_guid, guid)
        creator["admins"].append(user.user.user_guid)
        return await msg.reply(f"کاربر به لیست ادمین های ربات در گروه اضافه شد\nتعداد مدیران ربات در این گروه{len(creator['admins'])}")

    async def delete_admin(self, msg: Message):
        print(msg)
        guid = msg.object_guid
        sender = msg.author_guid
        creator = None

        if self.groups_admins_list.get(guid, None):
            creator = self.groups_admins_list.get(guid, None)

        if sender != self.sudo or sender != creator['creator']:
            return False

        user = await self.get_messages_by_ID(guid, msg.message.reply_to_message_id)
        user = user.messages[0].author_object_guid
        user = await self.get_user_info(user)
        GroupAdmin.delete_group_admin(user.user.user_guid, guid)
        creator["admins"].remove(user.user.user_guid)
        return await msg.reply(f"کاربر از لیست ادمین های ربات در گروه حذف شد\nتعداد مدیران ربات در این گروه{len(creator['admins'])}")

    async def manage_group_setting(self, msg: Message):
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

    async def run_until_disconnected(self):
        await self.connect()
        await self.start()
        
        self.add_handler(
            func=self.help_bot,
            handler=handlers.MessageUpdates(models.RegexModel('^راهنما$')))
        
        self.add_handler(
            func=self.set_sudo_admin_bot,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^setsudo$'), models.is_private))
        
        self.add_handler(
            func=self.add_group_bot,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^setgroup$'), models.is_group))
        
        self.add_handler(
            func=self.update_group_admin,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^به روزرسانی مدیران$'), models.is_group))
        
        self.add_handler(
            func=self.lock_group_setting,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^قفل '), models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.get_lock_list,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^لیست قفل ها$'), models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.unlock_group_setting,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^بازکردن '), models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.unlock_all,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^بازکردن همه'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.delete_all_messages,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^پاک کردن پیام ها'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.group_status,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^وضعیت'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.ban_user,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^بن'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^ارتقا مقام'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.set_new_admin,
            handler=handlers.MessageUpdates(models.RegexModel(pattern='^تنزل مقام'), models.is_group, models.object_guid in self.groups_id))
        
        self.add_handler(
            func=self.manage_group_setting,
            handler=handlers.MessageUpdates(models.object_guid in self.groups_id))

        return await super().run_until_disconnected()
