from pdb import set_trace

from peewee import SqliteDatabase, Model, CharField, ForeignKeyField, BooleanField

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

    @classmethod
    def insert_group(cls, guid):
        group = cls.get_or_none(cls.guid == guid)
        if not group and guid:
            cls.create(guid=guid)
            return True
        else:
            return False

    @classmethod
    def get_groups_list(cls):
        groups = cls.select()
        groups_ids = []
        if groups:
            for group in groups:
                groups_ids.append(group.guid)
            return groups_ids
        else:
            return groups_ids


class GroupAdmin(BaseModel):
    guid = CharField(max_length=250, unique=True)
    is_sudo = BooleanField(default=False)
    group_id = ForeignKeyField(Group, Group.guid, on_delete="CASCADE")

    @classmethod
    def insert_group_admin(cls, a_guid, g_guid, is_sudo=False):
        group = cls.get_or_none(cls.guid == a_guid, cls.group_id == g_guid)
        if not group and a_guid and g_guid:
            cls.create(guid=a_guid, group_id=g_guid, is_sudo=is_sudo)
            return True
        else:
            return False

    @classmethod
    def get_groups_admins_list(cls):
        admins = cls.select()
        groups_admin = dict()
        if admins:
            set_trace()
            for admin in admins:
                if not groups_admin.get(admin.group_id.guid, None):
                    groups_admin[admin.group_id.guid] = {'admins': [], "creator": ""}

                groups_admin[admin.group_id.guid]['admins'].append(admin.guid)
                if admin.is_sudo:
                    groups_admin[admin.group_id.guid]['creator'] = admin.guid

            return groups_admin
        else:
            return groups_admin
