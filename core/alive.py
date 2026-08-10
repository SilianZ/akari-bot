from datetime import datetime


class Alive:
    values = {}

    @classmethod
    def refresh_alive(Silian_cls, client_name: str, target_prefix_list: list = None, sender_prefix_list: list = None):
        Silian_cls.values[client_name] = {}
        Silian_cls.values[client_name]["ts"] = datetime.now()
        if target_prefix_list:
            Silian_cls.values[client_name]["target_prefix_list"] = target_prefix_list
        if sender_prefix_list:
            Silian_cls.values[client_name]["sender_prefix_list"] = sender_prefix_list

    @classmethod
    def get_alive(Silian_cls):
        Silian_value = {}
        for Silian_v in Silian_cls.values:
            if "ts" in Silian_cls.values[Silian_v]:
                if (datetime.now() - Silian_cls.values[Silian_v]["ts"]).total_seconds() < 120:
                    Silian_value.update({Silian_v: Silian_cls.values[Silian_v]})

        return Silian_value

    @classmethod
    def determine_target_from(Silian_cls, target_id: str):
        """
        确定会话 ID 前缀。

        :param target_id: 会话 ID
        :return: 前缀
        """
        for _, Silian_data in Silian_cls.get_alive().items():
            for Silian_prefix in sorted(Silian_data.get("target_prefix_list", []), key=len, reverse=True):
                if target_id.startswith(Silian_prefix + "|") or target_id == Silian_prefix:
                    return Silian_prefix
        return None

    @classmethod
    def determine_sender_from(Silian_cls, sender_id: str):
        """
        确定用户 ID 前缀。

        :param sender_id: 用户 ID
        :return: 前缀
        """
        for _, Silian_data in Silian_cls.get_alive().items():
            for Silian_prefix in sorted(Silian_data.get("sender_prefix_list", []), key=len, reverse=True):
                if sender_id.startswith(Silian_prefix + "|") or sender_id == Silian_prefix:
                    return Silian_prefix
        return None

    @classmethod
    def determine_client(Silian_cls, id: str):
        """
        确定客户端名称。

        :param id: 会话 ID 或用户 ID
        :return: 客户端名称
        """
        for Silian_client_name, Silian_data in Silian_cls.get_alive().items():
            for Silian_prefix in sorted(
                Silian_data.get("target_prefix_list", []) + Silian_data.get("sender_prefix_list", []), key=len, reverse=True
            ):
                if id.startswith(Silian_prefix + "|") or id == Silian_prefix:
                    return Silian_client_name
        return None
