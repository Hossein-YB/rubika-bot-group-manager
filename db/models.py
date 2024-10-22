import datetime
from peewee import MySQLDatabase, Model, CharField, ForeignKeyField, BooleanField, DateTimeField, IntegerField, \
    TextField, CompositeKey
from playhouse.shortcuts import ReconnectMixin

from bot.tools import error_writer


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


database = ReconnectMySQLDatabase(database="irpytho1_rubika_v_2", host="127.0.0.1", user="irpytho1_rubika_v2",
                                  password='rubika@v2', port=3333)


class BaseModel(Model):
    class Meta:
        database = database


class SudoBot(BaseModel):
    sudo_guid = CharField(max_length=250, unique=True)
    base_sudo = BooleanField(default=False)

    @classmethod
    def insert_sudo(cls, guid, base_sudo):
        user = cls.get_or_none(cls.sudo_guid == guid)
        if not user and guid:
            cls.create(sudo_guid=guid, base_sudo=base_sudo)
            return True
        else:
            return False

    @classmethod
    def get_list(cls):
        user = cls.select()
        if user:
            su = [sudo.sudo_guid for sudo in user]
            return su[0]
        else:
            return None

    @classmethod
    def get_main_su(cls):
        user = cls.get_or_none(cls.base_sudo == True)
        return user.sudo_guid


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
        if groups:
            return [group.group_guid for group in groups]
        else:
            return []


class Users(BaseModel):
    user_guid = CharField(max_length=250)
    is_special = BooleanField(default=False)
    warning = IntegerField(default=0)
    silent = BooleanField(default=False)
    group_guid = ForeignKeyField(Group, Group.group_guid, on_delete="CASCADE")

    @classmethod
    def insert_user(cls, user_guid, group_guid):
        try:
            cls.insert(user_guid=user_guid, group_guidn=group_guid)
        except Exception as e:
            error_writer(e, 'insert_user')
            pass

    @classmethod
    def get_user(cls, user_guid, group_guid):
        return cls.get_or_none(cls.user_guid == user_guid, cls.group_guid == group_guid)

    class Meta:
        database = database
        primary_key = CompositeKey('user_guid', 'group_guid')


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
    def admins_list(cls):
        admins = cls.select()
        groups_admin = {}

        if not admins:
            return groups_admin

        for admin in admins:

            if not groups_admin.get(admin.group_guid.group_guid, None):
                groups_admin[admin.group_guid.group_guid] = {'admins': [], "creator": ""}

            groups_admin[admin.group_guid.group_guid]['admins'].append(admin.admin_guid)

            if admin.is_mein_admin:
                groups_admin[admin.group_guid.group_guid]['creator'] = admin.admin_guid

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
                text += f"{key}: {status} \n"
            else:
                status = "❌ "
        return text


class Messages(BaseModel):
    m_type = CharField(max_length=10, )
    group = ForeignKeyField(Group, )
    user = ForeignKeyField(Users, )
    text = TextField(null=True)
    file_id = CharField(max_length=250, null=True)

