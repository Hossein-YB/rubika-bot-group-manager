import datetime
from peewee import MySQLDatabase, Model, CharField, ForeignKeyField, BooleanField, DateTimeField
from playhouse.shortcuts import ReconnectMixin


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


database = ReconnectMySQLDatabase(database="rubika", host="127.0.0.1", user="rubika_user",
                                  password='rubika@919', port=3306)


class BaseModel(Model):
    class Meta:
        database = database


class BotSettings(BaseModel):
    """save bot base settings like main admin"""
    sudo_guid = CharField(max_length=250, unique=True)

    @classmethod
    def insert_sudo(cls, guid):
        user = cls.get_or_none(cls.sudo_guid == guid)
        if not user and guid:
            cls.create(guid=guid)
            return True
        else:
            return False

    @classmethod
    def get_sudo(cls):
        user = cls.select()
        if user:
            su = [sudo.sudo_guid for sudo in user]
            if len(su) > 1:
                return su
            else:
                return su[0]
        else:
            return None

    class Meta:
        db_table = 'bot_setting'


class Group(BaseModel):
    """A model to store information about the group in which the robot is active"""
    group_guid = CharField(max_length=250, unique=True)
    date_active = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def insert_group(cls, guid):
        group = cls.get_or_none(cls.group_guid == guid)
        if not group and guid:
            cls.create(group_guid=guid)
            return True
        else:
            return False

    @classmethod
    def get_groups_list(cls):
        groups = cls.select()
        groups_ids = []
        if groups:
            for group in groups:
                groups_ids.append(group.group_guid)
            return groups_ids
        else:
            return groups_ids


class GroupAdmin(BaseModel):
    """A model to store group admins guid """
    admin_guid = CharField(max_length=250)
    is_mein_admin = BooleanField(default=False)
    group_guid = ForeignKeyField(Group, Group.group_guid, on_delete="CASCADE")

    @classmethod
    def insert_group_admin(cls, a_guid, g_guid, is_sudo=False):
        group = cls.get_or_none(cls.admin_guid == a_guid, cls.group_guid == g_guid)
        if not group and a_guid and g_guid:
            cls.create(admin_guid=a_guid, group_guid=g_guid, is_mein_admin=is_sudo)
            return True
        else:
            return False

    @classmethod
    def delete_group_admin(cls, a_guid, g_guid):
        group = cls.get_or_none(cls.admin_guid == a_guid, cls.group_guid == g_guid)
        if group:
            group.delete_instance()
            return True
        else:
            return False

    @classmethod
    def get_groups_admins_list(cls):
        admins = cls.select()
        groups_admin = dict()
        if admins:
            for admin in admins:
                if not groups_admin.get(admin.group_guid.group_guid, None):
                    groups_admin[admin.group_guid.group_guid] = {'admins': [], "creator": ""}

                groups_admin[admin.group_guid.group_guid]['admins'].append(admin.admin_guid)
                if admin.is_mein_admin:
                    groups_admin[admin.group_guid.group_guid]['creator'] = admin.admin_guid

            return groups_admin
        else:
            return groups_admin

    @classmethod
    def get_group_admins(cls, group_guid):
        admins = cls.select(cls.group_guid == group_guid)
        list_admins = [ad.admin_guid for ad in admins]
        return list_admins


class GroupSettings(BaseModel):
    """A model to store group settings """
    names = {
        'گیف': "gif",
        'ویدیو': "video",
        'مخاطب': "contact",
        'موسیقی': "music",
        'ویس': "voice",
        'مکان': "location",
        'عکس': "image",
        'پست': "post",
        'استوری': "rubinostory",
        'لینک': "link",
        'منشن': "mention",
        'استیکر': "sticker",
        'نظرسنجی': "poll",
        'چت': "chat",
        'فروارد': "forwarded_from",
        'قفل گروه': "all_lock",
        'خوشامد': "welcome",
        'جوین': "join"
    }

    group_guid = ForeignKeyField(Group, Group.group_guid, on_delete="CASCADE")

    link = BooleanField(default=True)
    mention = BooleanField(default=True)
    welcome = BooleanField(default=True)
    join = BooleanField(default=True)

    gif = BooleanField(default=False)
    chat = BooleanField(default=False)
    video = BooleanField(default=False)
    contact = BooleanField(default=False)
    music = BooleanField(default=False)
    voice = BooleanField(default=False)
    location = BooleanField(default=False)
    image = BooleanField(default=False)
    post = BooleanField(default=False)
    sticker = BooleanField(default=False)
    poll = BooleanField(default=False)
    forwarded_from = BooleanField(default=False)
    rubinostory = BooleanField(default=False)
    all_lock = BooleanField(default=False)

    @classmethod
    def insert_group(cls, g_guid):
        setting = cls.get_or_none(cls.group_guid == g_guid)
        if not setting:
            setting = cls.create(group_guid=g_guid)
        else:
            return setting

    @classmethod
    def update_setting(cls, g_guid, setting_name, status):
        group = cls.get_or_none(cls.group_guid == g_guid)
        if group:
            setattr(group, setting_name, status)
            group.save()
        else:
            return None

    @classmethod
    def update_all(cls, guid, status=0):
        list_attr = cls.names.values()
        group_setting = cls.get_or_none(cls.group_guid == guid)
        if not group_setting:
            return False
        for attr in list_attr:
            setattr(group_setting, attr, status)
        group_setting.save()

    @classmethod
    def get_group_status(cls, guid):
        group_setting = cls.get_or_none(cls.group_guid == guid)
        if not group_setting:
            return False
        text = ""
        for key, val in cls.names.items():
            if getattr(group_setting, val):
                status = "✅"
            else:
                status = "❌ "

            text += f"{key}: {status} \n"

        return text
