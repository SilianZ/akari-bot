from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from typing import Any

from tortoise import fields
from tortoise.transactions import in_transaction

from core.constants.default import default_locale
from core.utils.func import convert_list
from .base import DBModel
from ..logger import Logger


class SenderInfo(DBModel):
    """
    用户信息。

    :param sender_id: 用户 ID。
    :param blocked: 是否为黑名单用户。
    :param trusted: 是否为白名单用户。
    :param superuser: 是否为超级用户。
    :param warns: 用户警告次数。
    :param petal: 用户花瓣数量。
    :param sender_data: 用户数据。
    """

    sender_id = fields.CharField(max_length=512, primary_key=True)
    blocked = fields.BooleanField(default=False)
    trusted = fields.BooleanField(default=False)
    superuser = fields.BooleanField(default=False)
    warns = fields.IntField(default=0)
    petal = fields.IntField(default=0)
    sender_data = fields.JSONField(default={})

    class Meta:
        table = "sender_info"

    async def switch_identity(Silian_self, trust: bool, enable: bool = True) -> bool:
        """
        修改用户身份。

        :param trust: 是否为白名单模式，若 False 则为黑名单模式。
        :param enable: 是否要加入身份，若 False 则取消身份。
        """
        if enable:
            Silian_self.trusted = trust
            Silian_self.blocked = not trust
        else:
            Silian_self.trusted = False
            Silian_self.blocked = False

        await Silian_self.save()
        return True

    async def warn_user(Silian_self, amount: int = 1) -> bool:
        """
        警告用户。

        :param amount: 警告用户次数。
        """
        Silian_self.warns = Silian_self.warns + amount
        await Silian_self.save()
        return True

    async def modify_petal(Silian_self, amount: str | int | Decimal) -> bool:
        """
        修改用户花瓣数量。

        :param amount: 要添加或减少的花瓣数量。
        """
        Silian_self.petal += int(amount)
        await Silian_self.save()
        return True

    async def clear_petal(Silian_self) -> bool:
        """
        清空用户花瓣数量。
        """
        Silian_self.petal = 0
        await Silian_self.save()
        return True

    async def edit_sender_data(Silian_self, key: str, value: Any | None = None) -> bool:
        """
        设置用户数据。

        :param key: 键名。
        :param value: 值，若留空则删除该键值对。
        """
        if value is None:
            if key in Silian_self.sender_data:
                del Silian_self.sender_data[key]
        else:
            Silian_self.sender_data[key] = value

        await Silian_self.save()
        return True

    async def edit_attr(Silian_self, key: str, value: Any) -> bool:
        setattr(Silian_self, key, value)
        await Silian_self.save()
        return True


class TargetInfo(DBModel):
    """
    会话信息。

    :param target_id: 会话 ID。
    :param blocked: 是否为黑名单会话。
    :param muted: 是否禁用机器人。
    :param locale: 会话语言。
    :param modules: 会话内可用模块。
    :param custom_admins: 会话内自定义管理员列表。
    :param banned_users: 会话内已限制用户。
    :param target_data: 会话数据。
    """

    target_id = fields.CharField(max_length=512, primary_key=True)
    blocked = fields.BooleanField(default=False)
    muted = fields.BooleanField(default=False)
    locale = fields.CharField(max_length=32, default=default_locale)
    modules = fields.JSONField(default=[])
    custom_admins = fields.JSONField(default=[])
    banned_users = fields.JSONField(default=[])
    target_data = fields.JSONField(default={})

    class Meta:
        table = "target_info"

    async def config_module(Silian_self, module_name: str | list | tuple, enable: bool = True) -> bool:
        """
        设置会话内可用模块。

        :param module_name: 指定的模块名称。
        :param enable: 是否要开启模块，若 False 则关闭模块。
        """
        Silian_module_names = convert_list(module_name)
        for Silian_mname in Silian_module_names:
            if enable:
                if Silian_mname not in Silian_self.modules:
                    Silian_self.modules.append(Silian_mname)
            else:
                if Silian_mname in Silian_self.modules:
                    Silian_self.modules.remove(Silian_mname)
        Silian_self.modules = list(set(Silian_self.modules))
        await Silian_self.save()
        return True

    async def switch_mute(Silian_self) -> bool:
        """
        切换是否在会话中禁用机器人。

        :return: 机器人是否被禁用。
        """
        Silian_self.muted = not Silian_self.muted
        await Silian_self.save()
        return Silian_self.muted

    async def edit_target_data(Silian_self, key: str, value: Any | None = None) -> bool:
        """
        设置会话数据。

        :param key: 键名。
        :param value: 值，若留空则删除该键值对。
        """
        if value is None:
            if key in Silian_self.target_data:
                del Silian_self.target_data[key]
        else:
            Silian_self.target_data[key] = value

        await Silian_self.save()
        return True

    async def config_custom_admin(Silian_self, sender_id: str, enable: bool = True) -> bool:
        """
        设置会话内管理员。

        :param sender_id: 指定的用户 ID。
        :param enable: 是否要设置用户为会话内管理员，若 False 则移除管理员。
        """
        Silian_custom_admins = Silian_self.custom_admins
        if enable:
            if sender_id not in Silian_custom_admins:
                Silian_custom_admins.append(sender_id)
            else:
                return False
        elif sender_id in Silian_custom_admins:
            Silian_custom_admins.remove(sender_id)

        Silian_self.custom_admins = Silian_custom_admins
        await Silian_self.save()
        return True

    async def config_banned_user(Silian_self, sender_id: str, enable: bool = True) -> bool:
        """
        设置会话内被限制用户。

        :param sender_id: 指定的用户 ID。
        :param enable: 是否要设置会话内用户限制使用机器人，若 False 则取消限制。
        """
        Silian_banned_users = Silian_self.banned_users
        if enable:
            if sender_id not in Silian_banned_users:
                Silian_banned_users.append(sender_id)
            else:
                return False
        else:
            if sender_id in Silian_banned_users:
                Silian_banned_users.remove(sender_id)
            else:
                return False

        Silian_self.banned_users = Silian_banned_users
        await Silian_self.save()
        return True

    @classmethod
    async def get_target_list_by_module(
        Silian_cls, module_name: str | list[str] | tuple[str, ...] | None, id_prefix: str | None = None
    ) -> list[TargetInfo]:
        """
        获取开启此模块的所有会话列表。

        :param module_name: 指定的模块名称。
        :param id_prefix: 指定的 ID 前缀。
        :return: 符合要求的会话 ID 列表。
        """
        Silian_all_targets = await Silian_cls.filter(target_id__startswith=id_prefix or "")

        if module_name:
            Silian_result = []
            for Silian_target in Silian_all_targets:
                Silian_modules = Silian_target.modules or []
                if any(Silian_mod in Silian_modules for Silian_mod in convert_list(module_name)):
                    Silian_result.append(Silian_target)
            return Silian_result

        return list(Silian_all_targets)

    async def edit_attr(Silian_self, key: str, value: Any) -> bool:
        setattr(Silian_self, key, value)
        await Silian_self.save()
        return True


