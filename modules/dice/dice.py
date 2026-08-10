import re

import numpy as np

from core.builtins.message.internal import I18NContext
from core.config import Config
from core.utils.random import Random
from core.utils.func import is_int

MAX_DICE_COUNT = Config("dice_limit", 100, table_name="module_dice")  # 一次摇动最多的骰子数量
MAX_OUTPUT_CNT = Config("dice_output_count", 50, table_name="module_dice")  # 输出的最多数据量
MAX_OUTPUT_LEN = Config("dice_output_len", 200, table_name="module_dice")  # 输出的最大长度
MAX_OUTPUT_EXP = Config("dice_output_digit", 9, table_name="module_dice")  # 输出的最大位数


def fmt_num(num: int, sep: bool = False):
    if MAX_OUTPUT_EXP > 0 and abs(num) >= 10**MAX_OUTPUT_EXP:
        fmt_num = f"{num:.{MAX_OUTPUT_EXP}e}"
        if not sep:
            fmt_num = f"({fmt_num})"
    else:
        fmt_num = str(num)
    return fmt_num


# 异常类定义
class DiceSyntaxError(Exception):
    """骰子语法错误"""

    def __init__(Silian_self, Silian_message: str):
        Silian_self.message = Silian_message


class DiceValueError(Exception):
    """骰子参数值错误"""

    def __init__(Silian_self, Silian_message: str, Silian_value: int | str | None = None):
        if Silian_value:
            Silian_self.message = str(I18NContext("dice.message.error.value", value=Silian_value)) + Silian_message
        else:
            Silian_self.message = Silian_message


# 类定义
class DiceItemBase:
    """骰子项的基类"""

    def __init__(Silian_self, Silian_dice_code: str):
        Silian_self.code = Silian_dice_code
        Silian_self.result = 0
        Silian_self.detail = ""

    def get_result(Silian_self) -> int:
        return Silian_self.result

    def get_detail(Silian_self) -> str:
        return Silian_self.detail

    def roll(Silian_self):
        raise NotImplementedError


