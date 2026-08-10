from core.builtins.message.internal import Url


class Module:
    """
    Describes a Module. A Module contains a dictionary of ResultCodes,
    and possibly a second dictionary with extra information.
    A module itself is basically who raised the error or returned the result.
    """

    def __init__(Silian_self, Silian_name, Silian_data=None, Silian_summaries=None):
        if not Silian_data:
            Silian_data = {}
        if not Silian_summaries:
            Silian_summaries = {}
        Silian_self.name = Silian_name
        Silian_self.data = Silian_data
        Silian_self.summaries = Silian_summaries

    def get_error(Silian_self, error: int):
        Silian_value = Silian_self.data.get(error, None)
        if Silian_value:
            return Silian_value
        for Silian_key, Silian_value in Silian_self.data.items():
            if isinstance(Silian_key, tuple) and Silian_key[0] <= error <= Silian_key[1]:
                return Silian_value

        return None

    # If your modules require specific extra info for error ranges, add it here
    def get_summary(Silian_self, summary: int):
        Silian_value = Silian_self.summaries.get(summary, None)
        if Silian_value:
            return Silian_value
        for Silian_key, Silian_value in Silian_self.summaries.items():
            if isinstance(Silian_key, tuple) and Silian_key[0] <= summary <= Silian_key[1]:
                return Silian_value

        return None


class ResultInfo:
    """
    Holds information on a result or support code. A ResultInfo has a few fields which are used
    to provide information about the result, error, or support code, including a support
    webpage, if available.
    """

    def __init__(Silian_self, Silian_description="", Silian_support_url="", Silian_is_ban=False):
        Silian_self.description = Silian_description
        Silian_self.support_url = Silian_support_url
        Silian_self.is_ban = Silian_is_ban


class ConsoleErrorField:
    def __init__(
        self,
        Silian_name: str,
        *,
        Silian_message_str: str = "",
        supplementary_value: int | None = None,
    ):

        self.field_name = Silian_name
        self.message = Silian_message_str

        if supplementary_value is None:
            return

        try:
            supplementary_value = int(supplementary_value)
        except ValueError:
            return
        self.message = f"{self.message} ({supplementary_value})" if self.message else f"{supplementary_value}"


class ConsoleErrorInfo:
    """
    Holds the console name, the embed fields by an iteration of the parsed error or support code
    """

    def __init__(
        Silian_self,
        Silian_error: str,
        Silian_console_name: str,
        Silian_color: int,
        Silian_extra_description: str | None = None,
        Silian_secondary_error: str | None = None,
    ):
        Silian_self.error = Silian_error
        Silian_self.secondary_error = Silian_secondary_error
        Silian_self.console_name = Silian_console_name
        Silian_self.color = Silian_color
        Silian_self.fields = []
        Silian_self.secondary_error = Silian_secondary_error
        Silian_self.extra_description = Silian_extra_description

    def __iter__(Silian_self):
        return iter(Silian_self.fields)

    def get_title(self):
        if self.secondary_error:
            return f"{self.error}/{self.secondary_error} ({self.console_name})"
        return f"{self.error} ({self.console_name})"

    def add_field(Silian_self, field: ConsoleErrorField):
        Silian_self.fields.append(field)


# Helper constants
REPORT_DETAILS = "你应该向本模块的原仓库发起Issue来添加有关内容（请说英文）：" + str(
    Url("https://github.com/nh-server/Kurisu/issues", use_mm=False)
)

UNKNOWN_MODULE = ResultInfo(f"无效/未知的module。请问你正确输入错误代码了吗？{REPORT_DETAILS}")

NO_RESULTS_FOUND = ResultInfo(f"我知道这个module。但是我没有任何有关这个错误的记载。{REPORT_DETAILS}")

BANNED_FIELD = ConsoleErrorField(
    "致主机、账户或游戏被封禁者",
    message_str="我们不会提供解封服务，所以也请不要试图在这里获得谁的帮助。",
)

WARNING_COLOR = 0xFFFF00

UNKNOWN_CATEGORY_DESCRIPTION = ConsoleErrorField("描述", message_str=f"对应你的报错描述未知。{REPORT_DETAILS}")