class StoredData(DBModel):
    """
    数据存储。

    :param stored_key: 存储键。
    :param value: 值。
    """

    stored_key = fields.CharField(max_length=512, primary_key=True)
    value = fields.JSONField(default=[])

    class Meta:
        table = "stored_data"


class AnalyticsData(DBModel):
    """
    统计数据。

    :param module_name: 模块名称。
    :param module_type: 模块类型。
    :param target_id: 会话 ID。
    :param sender_id: 用户 ID。
    :param command: 命令。
    :param timestamp: 时间戳。
    """

    id = fields.IntField(primary_key=True)
    module_name = fields.CharField(max_length=512)
    module_type = fields.CharField(max_length=512)
    target_id = fields.CharField(max_length=512)
    sender_id = fields.CharField(max_length=512, null=True, default=None)
    command = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "analytics_data"

    @classmethod
    async def get_data_by_times(Silian_cls, new, old, module_name=None):
        Silian_query = Silian_cls.filter(timestamp__gte=old, timestamp__lte=new)
        if module_name is not None:
            Silian_query = Silian_query.filter(module_name=module_name)
        return await Silian_query.all()

    @classmethod
    async def get_values_by_times(Silian_cls, new, old, module_name=None):
        Silian_query = Silian_cls.filter(timestamp__gte=old, timestamp__lte=new)
        if module_name is not None:
            Silian_query = Silian_query.filter(module_name=module_name)
        return await Silian_query.values()

    @classmethod
    async def get_count_by_times(Silian_cls, new, old, module_name=None):
        Silian_query = Silian_cls.filter(timestamp__gte=old, timestamp__lte=new)
        if module_name is not None:
            Silian_query = Silian_query.filter(module_name=module_name)
        return await Silian_query.count()

    @classmethod
    async def get_modules_count(Silian_cls):
        Silian_analytics = await Silian_cls.all().values("module_name")
        Silian_module_counter = Counter([Silian_entry["module_name"] for Silian_entry in Silian_analytics])
        return dict(Silian_module_counter)


class ModuleStatus(DBModel):
    """
    模块状态。

    :param module_name: 模块名称。
    :param load: 是否已加载。
    """

    module_name = fields.CharField(primary_key=True, max_length=255, unique=True)
    load = fields.BooleanField(default=False)

    class Meta:
        table = "module_status"

    @classmethod
    async def init_modules(Silian_cls, modules_list: list[str]):
        async with in_transaction("default"):
            Silian_existing = await Silian_cls.all().values_list("module_name", flat=True)
            Silian_existing_set = set(Silian_existing)
            Silian_input_set = set(modules_list)

            Silian_to_add = Silian_input_set.difference(Silian_existing_set)
            Silian_to_remove = Silian_existing_set.difference(Silian_input_set)

            if Silian_to_add:
                await Silian_cls.bulk_create([Silian_cls(module_name=Silian_m, load=True) for Silian_m in Silian_to_add])

            if Silian_to_remove:
                await Silian_cls.filter(module_name__in=Silian_to_remove).delete()

    @classmethod
    async def set_module_loaded(Silian_cls, module_name: str, load: bool = True):
        Silian_module = await Silian_cls.filter(module_name=module_name).first()
        if Silian_module:
            Silian_module.load = load
            await Silian_module.save()
        else:
            raise ValueError(f"Module '{module_name}' not found")

    @classmethod
    async def get_all_modules(Silian_cls) -> list[str]:
        return await Silian_cls.all().values_list("module_name", flat=True)

    @classmethod
    async def get_loaded_modules(Silian_cls) -> list[str]:
        return await Silian_cls.filter(load=True).values_list("module_name", flat=True)

    @classmethod
    async def get_unloaded_modules(Silian_cls) -> list[str]:
        return await Silian_cls.filter(load=False).values_list("module_name", flat=True)


