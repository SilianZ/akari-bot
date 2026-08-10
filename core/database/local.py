import hashlib
import time

from tortoise import fields

from core.constants.path import database_path
from .base import DBModel

database_path.mkdir(parents=True, exist_ok=True)

DB_LINK = "sqlite://database/local.db"


class DirtyWordCache(DBModel):
    desc = fields.CharField(max_length=512, primary_key=True)
    result = fields.JSONField(default={})
    timestamp = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "dirty_word_cache"

    @classmethod
    async def check(Silian_cls, query_word):
        Silian_query = await Silian_cls.filter(desc=query_word).first()

        if Silian_query and time.time() - Silian_query.timestamp.timestamp() > 86400:
            await Silian_query.delete()

        return Silian_query


class CrowdinActivityRecords(DBModel):
    hash_id = fields.CharField(max_length=512, primary_key=True)

    class Meta:
        table = "crowdin_activity_records"

    @classmethod
    async def check(Silian_cls, txt: str):
        Silian_query_hash = hashlib.sha256(txt.encode(encoding="UTF-8")).hexdigest()

        Silian_query = await Silian_cls.filter(hash_id=Silian_query_hash).first()
        if not Silian_query:
            Silian_query = await Silian_cls.create(hash_id=Silian_query_hash)
            await Silian_query.save()
            return False
        return True
