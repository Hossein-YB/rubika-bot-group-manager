from .models import database, Admin, Group, GroupAdmin


def create_table():
    with database:
        database.create_tables([Admin, Group, GroupAdmin])
