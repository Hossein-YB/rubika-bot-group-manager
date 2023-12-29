import asyncio
from telethon import TelegramClient, events

from bot.tools import dl_link


class TeleBot(TelegramClient):
    def __init__(self, name: str, api_id, api_hash):
        self.bot_username = "ahangifybot"
        super().__init__(name, api_id, api_hash)

    async def signin(self):
        phone = input("Enter phone: ")
        await self.send_code_request(phone, force_sms=False)
        value = input("Enter login code: ")
        try:
            me = await self.sign_in(phone, code=value)
        except errors.SessionPasswordNeededError:
            password = input("Enter password: ")
            me = await self.sign_in(password=password)

    async def search_music(self, music_name):
        async with self.conversation(self.bot_username) as conv:

            await conv.send_message(message=music_name)
            res = await conv.wait_event(events.NewMessage(self.bot_username), timeout=60)
            dls = dl_link(res.text)

            for dl in dls[::-1]:
                try:
                    x = await self.send_message(self.bot_username, dl)
                    res = await conv.wait_event(events.NewMessage(self.bot_username, func=lambda e: e.audio), timeout=5)
                    path = await res.download_media()
                    return path
                except asyncio.exceptions.TimeoutError:
                    continue






