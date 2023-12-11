from rubpy import Client, handlers, Message
from rubpy.structs import models
import asyncio


class RubikaBot(Client):
    def __init__(self, session: str, *args, **kwargs):
        self.name = "__name__"
        super().__init__(session, *args, **kwargs)

    async def check_bot(self, msg: Message):
        print(msg)
        await msg.reply(f"Hi {self.name} bot is online")

    async def run_until_disconnected(self):
        await self.start()
        self.add_handler(self.check_bot, handlers.MessageUpdates(models.is_private()))
        return await super().run_until_disconnected()

