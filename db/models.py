from peewee import SqliteDatabase, Model, CharField, ForeignKeyField

database = SqliteDatabase("bot_db.sqlite3")


class BaseModel(Model):
    class Meta:
        database = database


class Admin(BaseModel):
    guid = CharField(max_length=250, unique=True)

    @classmethod
    def insert_admin(cls, guid):
        user = cls.get_or_none(cls.guid == guid)
        if not user and guid:
            cls.create(guid=guid)
            return True
        else:
            return False

    @classmethod
    def get_sudo(cls):
        user = cls.get_or_none()
        if user:
            return user.guid
        else:
            return None


class Group(BaseModel):
    guid = CharField(max_length=250, unique=True)


class GroupAdmin(BaseModel):
    guid = CharField(max_length=250, unique=True)
    group_id = ForeignKeyField(Group, on_delete="CASCADE")