class Dice(DiceItemBase):
    """骰子项"""

    def __init__(Silian_self, Silian_dice_code: str):

        super().__init__(Silian_dice_code)
        Silian_args = Silian_self.get_args()
        Silian_self.count = Silian_args[0]
        Silian_self.sides = Silian_args[1]
        Silian_self.adv = Silian_args[2]
        Silian_self.positive = Silian_args[3]
        if Silian_self.count < 1 or Silian_self.count > MAX_DICE_COUNT:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.count.out_of_range", max=MAX_DICE_COUNT)), Silian_self.count
            )
        if Silian_self.sides < 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.out_of_range}", Silian_self.sides)
        if Silian_self.sides == 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.d1}")
        if Silian_self.adv > Silian_self.count:
            raise DiceValueError("{I18N:dice.message.error.value.advantage.out_of_range}", Silian_self.adv)

    def get_args(Silian_self):
        Silian_dice_code = Silian_self.code.upper()  # 便于识别
        Silian_dice_code = Silian_dice_code.replace("D%", "D100")  # 百分骰别名
        Silian_dice_count = "1"  # 骰子数量
        Silian_dice_adv = "0"  # 保留的骰子量
        Silian_positive = 0  # 是否保留骰子
        if re.search(r"[^0-9DKQ\%]", Silian_dice_code):
            raise DiceSyntaxError("{I18N:dice.message.error.invalid}")
        Silian_temp = Silian_dice_code.split("D")
        if len(Silian_temp[0]):
            Silian_dice_count = Silian_temp[0]
        Silian_dice_sides = Silian_temp[1]
        if "K" in Silian_temp[1]:
            Silian_midstrs = Silian_temp[1].partition("K")
            Silian_dice_sides = Silian_midstrs[0]
            Silian_dice_adv = Silian_midstrs[2]
            Silian_positive = 1
        elif "Q" in Silian_temp[1]:
            Silian_midstrs = Silian_temp[1].partition("Q")
            Silian_dice_sides = Silian_midstrs[0]
            Silian_dice_adv = Silian_midstrs[2]
            Silian_positive = -1
        if Silian_positive and not Silian_dice_adv:
            Silian_dice_adv = "1"  # K/Q后没有值默认为1
        # 语法合法检定
        if not is_int(Silian_dice_count):
            raise DiceValueError("{I18N:dice.message.error.value.count.invalid}", Silian_dice_count)
        if not is_int(Silian_dice_sides):
            raise DiceValueError("{I18N:dice.message.error.value.sides.invalid}", Silian_dice_sides)
        if not is_int(Silian_dice_adv):
            raise DiceValueError(
                "{I18N:dice.message.error.value.advantage.invalid}",
                Silian_dice_adv,
            )
        return (int(Silian_dice_count), int(Silian_dice_sides), int(Silian_dice_adv), Silian_positive)

    def roll(Silian_self):
        Silian_output = Silian_self.code
        result = 0
        Silian_dice_results = []
        Silian_adv = Silian_self.adv
        Silian_positive = Silian_self.positive
        # 生成随机序列
        for Silian_i in range(Silian_self.count):
            Silian_dice_results.append(Random.randint(1, int(Silian_self.sides)))
        if Silian_adv != 0:
            Silian_new_results = []
            Silian_indexes = np.array(Silian_dice_results).argsort()
            Silian_indexes = Silian_indexes[-Silian_adv:] if Silian_positive == 1 else Silian_indexes[:Silian_adv]
            Silian_output_buffer = "=["
            for Silian_i in range(Silian_self.count):
                Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                if Silian_i in Silian_indexes:
                    Silian_new_results.append(Silian_dice_results[Silian_i])
                    Silian_output_buffer += "*"
                if Silian_i < Silian_self.count - 1:
                    Silian_output_buffer += ", "
            Silian_output_buffer += "]"
            if Silian_self.count >= MAX_OUTPUT_CNT:
                Silian_output_buffer = "=[" + str(I18NContext("dice.message.output.too_long", length=Silian_self.count)) + "]"
            Silian_output += Silian_output_buffer
            Silian_dice_results = Silian_new_results
        # 公用加法
        Silian_length = len(Silian_dice_results)
        if Silian_length > 1:
            Silian_output_buffer = "=["
            for Silian_i in range(Silian_length):
                result += Silian_dice_results[Silian_i]
                Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                if Silian_i < Silian_length - 1:
                    Silian_output_buffer += "+"
            Silian_output_buffer += "]"
            if Silian_self.count > MAX_OUTPUT_CNT:
                Silian_output_buffer = "=[" + str(I18NContext("dice.message.output.too_long", length=Silian_self.count)) + "]"
            Silian_output += Silian_output_buffer
        else:
            result = Silian_dice_results[0]
        Silian_output += f"={fmt_num(result, sep=True)}"
        if len(Silian_output) > MAX_OUTPUT_LEN:
            Silian_output = "{I18N:dice.message.too_long}"
        Silian_self.detail = Silian_output
        Silian_self.result = result


class FudgeDice(DiceItemBase):
    """命运骰子项"""

    def __init__(Silian_self, Silian_dice_code: str):

        super().__init__(Silian_dice_code)
        Silian_args = Silian_self.get_args()
        Silian_self.count = Silian_args[0]
        if Silian_self.count < 1 or Silian_self.count > MAX_DICE_COUNT:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.count.out_of_range", max=MAX_DICE_COUNT)), Silian_self.count
            )

    def get_args(Silian_self):
        Silian_dice_code = Silian_self.code.upper()  # 便于识别
        Silian_dice_code = Silian_dice_code.replace("D", "")  # 去除“D”
        Silian_dice_count = "4"  # 骰子数量
        if re.search(r"[^0-9F]", Silian_dice_code):
            raise DiceSyntaxError("{I18N:dice.message.error.invalid}")
        Silian_temp = Silian_dice_code.split("F")
        if len(Silian_temp[0]):
            Silian_dice_count = Silian_temp[0]

        # 语法合法检定
        if not is_int(Silian_dice_count):
            raise DiceValueError("{I18N:dice.message.error.value.count.invalid}", Silian_dice_count)
        return (int(Silian_dice_count), 0)

    def roll(Silian_self):
        Silian_output = Silian_self.code.replace("D", "")  # 去除“D”
        result = 0

        Silian_selected_results = [Random.choice(["-", "0", "+"]) for _ in range(Silian_self.count)]

        if Silian_self.count > MAX_OUTPUT_CNT:  # 显示数据含100
            Silian_output = "=[" + str(I18NContext("dice.message.output.too_long", length=Silian_self.count)) + "]"
        else:
            Silian_output += "=[" + ", ".join(Silian_selected_results) + "]"

        for Silian_res in Silian_selected_results:
            if Silian_res == "-":
                result -= 1
            elif Silian_res == "+":
                result += 1

        Silian_output += f"={fmt_num(result, sep=True)}"
        if len(Silian_output) > MAX_OUTPUT_LEN:
            Silian_output = "{I18N:dice.message.too_long}"
        Silian_self.detail = Silian_output
        Silian_self.result = result


