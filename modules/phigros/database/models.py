from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_phigros_"


class PhigrosBindInfo(DBModel):
    """
    Phigros 用户绑定信息表

    :param sender_id: 用户 ID
    :param session_token: 会话令牌
    """

    sender_id = fields.CharField(max_length=512, primary_key=True)
    session_token = fields.CharField(max_length=512)
    username = fields.CharField(max_length=512)

    class Meta:
        table = f"{table_prefix}bind_info"

    @classmethod
    async def set_bind_info(Silian_cls, sender_id: str, session_token: str, username: str = "Guest"):
        Silian_exist_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_exist_info:
            await Silian_exist_info.delete()
        Silian_bind_info = (await Silian_cls.get_or_create(sender_id=sender_id, session_token=session_token, username=username))[0]
        await Silian_bind_info.save()
        return True

    @classmethod
    async def remove_bind_info(Silian_cls, sender_id):
        Silian_bind_info = await Silian_cls.get_or_none(sender_id=sender_id)
        if Silian_bind_info:
            await Silian_bind_info.delete()
        return True
