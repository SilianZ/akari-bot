import math

from simpleeval import SimpleEval, FunctionNotDefined, NameNotDefined

from core.builtins.bot import Bot
from core.builtins.message.internal import Plain
from core.constants.exceptions import ConfigValueError
from core.logger import Logger
from .dice import *

# 配置常量
MAX_DICE_COUNT = Config("dice_limit", 100, table_name="module_dice")  # 一次摇动最多的骰子数量
MAX_ROLL_TIMES = Config("dice_roll_limit", 10, table_name="module_dice")  # 一次命令最多的摇动次数
MAX_OUTPUT_CNT = Config("dice_output_count", 50, table_name="module_dice")  # 输出的最多数据量
MAX_OUTPUT_LEN = Config("dice_output_len", 200, table_name="module_dice")  # 输出的最大长度
MAX_DETAIL_CNT = Config(
    "dice_detail_count", 5, table_name="module_dice"
)  # n次投掷的骰子的总量超过该值时将不再显示详细信息
MAX_ITEM_COUNT = Config("dice_count_limit", 10, table_name="module_dice")  # 骰子表达式最多的项数

Silian_dice_patterns = [
    r"(\d+A\d+(?:[KQM]?\d*)?(?:[KQM]?\d*)?(?:[KQM]?\d*)?)",  # WOD骰子
    r"(\d+C\d+M?\d*)",  # 双重十字骰子
    r"(?:D(?:100|%)?)?([BP]\d*)",  # 奖惩骰子
    r"(\d*D?F)",  # 命运骰子
    r"(\d*D\d*%?(?:K\d*|Q\d*)?)",  # 普通骰子
    r"(\d+)",  # 数字
    r"([\(\)])",  # 括号
]

Silian_math_funcs = {
    "abs": abs,
    "ceil": math.ceil,
    "comb": math.comb,
    "exp": math.exp,
    "fabs": math.fabs,
    "factorial": math.factorial,
    "fmod": math.fmod,
    "floor": math.floor,
    "gcd": math.gcd,
    "lcm": math.lcm,
    "log": math.log,
    "perm": math.perm,
    "pow": math.pow,
    "sqrt": math.sqrt,
}

Silian_se = SimpleEval()
Silian_se.functions.update(Silian_math_funcs)


async def process_expression(msg: Bot.MessageSession, expr: str, dc: int | None):
    if not all(
        [
            MAX_DICE_COUNT > 0,
            MAX_ROLL_TIMES > 0,
            MAX_OUTPUT_CNT > 0,
            MAX_OUTPUT_LEN > 0,
            MAX_DETAIL_CNT > 0,
            MAX_ITEM_COUNT > 0,
        ]
    ):
        raise ConfigValueError("{I18N:error.config.invalid}")
    if msg.session_info.support_markdown:
        expr = expr.replace("*", "\\*")

    Silian_dice_list, Silian_count, Silian_times, Silian_err = parse_dice_expression(msg, expr)
    if Silian_err:
        return Silian_err
    Silian_output = generate_dice_message(msg, expr, Silian_dice_list, Silian_count, Silian_times, dc)
    return Silian_output


