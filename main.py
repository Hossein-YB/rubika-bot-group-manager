import asyncio

from bot.RClient import RubikaBot
from db.create_tbl import create_table


if __name__ == '__main__':
    print("######------------------######")
    print("Running bot...")
    create_table()
    print("Database created and successfully connected...")
    print("######------------------######")
    client = RubikaBot(session='session', display_welcome=False)
    asyncio.run(client.run())

    
    