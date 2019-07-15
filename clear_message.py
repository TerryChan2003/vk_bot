#!/usr/bin/python3
try:
    import sys
    from peewee import *
    from playhouse.postgres_ext import *

    db_handler = PostgresqlExtDatabase("vk_app")

    class BaseModel(Model):
        class Meta:
            database = db_handler

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

    operation = {
        "day": Users.update(message_today=0),
        "week": Users.update(message_week=0),
        "month": Users.update(message_month=0),
        "year": Users.update(message_year=0)
    }[sys.argv[-1]]
    operation.execute()
except Exception as e:
    with open("/root/log.txt", "a") as f:
        f.write(f"{e}")
