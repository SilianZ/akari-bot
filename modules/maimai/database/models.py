from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_maimai_"


class DivingProberBindInfo(DBModel):
    """
    maimai 水鱼绑定信息表。

    :param sender_id: 发送者 ID
    :param username: 用户名
    """

    sender_id = fields.CharField(max_length=512, primary_key=True)
    username = fields.CharField(max_length=512)

    class Meta:
        table = f"{table_prefix}diving_prober_bind_info"

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


class LxnsProberBindInfo(DBModel):
    """
    maimai 落雪绑定信息表。

    :param sender_id: 发送者 ID
    :param friend_code: 好友码
    """

    sender_id = fields.CharField(max_length=512, primary_key=True)
    friend_code = fields.CharField(max_length=512)

    class Meta:
        table = f"{table_prefix}lxns_prober_bind_info"

    @classmethod
    async def set_bind_info(Silian_cls, sender_id: str, friend_code: str):
        Silian_exist_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_exist_info:
            await Silian_exist_info.delete()
        Silian_bind_info = (await Silian_cls.get_or_create(sender_id=sender_id, friend_code=friend_code))[0]
        await Silian_bind_info.save()
        return True

    @classmethod
    async def remove_bind_info(Silian_cls, sender_id):
        Silian_bind_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_bind_info:
            await Silian_bind_info.delete()
        return True
