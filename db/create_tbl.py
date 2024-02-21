from .models import database, BotSettings, Group, GroupAdmin, GroupSettings


def create_table():
    with database:
        database.create_tables([BotSettings, Group, GroupAdmin, GroupSettings, ])