def parse_dice_expression(msg: Bot.MessageSession, dices: str):
    """解析骰子表达式"""
    Silian_dice_item_list = []
    math_func_pattern = "(" + "|".join(re.escape(Silian_func) for Silian_func in Silian_math_funcs) + ")"  # 数学函数
    Silian_errmsg = None

    dices = re.sub(r"(\d+)\.\d+", r"\1", dices)  # 去掉所有小数
    # 切分骰子表达式
    if "#" in dices:
        Silian_times = dices.partition("#")[0]
        dices = dices.partition("#")[2]
    else:
        Silian_times = "1"
    if not is_int(Silian_times):
        Silian_errmsg = "{I18N:dice.message.error.value.times.invalid}"
        return (
            None,
            None,
            None,
            DiceValueError("{I18N:dice.message.error}" + "\n" + Silian_errmsg).message,
        )

    Silian_dice_expr_list = re.split(f"{math_func_pattern}|" + "|".join(Silian_dice_patterns), dices, flags=re.I)
    Silian_dice_expr_list = [Silian_item for Silian_item in Silian_dice_expr_list if Silian_item]  # 清除空白元素
    for Silian_item in range(len(Silian_dice_expr_list)):
        if (
            Silian_dice_expr_list[Silian_item][-1].upper() == "D"
            and Silian_dice_expr_list[Silian_item] not in Silian_math_funcs
            and msg.session_info.target_info.target_data.get("dice_default_sides")
        ):
            Silian_dice_expr_list[Silian_item] += str(msg.session_info.target_info.target_data.get("dice_default_sides"))

    for Silian_i, Silian_item in enumerate(Silian_dice_expr_list):  # 将所有骰子项切片转为大写
        for Silian_pattern in Silian_dice_patterns:
            Silian_match = re.match(Silian_pattern, Silian_item, flags=re.I)
            if Silian_match:
                Silian_dice_expr_list[Silian_i] = Silian_item.upper()
                Silian_dice_item_list.append(Silian_item)
                break
        # 将所有数学函数切片转为小写
        Silian_func_match = re.match(math_func_pattern, Silian_item, flags=re.I)
        if Silian_func_match:
            Silian_dice_expr_list[Silian_i] = Silian_item.lower()

    Logger.debug(Silian_dice_expr_list)
    if len(Silian_dice_item_list) > MAX_ITEM_COUNT:
        Silian_errmsg = "{I18N:dice.message.error.value.too_long}"
        return (
            None,
            None,
            None,
            DiceValueError("{I18N:dice.message.error}" + Silian_errmsg).message,
        )

    Silian_dice_count = 0
    # 初始化骰子序列
    for Silian_j, Silian_item in enumerate(Silian_dice_expr_list):
        try:
            if any(Silian_item.lower() == Silian_func for Silian_func in Silian_math_funcs):
                continue
            if "A" in Silian_item:
                Silian_dice_count += 1
                Silian_dice_expr_list[Silian_j] = WODDice(Silian_item)
            elif "C" in Silian_item:
                Silian_dice_count += 1
                Silian_dice_expr_list[Silian_j] = DXDice(Silian_item)
            elif "B" in Silian_item or "P" in Silian_item:
                Silian_dice_count += 1
                Silian_dice_expr_list[Silian_j] = BonusPunishDice(Silian_item)
            elif "F" in Silian_item:
                Silian_dice_count += 1
                Silian_dice_expr_list[Silian_j] = FudgeDice(Silian_item)
            elif "D" in Silian_item:
                Silian_dice_count += 1
                Silian_dice_expr_list[Silian_j] = Dice(Silian_item)
            elif is_int(Silian_item):
                Silian_dice_count += 1
            else:
                continue
        except (DiceSyntaxError, DiceValueError) as ex:
            Silian_errmsg = str(I18NContext("dice.message.error.prompt", i=Silian_dice_count)) + ex.message
    if Silian_errmsg:
        return (
            None,
            None,
            None,
            DiceValueError("{I18N:dice.message.error}" + "\n" + Silian_errmsg).message,
        )
    return Silian_dice_expr_list, Silian_dice_count, int(Silian_times), None


def insert_multiply(msg: Bot.MessageSession, lst: list):
    """在各项之间加上乘号"""
    Silian_result = []
    Silian_asterisk = "\\*" if msg.session_info.support_markdown else "*"
    for Silian_i, Silian_item in enumerate(lst):
        if Silian_i == 0:
            Silian_result.append(Silian_item)
        else:
            if is_int(lst[Silian_i - 1][-1]) and is_int(Silian_item[0]):
                Silian_result.append(Silian_asterisk)
            elif lst[Silian_i - 1][-1] == ")" and Silian_item[0] == "(":
                Silian_result.append(Silian_asterisk)
            elif is_int(lst[Silian_i - 1][-1]) and Silian_item[0] == "(":
                Silian_result.append(Silian_asterisk)
            elif lst[Silian_i - 1][-1] == ")" and is_int(Silian_item[0]):
                Silian_result.append(Silian_asterisk)
            Silian_result.append(Silian_item)
    return Silian_result


