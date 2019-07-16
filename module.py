import os
import datetime
from peewee import *
from playhouse.postgres_ext import *

db_handler = PostgresqlExtDatabase("vk_app", autocommit=True, autorollback=True)

# db_handler = SqliteDatabase("base1.db")
# db_handler = PooledSqliteDatabase("base1.db")


def get_time():
    today = datetime.datetime.today()
    return today.strftime("%d.%m.%Y, %H:%M:%S")


class BaseModel(Model):
    class Meta:
        database = db_handler


class Reports(BaseModel):
    id = PrimaryKeyField()
    user_id = IntegerField()
    chat_id = IntegerField()
    text = TextField()
    vtime = TextField(default=get_time)
    helper = TextField(default="")
    otext = TextField(default="")
    otime = TextField(default="")


class BugList(BaseModel):
    id = PrimaryKeyField()
    from_id = IntegerField()
    text = CharField()
    result1 = CharField()
    result2 = CharField()
    data = TextField(default=get_time)
    status = IntegerField(default=0)
    priority = IntegerField()


class Admin_List(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()
    level = IntegerField(default=0)

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )


class Ban_List(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )


class Refer_Switch(BaseModel):
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
    avatar = CharField(default="https://vk.com/images/support15_budda.png")

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
    user_id=IntegerField(unique=True)
    first_name=CharField()
    last_name=CharField()
    sex=IntegerField()
    message_today=IntegerField(default = 1)
    message_week=IntegerField(default = 1)
    message_month=IntegerField(default = 1)
    message_year=IntegerField(default = 1)
    photo_200=CharField(default = "", null = True)

class ChatMembers(BaseModel):
    chat_id=IntegerField()
    user_id=IntegerField()

    class Meta:
        indexes=(
            (("chat_id", "user_id"), True),
        )

class Chat_Info(BaseModel):
    chat_id = IntegerField(unique=True)
    title = CharField(default="")
    photo = CharField(default="")
    greeting = TextField(default="")
    akick = BooleanField(default=False)
    warn_enabled = IntegerField(default=0)
    warn_max = IntegerField(default=3)
    group_check = IntegerField(default=0)
    whitelist = ArrayField(default=[])
    antimat = BooleanField(default=False)

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

class Warns(BaseModel):
    chat_id = IntegerField()
    user_id = IntegerField()
    count = IntegerField()

    class Meta:
        indexes = (
            (("chat_id", "user_id"), True),
        )

class Service(BaseModel):
    user_id = IntegerField(unique=True)
    onboarding = BooleanField(default=True)


tables = [Admin_List, Ban_List, Report_Muted, Helpers, Black_List, Chat_Info, BugList, Users, ChatMembers, Service, Reports, Warns, Refer_Switch]
db_handler.create_tables(tables)

class DB_For_Refer_Switch:
    def switch_refer(self, chat_id, user_id):
        try:
            Refer_Switch.get(chat_id=chat_id, user_id=user_id).delete_instance()
            return True
        except:
            Refer_Switch(chat_id=chat_id, user_id=user_id).save()
            return False
    
    def check_refer(self, chat_id, user_id):
        try:
            Refer_Switch.get(chat_id=chat_id, user_id=user_id)
            return False
        except:
            return True
    

class DB_For_Warns:
    def add_warn(self, chat_id, user_id):
        w = Warns.get_or_create(chat_id=chat_id, user_id=user_id, defaults=dict(count=0))[0]
        if w.count + 1 < self.get_warn_max(chat_id):
            w.count += 1
            w.save()
            return w
        else:
            w.count = 0
            w.save()
            return False

    def sub_warn(self, chat_id, user_id):
        w = Warns.get_or_create(chat_id=chat_id, user_id=user_id, defaults=dict(count=0))[0]
        if w.count > 0:
            w.count -= 1
            w.save()
            return w
        else:
            return False

    def clear_warn(self, chat_id, user_id):
        w = Warns.get_or_create(chat_id=chat_id, user_id=user_id, defaults=dict(count=0))[0]
        if w.count:
            w.count = 0
            w.save()
            return w
        else:
            return False

    def get_warns(self, chat_id):
        return Warns.select().where(Warns.chat_id==chat_id, Warns.count>0)

class DB_For_Reports:
    def add_report(self, user_id, chat_id, text):
        r = Reports(user_id=user_id, chat_id=chat_id, text=text)
        r.save()
        return r

    def update_reports(self, id, params, rez):
        report = self.check_report(id)
        setattr(report, params, rez)
        report.save()

    def check_report(self, id):
        try:
            return Reports.get(id = id)
        except:
            return None
    def get_reports(self):
        return Reports.select()