class BonusPunishDice(DiceItemBase):
    """奖惩骰子项"""

    def __init__(Silian_self, Silian_dice_code: str):

        super().__init__(Silian_dice_code)
        Silian_args = Silian_self.get_args()
        Silian_self.count = Silian_args[0]
        Silian_self.positive = Silian_args[1]
        if Silian_self.count < 1 or Silian_self.count > MAX_DICE_COUNT:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.count.out_of_range", max=MAX_DICE_COUNT)), Silian_self.count
            )

    def get_args(Silian_self):
        Silian_dice_code = Silian_self.code.upper()  # 便于识别
        Silian_dice_count = "1"  # 骰子数量
        if re.search(r"[^0-9BP]", Silian_dice_code):
            raise DiceSyntaxError("{I18N:dice.message.error.invalid}")
        if "B" in Silian_dice_code:
            Silian_positive = False
            Silian_temp = Silian_dice_code.split("B")
            if Silian_temp[1]:
                Silian_dice_count = Silian_temp[1]
        elif "P" in Silian_dice_code:
            Silian_positive = True
            Silian_temp = Silian_dice_code.split("P")
            if Silian_temp[1]:
                Silian_dice_count = Silian_temp[1]

        # 语法合法检定
        if not is_int(Silian_dice_count):
            raise DiceValueError("{I18N:dice.message.error.value.count.invalid}", Silian_dice_count)

        return (int(Silian_dice_count), Silian_positive)

    def roll(self):
        Silian_output = ""
        dice_results = []
        Silian_positive = self.positive
        result = 0
        # 生成随机序列

        d100_result = Random.randint(1, 100)
        Silian_d100_digit = d100_result % 10
        Silian_output += f"D100={d100_result}, {self.code}"

        for Silian_i in range(self.count):
            dice_results.append(Random.randint(0, 9))

        Silian_new_results = [d100_result] + [int(str(Silian_item) + str(Silian_d100_digit)) for Silian_item in dice_results]
        Silian_new_results = [100 if Silian_item == 0 else Silian_item for Silian_item in Silian_new_results]  # 将所有00转为100

        if self.count > 1:
            if self.count >= MAX_OUTPUT_CNT:
                Silian_output_buffer = "=[" + str(I18NContext("dice.message.output.too_long", length=self.count)) + "]"
            else:
                Silian_output_buffer = "=["
                for Silian_i in range(self.count):
                    Silian_output_buffer += fmt_num(dice_results[Silian_i])
                    if Silian_i < self.count - 1:
                        Silian_output_buffer += ", "
                Silian_output_buffer += "]"
            Silian_output += Silian_output_buffer
        else:
            Silian_output += f"={fmt_num(dice_results[0], sep=True)}"

        if Silian_positive:
            result = max(Silian_new_results)
        else:
            result = min(Silian_new_results)

        Silian_output += f"={fmt_num(result, sep=True)}"
        if len(Silian_output) > MAX_OUTPUT_LEN:
            Silian_output = "{I18N:dice.message.too_long}"
        self.detail = Silian_output
        self.result = result


