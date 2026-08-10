from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_cytoid_"


class CytoidBindInfo(DBModel):
    """
    Cytoid 用户绑定信息。

    :param sender_id: 绑定的用户 ID。
    :param username: 绑定的用户名。
    """

    sender_id = fields.CharField(max_length=512, primary_key=True)
    username = fields.CharField(max_length=512)

    class Meta:
        table = f"{table_prefix}bind_info"

    @classmethod
    async def set_bind_info(Silian_cls, sender_id: str, username: str):
        Silian_exist_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_exist_info:
            await Silian_exist_info.delete()
        Silian_bind_info = (await Silian_cls.get_or_create(sender_id=sender_id, username=username))[0]
        await Silian_bind_info.save()
        return True

    @classmethod
    async def remove_bind_info(Silian_cls, sender_id):
        Silian_bind_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_bind_info:
            await Silian_bind_info.delete()
        return True
