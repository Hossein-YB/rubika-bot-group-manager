from db.models import database, SudoBot, Group, GroupAdmin, GroupSettings, Users, Messages


def create_table():
    with database:
        database.create_tables(models=(SudoBot, Group, GroupAdmin, GroupSettings, Users))
        SudoBot.insert_sudo('u0FnZcm0ad0aba287aee1a53dc845d7c', True)
