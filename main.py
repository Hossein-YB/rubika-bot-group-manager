import asyncio
from bot.RClient import RubikaBot
from db.create_tbl import create_table
if __name__ == '__main__':
    print("######------------------######")
    print("Running bot...")
    create_table()
    print("Database created and successfully connected...")
    print("######------------------######")
    client = RubikaBot(session='session')
    loop = asyncio.get_event_loop()
    loop.create_task(client.run_until_disconnected())
    loop.run_forever()
    