from playhouse.migrate import *
from peewee import *
from playhouse.postgres_ext import *

db_handler = PostgresqlExtDatabase("vk_app")
migrator = PostgresqlMigrator(db_handler)

migrate(
    migrator.add_column("chat_info", "golos", BooleanField(default=False))
)
