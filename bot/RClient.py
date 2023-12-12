# rubpy imports
from rubpy import Client, handlers, Message
from rubpy.structs import models

# database models imports
from db.models import Admin, Group, GroupAdmin


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.sudo = Admin.get_sudo()
        self.groups_id = []
        super().__init__(session, *args, **kwargs)

    async def check_bot(self, msg: Message):
        print(msg)
        await msg.reply(f"Hi {self.name} bot is online")

    async def set_sudo_admin(self, msg: Message):
        guid = msg.author_guid
        if self.sudo:
            ad = await self.get_user_info(self.sudo)
            return await msg.reply(f"مدیر از قبل تنظیم شده است\n{ad.user.username}")

        if Admin.insert_admin(guid):
            self.sudo = guid
            await msg.reply("مدیر تنظیم شد.")
        else:
            await msg.reply("مشکلی رخ داد.")
        

    async def run_until_disconnected(self):
        await self.start()
        # self.add_handler(self.check_bot, handlers.MessageUpdates(models.is_private()))
        self.add_handler(self.set_sudo_admin, handlers.MessageUpdates(models.RegexModel('^!setsudo$') and models.is_private()))
        return await super().run_until_disconnected()