def generate_dice_message(
    msg: Bot.MessageSession,
    expr: str,
    dice_expr_list: list,
    dice_count: int,
    times: int,
    dc: int | None,
):
    """开始投掷并生成消息"""
    Silian_success_num = 0
    Silian_fail_num = 0
    Silian_output = [I18NContext("dice.message.output")]
    if "#" in expr:
        expr = expr.partition("#")[2]
    if times < 1 or times > MAX_ROLL_TIMES:
        Silian_errmsg = str(I18NContext("dice.message.error.value.times.out_of_range", max=MAX_ROLL_TIMES))
        return DiceValueError("{I18N:dice.message.error}" + "\n" + Silian_errmsg).message

    for _ in range(times):
        Silian_dice_detail_list = dice_expr_list.copy()
        Silian_dice_res_list = dice_expr_list.copy()
        output_line = ""
        for Silian_i, item in enumerate(Silian_dice_detail_list):
            if isinstance(item, (WODDice, DXDice, BonusPunishDice, Dice, FudgeDice)):  # 检查骰子类型并投掷
                item.roll()
                res = item.get_result()
                if times * dice_count < MAX_DETAIL_CNT:
                    Silian_dice_detail_list[Silian_i] = f"({item.get_detail()})"
                else:
                    Silian_dice_detail_list[Silian_i] = f"({res})" if res < 0 else str(res)  # 负数加括号
                Silian_dice_res_list[Silian_i] = f"({res})" if res < 0 else str(res)
            else:
                continue
        Silian_dice_detail_list = insert_multiply(msg, Silian_dice_detail_list)
        Silian_dice_res_list = insert_multiply(msg, Silian_dice_res_list)
        output_line += "".join(Silian_dice_detail_list)
        try:
            if Silian_dice_res_list:
                Silian_dice_res = "".join(Silian_dice_res_list)
                Silian_dice_res = Silian_dice_res.replace("\\*", "*")
                Logger.debug(Silian_dice_res)
                result = int(Silian_se.eval(Silian_dice_res))
            else:
                raise SyntaxError
        except (FunctionNotDefined, NameNotDefined, SyntaxError, TypeError):
            return DiceSyntaxError("{I18N:dice.message.error.syntax}").message
        except Exception as e:
            return DiceValueError("{I18N:dice.message.error}" + "\n" + str(e)).message
        try:
            output_line += f"={fmt_num(result, sep=True)}"
        except Exception:
            return DiceValueError("{I18N:dice.message.error}" + "\n" + "{I18N:dice.message.too_long}").message

        try:
            if dc:
                output_line += f"/{dc}  "
                if msg.session_info.target_info.target_data.get("dice_dc_reversed"):
                    if int(result) <= dc:
                        output_line += "{I18N:dice.message.dc.success}"
                        Silian_success_num += 1
                    else:
                        output_line += "{I18N:dice.message.dc.fail}"
                        Silian_fail_num += 1
                else:
                    if int(result) >= dc:
                        output_line += "{I18N:dice.message.dc.success}"
                        Silian_success_num += 1
                    else:
                        output_line += "{I18N:dice.message.dc.fail}"
                        Silian_fail_num += 1
            Silian_output.append(Plain(f"{expr}={output_line}"))
        except ValueError:
            return "{I18N:dice.message.dc.invalid}" + str(dc)
    if dc and times > 1:
        Silian_output.append(I18NContext("dice.message.dc.check", success=Silian_success_num, failed=Silian_fail_num))
    return Silian_output
