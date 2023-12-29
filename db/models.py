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
    def delete_group_admin(cls, a_guid, g_guid):
        group = cls.get_or_none(cls.guid == a_guid, cls.group_id == g_guid)
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
                if not groups_admin.get(admin.group_id.guid, None):
                    groups_admin[admin.group_id.guid] = {'admins': [], "creator": ""}

                groups_admin[admin.group_id.guid]['admins'].append(admin.guid)
                if admin.is_sudo:
                    groups_admin[admin.group_id.guid]['creator'] = admin.guid

            return groups_admin
        else:
            return groups_admin


class GroupSettings(BaseModel):
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
    }
    group_guid = ForeignKeyField(Group, Group.guid, on_delete="CASCADE")
    gif = BooleanField(default=False)
    chat = BooleanField(default=False)
    video = BooleanField(default=False)
    contact = BooleanField(default=False)
    music = BooleanField(default=False)
    voice = BooleanField(default=False)
    location = BooleanField(default=False)
    image = BooleanField(default=False)
    post = BooleanField(default=False)
    link = BooleanField(default=True)
    mention = BooleanField(default=True)
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
                status = "فعال"
            else:
                status = "باز "

            text += f"وضعیت قفل {key} {status} است\n"

        return text


class Music(BaseModel):
    music_name = CharField(max_length=1240)
    access_hash = CharField(max_length=255)
    search = CharField(max_length=500)
    file_id = CharField(max_length=100)

    @classmethod
    def insert_music(cls, music_name, access_hash, search, file_id):
        cls.create(music_name=music_name, access_hash=access_hash, search=search, file_id=file_id)
