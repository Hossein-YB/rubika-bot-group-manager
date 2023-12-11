from peewee import SqliteDatabase, Model, CharField, ForeignKeyField

database = SqliteDatabase("bot_db.sqlite3")


class BaseModel(Model):
    class Meta:
        database = database


class Admin(BaseModel):
    guid = CharField(max_length=250, unique=True)


class Group(BaseModel):
    guid = CharField(max_length=250, unique=True)


class GroupAdmin(BaseModel):
    guid = CharField(max_length=250, unique=True)
    group_id = ForeignKeyField(Group, on_delete="CASCADE")