class DB_For_Users:
    def add_service(self, user_id):
        Service.get_or_create(user_id=user_id)

    def del_service(self, user_id):
        return Service.get(user_id=user_id).delete_instance()

    def check_user(self, user_id):
        try:
            return Users.get(user_id = user_id)
        except:
            return None

    def add_user(self, user_id, first_name, last_name, sex, photo_200):
        return Users(user_id=user_id, first_name = first_name, last_name = last_name, sex = sex, photo_200=photo_200).save()

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
            return Helpers.get(user_id = user_id)
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
        admin = Admin_List.get_or_none(chat_id=chat_id, user_id=user_id)
        if admin:
            admin.level = level
            admin.save()
        else:
            Admin_List(chat_id=chat_id, user_id=user_id, level=level).save()

    def get_admins(self, chat_id):
        return Admin_List.select().where(Admin_List.chat_id == chat_id)

    def get_level_admin(self, chat_id, user_id):
        r = Admin_List.get_or_none(chat_id=chat_id, user_id=user_id)
        if r:
            return r.level
        else:
            return 0

    def remove_admin(self, chat_id, user_id):
        admin = Admin_List.get_or_none(chat_id=chat_id, user_id=user_id)
        if admin:
            return admin.delete_instance()
        else:
            return 0


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
            return Ban_List.get_or_none(chat_id = chat_id, user_id = user_id)
        except:
            return None

    def add_ban(self, chat_id, user_id):
        Ban_List(chat_id=chat_id, user_id=user_id).save()

    def get_ban(self):
        return Ban_List.select()

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
    
    def update_photo(self, chat_id, photo):
        chat = Chat_Info.get_or_create(chat_id=chat_id)[0]
        chat.photo = photo
        chat.save()
    
    def get_whitelist(self, chat_id):
        return Chat_Info.get_item(Chat_Info.whitelist, chat_id, [])

    def get_greeting(self, chat_id):
        return Chat_Info.get_item(Chat_Info.greeting, chat_id, "")

    def get_akick(self, chat_id):
        return Chat_Info.get_item(Chat_Info.akick, chat_id)

    def get_chat_info(self, chat_id):
        return Chat_Info.get_item(Chat_Info.chat_id, chat_id, 0)
    
    def get_chat_group_check(self, chat_id):
        return Chat_Info.get_item(Chat_Info.group_check, chat_id, 0)
    
    def get_chat_antimat(self, chat_id):
        return Chat_Info.get_item(Chat_Info.antimat, chat_id, False)
    
    def switch_chat_antimat(self, chat_id):
        chat = Chat_Info.get(chat_id=chat_id)
        chat.antimat = not chat.antimat
        chat.save()
        return chat.antimat

    def set_chat_group_check(self, chat_id, group_check):
        chat = Chat_Info.get(chat_id=chat_id)
        chat.group_check = group_check
        chat.save()

    def get_title(self, chat_id):
        return Chat_Info.get_item(Chat_Info.title, chat_id)

    def get_photo(self, chat_id):
        return Chat_Info.get_item(Chat_Info.photo, chat_id)

    def get_warn_max(self, chat_id):
        return Chat_Info.get_item(Chat_Info.warn_max, chat_id)

    def get_warn_enabled(self, chat_id):
        return Chat_Info.get_item(Chat_Info.warn_enabled, chat_id)
    
    def add_whitelist(self, chat_id, user_id):
        chat = Chat_Info.get(chat_id=chat_id)
        if not chat.whitelist:
            chat.whitelist = []
        if user_id not in chat.whitelist:
            chat.whitelist.append(user_id)
            chat.save()
            return True
        else:
            return False
    
    def remove_whitelist(self, chat_id, user_id):
        chat = Chat_Info.get(chat_id=chat_id)
        if not chat.whitelist:
            chat.whitelist = []
        if user_id in chat.whitelist:
            chat.whitelist.remove(user_id)
            chat.save()
            return True
        else:
            return False

    def set_warn_max(self, chat_id, count):
        chat = Chat_Info.get(chat_id=chat_id)
        chat.warn_max = count
        chat.save()

    def set_warn_enabled(self, chat_id):
        chat = Chat_Info.get(chat_id=chat_id)
        chat.warn_enabled = int(not bool(chat.warn_enabled))
        chat.save()
        return chat.warn_enabled

    def get_chat_infos(self):
        return Chat_Info.select()

    def check_chat(self, chat_id):
        return Chat_Info.get_or_none(chat_id=chat_id)

    def delete_chat(self, chat_id):
        Chat_Info.get(chat_id=chat_id).delete_instance()


class DB(DB_For_Admin_List, DB_For_Helpers, DB_For_Ban_List, DB_For_Report_Muted, DB_For_Chat_Info, DB_For_Black_List, DB_For_Users, DB_For_Reports, DB_For_Warns, DB_For_Refer_Switch):
    ...
