import os
import datetime
from peewee import *
from playhouse.postgres_ext import *

db_handler = PostgresqlExtDatabase("vk_app", autocommit=True, autorollback=True)


def get_time():
    today = datetime.datetime.today()
    return today.strftime("%d.%m.%Y, %H:%M:%S")


class BaseModel(Model):
    class Meta:
        database = db_handler


class BugList(BaseModel):
    id = PrimaryKeyField()
    from_id = IntegerField()
    text = CharField()
    result1 = CharField()
    result2 = CharField()
    data = TextField(default=get_time)
    status = IntegerField(default=0)
    priority = IntegerField()


class Ban_List(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )


class Report_Muted(BaseModel):
    user_id = IntegerField(unique=True)


class Helpers(BaseModel):
    id = PrimaryKeyField()
    user_id = IntegerField(unique=True)
    vig = IntegerField(default=0)
    reports = IntegerField(default=0)
    data = CharField(default=get_time)
    admin = CharField()

    class Meta:
        indexes = (
            (("user_id",), True),
        )


class Black_List(BaseModel):
    user_id = IntegerField(unique=True)

    class Meta:
        indexes = (
            (("user_id",), True),
        )


class Users(BaseModel):
    user_id = IntegerField()
    first_name = CharField()
    last_name = CharField()
    sex = IntegerField()
    message_today = IntegerField(default=1)
    message_week = IntegerField(default=1)
    message_month = IntegerField(default=1)
    message_year = IntegerField(default=1)
    photo_200 = CharField(default="", null=True)


class Chat_Info(BaseModel):
    chat_id = IntegerField(unique=True)
    title = CharField(default="")
    photo = CharField(default="")
    greeting = TextField(default="")
    akick = BooleanField(default=False)

    class Meta:
        indexes = (
            (("chat_id",), True),
        )

    @classmethod
    def get_item(cls, item, chat_id, default=None):
        chat = cls.get_or_none(chat_id=chat_id)
        if chat:
            return getattr(chat, item.name)
        else:
            return default


class ChatMembers(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()
    #chat_id = ForeignKeyField(Chat_Info, field="chat_id", backref="members")
    #user_id = ForeignKeyField(Users, field="user_id", backref="chats")

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )


class Admin_List(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()
    #chat_id = ForeignKeyField(Chat_Info, field="chat_id", backref="admins")
    #user_id = ForeignKeyField(Users, field="user_id", backref="chats_admin")
    level = IntegerField(default=0)

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )


class Service(BaseModel):
    user_id = IntegerField(unique=True)
    onboarding = BooleanField(default=True)


tables = [Admin_List, Ban_List, Report_Muted, Helpers, Black_List, Chat_Info, BugList, Users, ChatMembers, Service]
db_handler.create_tables(tables)


class DB_For_Users:
    def check_user(self, user_id):
        try:
            return Users.get(user_id=user_id)
        except:
            return None

    def add_user(self, user_id, first_name, last_name, sex, photo_200):
        return Users(user_id=user_id, first_name=first_name, last_name=last_name, sex=sex, photo_200=photo_200).save()

    def get_users(self, user_id):
        return Users.get_or_none(user_id=user_id)

    def update_users(self, user_id, params, rez):
        user = self.get_users(user_id)
        setattr(user, params, rez)
        user.save()


class DB_For_Helpers:
    def add_helper(self, user_id, admin):
        Helpers(user_id=user_id, admin=admin).save()

    def update_helpers(self, user_id, params, rez):
        helper = self.get_hstats(user_id)
        setattr(helper, params, rez)
        helper.save()

    def get_hstats(self, user_id):
        try:
            return Helpers.get(user_id=user_id)
        except:
            return False

    def del_helper(self, user_id):
        try:
            return Helpers.get(user_id=user_id).delete_instance()
        except:
            return False

    def get_helpers(self):
        return Helpers.select()


