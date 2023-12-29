from .models import database, Admin, Group, GroupAdmin, GroupSettings, Music


def create_table():
    with database:
        database.create_tables([Admin, Group, GroupAdmin, GroupSettings, Music])