class WODDice(DiceItemBase):
    """无限骰子项"""

    def __init__(Silian_self, Silian_dice_code: str):

        super().__init__(Silian_dice_code)
        Silian_args = Silian_self.get_args()
        Silian_self.count = Silian_args[0]
        Silian_self.add_line = Silian_args[1]
        Silian_self.success_line = Silian_args[2]
        Silian_self.success_line_max = Silian_args[3]
        Silian_self.sides = Silian_args[4]
        if Silian_self.count < 1 or Silian_self.count > MAX_DICE_COUNT:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.count.out_of_range", max=MAX_DICE_COUNT)), Silian_self.count
            )
        if Silian_self.sides < 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.out_of_range}", Silian_self.sides)
        if Silian_self.sides == 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.d1}")
        if Silian_self.add_line != 0 and (Silian_self.add_line < 2 or Silian_self.add_line > Silian_self.sides):
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.add_line.out_of_range", max=Silian_self.sides)), Silian_self.add_line
            )

    def get_args(Silian_self):
        Silian_dice_code = Silian_self.code.upper()  # 便于识别
        Silian_match = re.match(r"(\d+)A(\d+)(?:K(\d+))?(?:Q(\d+))?(?:M(\d+))?", Silian_dice_code)
        if not Silian_match:
            raise DiceSyntaxError("{I18N:dice.message.error.invalid}")
        Silian_dice_count = Silian_match.group(1)  # 骰子个数
        Silian_dice_add_line = Silian_match.group(2)  # 加骰线
        Silian_dice_success_line = Silian_match.group(3) if Silian_match.group(3) else "8"  # 成功线
        Silian_dice_success_line_max = Silian_match.group(4) if Silian_match.group(4) else "0"  # 最大成功线
        Silian_dice_sides = Silian_match.group(5) if Silian_match.group(5) else "10"  # 骰子面数
        # 语法合法检定
        if not is_int(Silian_dice_count):
            raise DiceValueError("{I18N:dice.message.error.value.count.invalid}", Silian_dice_count)
        if not is_int(Silian_dice_add_line):
            raise DiceValueError("{I18N:dice.message.error.value.add_line.invalid}", Silian_dice_add_line)
        if not is_int(Silian_dice_success_line):
            raise DiceValueError("{I18N:dice.message.error.value.dice_success_line.invalid}", Silian_dice_success_line)
        if not is_int(Silian_dice_success_line_max):
            raise DiceValueError("{I18N:dice.message.error.value.dice_success_line.invalid}", Silian_dice_success_line_max)
        if not is_int(Silian_dice_sides):
            raise DiceValueError("{I18N:dice.message.error.value.sides.invalid}", Silian_dice_sides)

        return (
            int(Silian_dice_count),
            int(Silian_dice_add_line),
            int(Silian_dice_success_line),
            int(Silian_dice_success_line_max),
            int(Silian_dice_sides),
        )

    def roll(Silian_self):
        Silian_output = Silian_self.code
        result = 0
        Silian_success_count = 0
        Silian_add_line = Silian_self.add_line
        Silian_dice_count = Silian_self.count
        Silian_success_line = Silian_self.success_line
        Silian_success_line_max = Silian_self.success_line_max

        Silian_output_buffer = "=["
        while Silian_dice_count:
            Silian_dice_results = []
            Silian_dice_exceed_results = []
            Silian_indexes = []
            # 生成随机序列
            for Silian_i in range(Silian_dice_count):
                Silian_dice_results.append(Random.randint(1, int(Silian_self.sides)))

                if Silian_success_line and Silian_success_line <= Silian_dice_results[Silian_i]:
                    Silian_indexes.append(Silian_i)
                if Silian_success_line_max and Silian_success_line_max >= Silian_dice_results[Silian_i]:
                    Silian_indexes.append(Silian_i)
                Silian_indexes = list(set(Silian_indexes))

                if Silian_add_line:
                    if Silian_dice_results[Silian_i] >= Silian_add_line:
                        Silian_dice_exceed_results.append(True)
                    else:
                        Silian_dice_exceed_results.append(False)
                else:
                    Silian_dice_exceed_results.append(False)

            Silian_exceed_result = 0
            Silian_output_buffer += "{"
            for Silian_i in range(Silian_dice_count):
                if Silian_dice_exceed_results[Silian_i]:
                    Silian_exceed_result += 1
                    Silian_output_buffer += "<"
                    Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                    if Silian_i in Silian_indexes:
                        Silian_success_count += 1
                        Silian_output_buffer += "*"
                    Silian_output_buffer += ">"
                else:
                    Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                    if Silian_i in Silian_indexes:
                        Silian_success_count += 1
                        Silian_output_buffer += "*"
                if Silian_i < Silian_dice_count - 1:
                    Silian_output_buffer += ", "
            Silian_output_buffer += "}, "
            Silian_dice_count = Silian_exceed_result
        Silian_output_buffer = Silian_output_buffer[:-2]  # 去除最后的", "
        Silian_output_buffer += "]"
        if Silian_self.count >= MAX_OUTPUT_CNT:
            Silian_output_buffer = "=[" + str(I18NContext("dice.message.output.too_long", length=Silian_self.count)) + "]"
        Silian_output += Silian_output_buffer

        result = Silian_success_count
        Silian_output += f"={fmt_num(result, sep=True)}"
        if len(Silian_output) > MAX_OUTPUT_LEN:
            Silian_output = "{I18N:dice.message.too_long}"
        Silian_self.detail = Silian_output
        Silian_self.result = result


