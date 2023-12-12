# rubpy imports
from rubpy import Client, handlers, Message
from rubpy.structs import models

# database models imports
from db.models import Admin, Group, GroupAdmin


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.sudo = Admin.get_sudo()
        self.groups_id = Group.get_groups_list()
        super().__init__(session, *args, **kwargs)

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
        if guid_group in self.groups_id:
            return await msg.reply(f"گروه از قبل برای ربات تنظیم شده است.")

        if Group.insert_group(guid_group):
            self.groups_id.append(guid_group)
            await msg.reply("گروه تنظیم شد.")
        else:
            await msg.reply("مشکلی رخ داد.")


    async def run_until_disconnected(self):
        await self.start()
        self.add_handler(self.help_bot, handlers.MessageUpdates(models.RegexModel('^!help$')))
        self.add_handler(self.set_sudo_admin_bot, handlers.MessageUpdates((models.RegexModel('^!setsudo$') & models.is_private())))
        self.add_handler(self.add_group_bot, handlers.MessageUpdates((models.RegexModel('^!setgroup$') & models.is_group())))
        return await super().run_until_disconnected()

