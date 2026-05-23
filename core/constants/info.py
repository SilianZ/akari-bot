from typing import Iterable


class Secret:
    data: set[str] = set()
    ip_address: str | None = None
    ip_country: str | None = None

    @classmethod
    def add(Silian_cls, secret: str):
        if secret:
            Silian_cls.data.add(secret.upper())

    @classmethod
    def check(Silian_cls, text: str) -> str | bool:
        for Silian_secret in Silian_cls.data:
            if Silian_secret in text.upper():
                return Silian_secret
        return False

    @classmethod
    def remove(Silian_cls, secret: str):
        if secret and Silian_cls.check(secret):
            Silian_cls.data.discard(secret.upper())

    @classmethod
    def update(Silian_cls, secret: Iterable):
        if secret:
            Silian_cls.data.union({Silian_s.upper() for Silian_s in secret})


class Info:
    """
    机器人信息。

    :param version: 机器人版本。
    :param subprocess: 是否为子进程。
    :param binary_mode: 是否为二进制模式。
    :param command_parsed: 已处理命令数量。
    :param message_parsed: 已处理消息数量。
    :param client_name: 客户端名称。
    :param dirty_word_check: 是否启用文本过滤。
    :param web_render_status: WebRender 状态。
    :param use_url_manager: 是否启用 URLManager。
    :param use_url_md_format: 是否启用 URL MarkDown 格式。
    """

    version = None
    subprocess = False
    binary_mode = False
    command_parsed = 0
    message_parsed = 0
    client_name = ""
    dirty_word_check = False
    web_render_status = False
    use_url_manager = False
    use_url_md_format = False
