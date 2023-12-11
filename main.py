import asyncio
from bot.RClient import RubikaBot

if __name__ == '__main__':
    client = RubikaBot(session='session')
    loop = asyncio.get_event_loop()
    loop.create_task(client.run_until_disconnected())
    loop.run_forever()
