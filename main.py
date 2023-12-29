import asyncio
from bot.RClient import RubikaBot
from db.create_tbl import create_table
from dotenv import dotenv_values

env_variables = dotenv_values('.env')

api_id = env_variables.get('API_ID')
api_hash = env_variables.get('API_HASH')
if __name__ == '__main__':
    print("######------------------######")
    print("Running bot...")
    create_table()
    print("Database created and successfully connected...")
    print("######------------------######")
    client = RubikaBot(session='session', api_id=int(api_id), api_hash=api_hash)
    loop = asyncio.get_event_loop()
    loop.create_task(client.run_until_disconnected())
    # loop.create_task()
    loop.run_forever()