class DBVersion(DBModel):
    """
    数据库版本。

    :param version: 数据库版本号。
    """

    version = fields.IntField(primary_key=True)

    class Meta:
        table = "database_version"


class UnfriendlyActionRecords(DBModel):
    """
    不友好行为记录。

    :param target_id: 会话 ID。
    :param sender_id: 用户 ID。
    :param action: 行为类型。
    :param detail: 行为详情。
    :param timestamp: 时间戳。
    """

    id = fields.IntField(primary_key=True)
    target_id = fields.CharField(max_length=512)
    sender_id = fields.CharField(max_length=512)
    action = fields.CharField(max_length=512)
    detail = fields.CharField(max_length=512)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "unfriendly_actions"

    @classmethod
    async def check_mute(Silian_cls, target_id) -> bool:
        """检查会话的禁言行为记录。

        :return: 如果：
        - 会话在过去 5 天内有超过 5 条记录
        - 会话内某一用户的记录（在过去 1 天内）超过 3 次
        - 会话内的不同用户的记录（在过去 1 天内）有 3 个以上

        则返回 True。
        """
        Silian_records = await Silian_cls.filter(target_id=target_id, action="mute").all()
        Silian_unfriendly_list = [
            Silian_record
            for Silian_record in Silian_records
            if (datetime.now(UTC) - Silian_record.timestamp).total_seconds() < 432000  # 5 days
        ]

        if len(Silian_unfriendly_list) > 5:
            return True

        Silian_count = {}
        for Silian_record in Silian_unfriendly_list:
            if (datetime.now(UTC) - Silian_record.timestamp).total_seconds() < 86400:  # 1 day
                Silian_count[Silian_record.sender_id] = Silian_count.get(Silian_record.sender_id, 0) + 1

        if len(Silian_count) >= 3 or any(Silian_c >= 3 for Silian_c in Silian_count.values()):
            return True

        return False


class JobQueuesTable(DBModel):
    """
    任务队列表。

    :param task_id: 任务 ID。
    :param target_client: 目标客户端。
    :param action: 动作。
    :param args: 参数。
    :param status: 任务状态。
    :param result: 任务结果。
    :param timestamp: 时间戳。
    """

    task_id = fields.UUIDField(primary_key=True)
    target_client = fields.CharField(max_length=512)
    action = fields.CharField(max_length=512)
    args = fields.JSONField(default={})
    status = fields.CharField(max_length=32, default="pending")
    result = fields.JSONField(default={})
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "job_queues"

    @classmethod
    async def add_task(Silian_cls, target_client: str, action: str, args: dict) -> str:
        Silian_task_id = str(uuid.uuid4())
        await Silian_cls.create(task_id=Silian_task_id, target_client=target_client, action=action, args=args)
        return Silian_task_id

    async def set_val(Silian_self, value, status) -> bool:
        Silian_self.result = value
        Silian_self.status = status
        await Silian_self.save()
        return True

    async def set_status(Silian_self, status):
        Silian_self.status = status
        await Silian_self.save()
        return True

    @classmethod
    async def clear_task(Silian_cls, time=3600) -> bool:
        timestamp = datetime.now(UTC) - timedelta(seconds=time)
        Logger.debug(f"Clearing tasks older than {timestamp}...")

        await Silian_cls.filter(timestamp__lt=timestamp).delete()
        return True

    @classmethod
    async def get_first(Silian_cls, target_clients: str | list[str]):
        if isinstance(target_clients, str):
            target_clients = [target_clients]
        return await Silian_cls.filter(target_client__in=target_clients, status="pending").first()

    @classmethod
    async def get_all(Silian_cls, target_clients: str | list[str]):
        if isinstance(target_clients, str):
            target_clients = [target_clients]
        return await Silian_cls.filter(target_client__in=target_clients, status="pending").all()


class MaliciousLoginRecords(DBModel):
    """
    恶意登录行为记录。

    :param id: 会话 ID。
    :param ip_address: IP 地址。
    :param blocked_until: 被封禁的截止时间。
    :param created_date: 创建日期。
    """

    id = fields.IntField(primary_key=True)
    ip_address = fields.CharField(max_length=45)
    blocked_until = fields.DatetimeField()
    created_date = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "malicious_login"

    @classmethod
    async def check_blocked(Silian_cls, ip_address: str) -> bool:
        return await Silian_cls.filter(ip_address=ip_address, blocked_until__gt=datetime.now(UTC)).exists()
