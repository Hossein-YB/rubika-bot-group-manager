from pdb import set_trace

from rubpy import Client, handlers, Message
from rubpy.structs import models

from db.models import Admin, Group, GroupAdmin, GroupSettings
import re


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.sudo = Admin.get_sudo()
        self.groups_id = Group.get_groups_list()
        self.groups_admins_list = GroupAdmin.get_groups_admins_list()
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

    async def help_bot(self, msg: Message):
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
        text = "لیست قفل های ربات:"
        for i in GroupSettings.names.keys():
            text += f"\n`!قفل {i}`"
        await msg.reply(text)

    async def lock_group_setting(self, msg: Message):
        guid = msg.object_guid
        sender = msg.author_guid
        admins = await self.normalize_admins(guid)
        if not admins or len(admins) == 0 or sender not in admins:
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
        if not admins or len(admins) == 0 or sender not in admins:
            return False
        unlock_name = msg.message.text.replace("!بازکردن", "").strip()
        en_lock_name = GroupSettings.names.get(unlock_name, False)
        if en_lock_name:
            GroupSettings.update_setting(msg.object_guid, setting_name=en_lock_name, status=False)
            await msg.reply(f"قفل {unlock_name} غیر فعال شد.")

    async def manage_group_setting(self, msg: Message):
        text = msg.message.text if msg.message.text else None
        m_type = msg.message.type.lower()
        print(text, m_type)

        guid = msg.object_guid
        sender = msg.author_guid

        admins = await self.normalize_admins(guid)
        if not admins or len(admins) == 0 or sender in admins:
            return False

        group_setting = GroupSettings.get_or_none(GroupSettings.group_guid == guid)
        if not group_setting:
            return False

        if group_setting.post and m_type == "rubinopost":
            return await msg.delete_messages()

        if msg.file_inline:
            f_type = msg.file_inline.type.lower()
            setting = getattr(group_setting, f_type)
            if setting:
                await msg.delete_messages()

        if text and (group_setting.link or group_setting.mention):
            link_re = re.compile(
                "((http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?|([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)"
            )
            finds = re.findall(link_re, text)
            if finds:
                await msg.delete_messages()

    async def run_until_disconnected(self):
        await self.start()

        self.add_handler(
            self.help_bot,
            handlers.MessageUpdates(models.RegexModel('^!help$'))
        )

        self.add_handler(
            self.set_sudo_admin_bot,
            handlers.MessageUpdates(models.RegexModel(pattern='^!setsudo$'), models.is_private)
        )

        self.add_handler(
            self.add_group_bot,
            handlers.MessageUpdates(models.RegexModel(pattern='^!setgroup$'), models.is_group)
        )

        self.add_handler(
            self.update_group_admin,
            handlers.MessageUpdates(models.RegexModel(pattern='^!updateadmins$'), models.is_group)
        )

        self.add_handler(
            self.lock_group_setting,
            handlers.MessageUpdates(models.RegexModel(pattern='^!قفل '), models.object_guid in self.groups_id)
        )
        self.add_handler(
            self.get_lock_list,
            handlers.MessageUpdates(models.RegexModel(pattern='^!لیست قفل ها$'), models.object_guid in self.groups_id)
        )
        self.add_handler(
            self.unlock_group_setting,
            handlers.MessageUpdates(models.RegexModel(pattern='^!بازکردن '), models.object_guid in self.groups_id)
        )

        self.add_handler(
            self.manage_group_setting,
            handlers.MessageUpdates(models.is_group, models.object_guid in self.groups_id)
        )

        return await super().run_until_disconnected()
