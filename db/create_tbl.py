from .models import database, Admin, Group, GroupAdmin, GroupSettings


def create_table():
    with database:
        database.create_tables([Admin, Group, GroupAdmin, GroupSettings])
