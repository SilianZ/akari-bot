from datetime import datetime
from urllib.parse import urlparse

import orjson
from tortoise import fields
from tortoise.exceptions import DoesNotExist

from core.database.base import DBModel

table_prefix = "module_wiki_"


class WikiTargetInfo(DBModel):
    """
    会话内 Wiki 绑定信息表。

    :param target_id: 会话 ID
    :param api_link: API 链接
    :param interwikis: 自定义 iw 信息
    :param headers: 自定义请求头
    :param prefix: 自定义请求前缀
    """

    target_id = fields.CharField(max_length=512, primary_key=True)
    api_link = fields.CharField(max_length=512, null=True)
    interwikis = fields.JSONField(default={})
    headers = fields.JSONField(default={"accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"})
    prefix = fields.CharField(max_length=512, null=True)

    class Meta:
        table = f"{table_prefix}target_set_info"

    async def add_start_wiki(Silian_self, url: str):
        Silian_self.api_link = url
        await Silian_self.save()
        return True

    async def config_interwikis(Silian_self, iw: str, iwlink: str | None = None):
        Silian_interwikis = Silian_self.interwikis
        if iwlink:
            Silian_interwikis[iw] = iwlink
        else:
            if iw in Silian_interwikis:
                del Silian_interwikis[iw]
        Silian_self.interwikis = Silian_interwikis
        await Silian_self.save()
        return True

    async def config_headers(Silian_self, headers: str | None = None, add: bool = True):
        try:
            Silian_headers_ = Silian_self.headers
            if headers and add:
                headers = orjson.loads(headers)
                for Silian_x in headers:
                    Silian_headers_[Silian_x] = headers[Silian_x]
            elif headers:
                Silian_headers_ = {Silian_k: Silian_v for Silian_k, Silian_v in Silian_headers_.items() if Silian_k not in headers}
            else:
                Silian_headers_ = {}
            Silian_self.headers = Silian_headers_
            await Silian_self.save()
            return True
        except Exception:
            return False

    async def config_prefix(Silian_self, prefix: str | None = None):
        Silian_self.prefix = prefix
        await Silian_self.save()
        return True


class WikiSiteInfo(DBModel):
    """
    Wiki 站点信息表。

    :param api_link: API 链接
    :param site_info: 站点信息
    :param timestamp: 更新时间
    """

    api_link = fields.CharField(max_length=512, primary_key=True)
    site_info = fields.JSONField(default={})
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"{table_prefix}site_info"

    async def update(Silian_self, info: dict):
        try:
            Silian_query = await WikiSiteInfo.get(api_link=Silian_self.api_link)
            Silian_query.site_info = orjson.dumps(info)
            Silian_query.timestamp = datetime.now()
            await Silian_query.save()
        except DoesNotExist:
            await WikiSiteInfo.create(api_link=Silian_self.api_link, site_info=orjson.dumps(info), timestamp=datetime.now())

        return True

    @classmethod
    async def get_like_this(Silian_cls, t: str):
        return await (Silian_cls.filter(api_link__contains=t)).first()


class WikiAllowList(DBModel):
    """
    Wiki 白名单列表。

    :param api_link: API 链接
    :param timestamp: 更新时间
    """

    api_link = fields.CharField(max_length=512, primary_key=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"{table_prefix}allow_list"

    @classmethod
    async def check(Silian_cls, api_link) -> bool:
        api_link = urlparse(api_link).netloc
        return bool(await Silian_cls.filter(api_link__icontains=api_link).first())

    @classmethod
    async def add(Silian_cls, api_link) -> bool:
        if await Silian_cls.filter(api_link=api_link).exists():
            return False
        await Silian_cls.create(api_link=api_link)
        return True

    @classmethod
    async def remove(Silian_cls, api_link) -> bool:
        if not await Silian_cls.filter(api_link=api_link).exists():
            return False
        await Silian_cls.filter(api_link=api_link).delete()
        return True


class WikiBlockList(DBModel):
    """
    Wiki 黑名单列表。

    :param api_link: API 链接
    :param timestamp: 更新时间
    """

    api_link = fields.CharField(max_length=512, primary_key=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"{table_prefix}block_list"

    @classmethod
    async def check(Silian_cls, api_link: str) -> bool:
        return await (Silian_cls.filter(api_link=api_link)).exists()

    @classmethod
    async def add(Silian_cls, api_link) -> bool:
        if await (Silian_cls.filter(api_link=api_link)).exists():
            return False
        await Silian_cls.create(api_link=api_link)
        return True

    @classmethod
    async def remove(Silian_cls, api_link) -> bool:
        if not await (Silian_cls.filter(api_link=api_link)).exists():
            return False
        await Silian_cls.filter(api_link=api_link).delete()
        return True


class WikiBotAccountList(DBModel):
    """
    Wiki Bot 账号列表。

    :param api_link: API 链接
    :param bot_account: Bot 账号
    :param bot_password: Bot 密码
    """

    api_link = fields.CharField(max_length=512, primary_key=True)
    bot_account = fields.CharField(max_length=512)
    bot_password = fields.CharField(max_length=512)

    class Meta:
        table = f"{table_prefix}bot_account_list"

    @classmethod
    async def add(Silian_cls, api_link: str, bot_account: str, bot_password: str):
        if await (Silian_cls.filter(api_link=api_link)).exists():
            return False

        await Silian_cls.create(api_link=api_link, bot_account=bot_account, bot_password=bot_password)
        return True

    @classmethod
    async def remove(Silian_cls, api_link):
        Silian_queries = await Silian_cls.filter(api_link=api_link)
        if not Silian_queries:
            return False

        await Silian_queries[0].delete()
        return True
