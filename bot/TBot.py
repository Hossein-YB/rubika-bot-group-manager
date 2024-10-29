import asyncio
import re

from telethon import TelegramClient, events, errors

regex_dl_music = r"/dl_\S*"


def dl_link(text):
    dls = re.findall(regex_dl_music, text)
    return dls


class TeleBot(TelegramClient):
    def __init__(self, name: str, api_id, api_hash):
        self.bot_username = "ahangifybot"
        self.bot_username1 = "melobot"
        last_send = 0
        super().__init__(name, api_id, api_hash)

    async def signin(self):
        if await self.is_user_authorized():
            print('Login')
            return True
        print("telegram login")
        phone = input("Enter phone: ")
        await self.send_code_request(phone, force_sms=False)
        value = input("Enter login code: ")
        try:
            me = await self.sign_in(phone, code=value)
        except errors.SessionPasswordNeededError:
            password = input("Enter password: ")
            me = await self.sign_in(password=password)
        print('Login')

    async def search_music(self, music_name):
        path = None
        async with self.conversation(self.bot_username) as conv:
            await conv.send_message(message=music_name)
            res = await conv.wait_event(events.NewMessage(self.bot_username), timeout=60)
            dls = dl_link(res.text)
            try:
                x = await self.send_message(self.bot_username, dls[-1])
                res = await conv.wait_event(events.NewMessage(self.bot_username, func=lambda e: e.audio), timeout=5)
                path = await res.download_media()
                conv.cancel()
            except asyncio.TimeoutError:
                conv.cancel()
                pass
        return path

    async def search_melo(self, music_name):
        path = None
        async with self.conversation(self.bot_username1) as conv:
            await conv.send_message(message=music_name)
            res = await conv.wait_event(events.NewMessage(self.bot_username1), timeout=60)
            key_text = ''

            for keys in res.reply_markup.rows[0:]:
                for e in keys.buttons:
                    if 'تبلیغ' not in e.text:
                        key_text = e.text
                        break

            if not key_text:
                return False

            await asyncio.sleep(1)
            await conv.send_message(message=key_text)
            key_text = ''
            res = await conv.wait_event(events.NewMessage(self.bot_username1), timeout=60)
            for keys in res.reply_markup.rows[0:]:
                for e in keys.buttons[-1]:
                    if 'دانلود' in e.text:
                        key_text = e.text
                        break
            await asyncio.sleep(1)
            await conv.send_message(message=key_text)
            import pdb;pdb.set_trace()
            try:
                res = await conv.wait_event(events.NewMessage(self.bot_username, func=lambda e: e.audio), timeout=10)
                path = await res.download_media()
                conv.cancel()
            except asyncio.TimeoutError:
                conv.cancel()
                pass
        return path

    async def get_list(self, music_name):
        l_m = ''
        async with self.conversation(self.bot_username) as conv:
            await conv.send_message(message=music_name)
            res = await conv.wait_event(events.NewMessage(self.bot_username), timeout=60)
            t1 = res.text.split('ــ ـ ـ ـ ـ ـ ـ ـ ـ ـ ـ')
            t1 = t1[-1].split('----------------------------------')
            for i in t1:
                if 'مدیریت آسان موزیک های تلگرام' not in i:
                    l_m += i + "\n"
            conv.cancel()
        return l_m

    async def download_music(self, code):
        path = None
        async with self.conversation(self.bot_username) as conv:
            await conv.send_message(message=code)
            try:
                res = await conv.wait_event(events.NewMessage(self.bot_username, func=lambda e: e.audio), timeout=5)
                path = await res.download_media()
                conv.cancel()
            except asyncio.TimeoutError:
                conv.cancel()
                pass
        return path