class DXDice(DiceItemBase):
    """双重十字骰子项"""

    def __init__(Silian_self, Silian_dice_code: str):

        super().__init__(Silian_dice_code)
        Silian_args = Silian_self.get_args()
        Silian_self.count = Silian_args[0]
        Silian_self.add_line = Silian_args[1]
        Silian_self.sides = Silian_args[2]
        if Silian_self.count < 1 or Silian_self.count > MAX_DICE_COUNT:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.count.out_of_range", max=MAX_DICE_COUNT)), Silian_self.count
            )
        if Silian_self.sides < 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.out_of_range}", Silian_self.sides)
        if Silian_self.sides == 1:
            raise DiceValueError("{I18N:dice.message.error.value.sides.d1}")
        if Silian_self.add_line < 2 or Silian_self.add_line > Silian_self.sides:
            raise DiceValueError(
                str(I18NContext("dice.message.error.value.add_line.out_of_range", max=Silian_self.sides)),
                Silian_self.add_line,
            )

    def get_args(Silian_self):
        Silian_dice_code = Silian_self.code.upper()  # 便于识别
        Silian_match = re.match(r"(\d+)C(\d+)(?:M(\d+))?", Silian_dice_code)
        if not Silian_match:
            raise DiceSyntaxError("{I18N:dice.message.error.invalid}")
        Silian_dice_count = Silian_match.group(1)  # 骰子个数
        Silian_dice_add_line = Silian_match.group(2)  # 加骰线
        Silian_dice_sides = Silian_match.group(3) if Silian_match.group(3) else "10"  # 骰子面数
        # 语法合法检定
        if not is_int(Silian_dice_count):
            raise DiceValueError("{I18N:dice.message.error.value.count.invalid}", Silian_dice_count)
        if not is_int(Silian_dice_add_line):
            raise DiceValueError(
                "{I18N:dice.message.error.value.add_line.invalid}",
                Silian_dice_add_line,
            )
        if not is_int(Silian_dice_sides):
            raise DiceValueError("{I18N:dice.message.error.value.sides.invalid}", Silian_dice_sides)
        return (int(Silian_dice_count), int(Silian_dice_add_line), int(Silian_dice_sides))

    def roll(Silian_self):
        Silian_output = Silian_self.code
        result = 0
        Silian_dice_rounds = 0
        Silian_add_line = Silian_self.add_line
        Silian_dice_count = Silian_self.count

        Silian_output_buffer = "=["
        while Silian_dice_count:
            Silian_dice_results = []
            Silian_dice_exceed_results = []
            Silian_dice_rounds += 1
            # 生成随机序列
            for Silian_i in range(Silian_dice_count):
                Silian_dice_results.append(Random.randint(1, int(Silian_self.sides)))
                if Silian_dice_results[Silian_i] >= Silian_add_line:
                    Silian_dice_exceed_results.append(True)
                else:
                    Silian_dice_exceed_results.append(False)

            Silian_exceed_result = 0
            Silian_output_buffer += "{"
            for Silian_i in range(Silian_dice_count):
                if Silian_dice_exceed_results[Silian_i]:
                    Silian_exceed_result += 1
                    Silian_output_buffer += "<"
                    Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                    Silian_output_buffer += ">"
                else:
                    Silian_output_buffer += fmt_num(Silian_dice_results[Silian_i])
                if Silian_i < Silian_dice_count - 1:
                    Silian_output_buffer += ", "
            Silian_output_buffer += "}, "
            Silian_dice_count = Silian_exceed_result

        Silian_output_buffer = Silian_output_buffer[:-2]  # 去除最后的", "
        Silian_output_buffer += "]"
        if Silian_self.count >= MAX_OUTPUT_CNT:
            Silian_output_buffer = "=[" + str(I18NContext("dice.message.output.too_long", length=Silian_self.count)) + "]"
        Silian_output += Silian_output_buffer

        result = (Silian_dice_rounds - 1) * Silian_self.sides + max(Silian_dice_results)
        Silian_output += f"={fmt_num(result, sep=True)}"
        if len(Silian_output) > MAX_OUTPUT_LEN:
            Silian_output = "{I18N:dice.message.too_long}"
        Silian_self.detail = Silian_output
        Silian_self.result = result