class DB_For_Admin_List:
    def add_admin(self, chat_id, user_id, level):
        admin = Admin_List.get_or_create(chat_id=chat_id, user_id=user_id, defaults={"level": 0})[0]
        admin.level = level
        admin.save()

    def add_service(self, user_id):
        Service.get_or_create(user_id=user_id)

    def get_admins(self, chat_id):
        return Admin_List.select().where(Admin_List.chat_id == chat_id)

    def get_level_admin(self, chat_id, user_id):
        return Admin_List.get_or_create(chat_id=chat_id, user_id=user_id, defaults={"level": 0})[0].level

    def remove_admin(self, chat_id, user_id) -> int:
        admin = Admin_List.get_or_create(chat_id=chat_id, user_id=user_id, defaults={"level": 0})[0]
        admin.level = 0
        admin.save()


class DB_For_Report_Muted:
    def add_muted_report(self, user_id):
        Report_Muted(user_id=user_id).save()

    def remove_muted_report(self, user_id):
        return Report_Muted.get(user_id=user_id).delete_instance()

    def get_muted_report(self):
        return Report_Muted.select()

    def check_muted_report(self, user_id):
        return Report_Muted.get_or_none(user_id=user_id)


class DB_For_Black_List:
    def check_black_list(self, user_id):
        try:
            return Black_List.get(user_id=user_id)
        except:
            return None

    def add_black_list(self, user_id):
        Black_List(user_id=user_id).save()

    def remove_black_list(self, user_id):
        try:
            return Black_List.get(user_id=user_id).delete_instance()
        except:
            return False

    def get_black_list(self):
        return Black_List.select()


class DB_For_Ban_List:
    def remove_ban(self, chat_id, user_id):
        try:
            return Ban_List.get(chat_id=chat_id, user_id=user_id).delete_instance()
        except:
            return False

    def check_ban(self, chat_id, user_id):
        try:
            return Ban_List.get_or_none(chat_id=chat_id, user_id=user_id)
        except:
            return None

    def add_ban(self, chat_id, user_id):
        Ban_List(chat_id=chat_id, user_id=user_id).save()


class DB_For_Chat_Info:
    def add_chat_info(self, chat_id):
        Chat_Info(chat_id=chat_id).save()

    def add_chat_infoex(self, chat_id, title, photo):
        Chat_Info(chat_id=chat_id, title=title, photo=photo).save()

    def set_akick(self, chat_id, params):
        chat = Chat_Info.get_or_create(chat_id=chat_id)[0]
        chat.akick = params
        chat.save()

    def update_greeting(self, chat_id, text):
        chat = Chat_Info.get_or_create(chat_id=chat_id)[0]
        chat.greeting = text
        chat.save()

    def update_title(self, chat_id, text):
        chat = Chat_Info.get_or_create(chat_id=chat_id)[0]
        chat.title = text
        chat.save()

    def get_greeting(self, chat_id):
        return Chat_Info.get_item(Chat_Info.greeting, chat_id, "")

    def get_akick(self, chat_id):
        return Chat_Info.get_item(Chat_Info.akick, chat_id)

    def get_chat_info(self, chat_id):
        return Chat_Info.get_item(Chat_Info.chat_id, chat_id, 0)

    def get_title(self, chat_id):
        return Chat_Info.get_item(Chat_Info.title, chat_id)

    def get_photo(self, chat_id):
        return Chat_Info.get_item(Chat_Info.photo, chat_id)

    def get_chat_infos(self):
        return Chat_Info.select()

    def check_chat(self, chat_id):
        return Chat_Info.get_or_none(chat_id=chat_id)

    def delete_chat(self, chat_id):
        Chat_Info.get(chat_id=chat_id).delete_instance()


class DB(DB_For_Admin_List, DB_For_Helpers, DB_For_Ban_List, DB_For_Report_Muted, DB_For_Chat_Info, DB_For_Black_List, DB_For_Users):
    ...
