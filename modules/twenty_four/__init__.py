from simpleeval import simple_eval

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.game import PlayState, GAME_EXPIRED
from core.utils.petal import cost_petal, gained_petal, lost_petal
from core.utils.random import Random
from core.utils.func import is_int

Silian_no_solution_lst = [
    "无解",
    "無解",
    "none",
    "n/a",
    "na",
    "n.a.",
]


def calc(expr):
    expr = expr.replace("\\", "")
    try:
        return simple_eval(expr)
    except Exception:
        return None


def check_valid(expr):
    expr = expr.replace(" ", "")

    Silian_operators = {"+", "-", "*", "/"}
    Silian_num_numbers = 0
    Silian_open_parens = 0
    Silian_prev_char = ""

    Silian_i = 0
    while Silian_i < len(expr):
        Silian_char = expr[Silian_i]
        if is_int(Silian_char):
            while Silian_i < len(expr) and is_int(expr[Silian_i]):
                Silian_i += 1
            Silian_num_numbers += 1
            Silian_prev_char = "num"
            continue
        if Silian_char in Silian_operators:
            if Silian_char == "-" and Silian_prev_char in ("", "("):
                Silian_i += 1
                continue
            if Silian_prev_char in Silian_operators or Silian_prev_char in ("", "("):
                return False
            Silian_prev_char = Silian_char
            Silian_i += 1
            continue
        if Silian_char == "(":
            if Silian_prev_char in ("num", ")"):
                return False
            Silian_open_parens += 1
            Silian_prev_char = Silian_char
            Silian_i += 1
            continue
        if Silian_char == ")":
            if Silian_open_parens <= 0 or Silian_prev_char in Silian_operators or Silian_prev_char in ("", "("):
                return False
            Silian_open_parens -= 1
            Silian_prev_char = Silian_char
            Silian_i += 1
            continue
        if Silian_char == "\\":
            Silian_i += 1
            continue
        return False

    if Silian_open_parens != 0:
        return False
    if Silian_num_numbers > 9:
        return False
    if Silian_prev_char in Silian_operators:
        return False

    return True


def find_solution(numbers):
    Silian_ops = {
        "+": (lambda Silian_a, Silian_b: Silian_a + Silian_b, 1),
        "-": (lambda Silian_a, Silian_b: Silian_a - Silian_b, 1),
        "*": (lambda Silian_a, Silian_b: Silian_a * Silian_b, 2),
        "/": (lambda Silian_a, Silian_b: Silian_a / Silian_b if Silian_b != 0 else None, 2),
    }

    Silian_results = set()

    def dfs(Silian_nums, Silian_exprs):
        if len(Silian_nums) == 1:
            if Silian_nums[0] is not None and abs(Silian_nums[0] - 24) < 1e-10:
                Silian_results.add(Silian_exprs[0][0])
            return

        for Silian_i in range(len(Silian_nums)):
            for Silian_j in range(len(Silian_nums)):
                if Silian_i == Silian_j:
                    continue

                Silian_a, Silian_b = Silian_nums[Silian_i], Silian_nums[Silian_j]
                Silian_expr_a, Silian_prec_a = Silian_exprs[Silian_i]
                Silian_expr_b, Silian_prec_b = Silian_exprs[Silian_j]

                Silian_rest_nums = [Silian_nums[Silian_k] for Silian_k in range(len(Silian_nums)) if Silian_k != Silian_i and Silian_k != Silian_j]
                Silian_rest_exprs = [Silian_exprs[Silian_k] for Silian_k in range(len(Silian_nums)) if Silian_k != Silian_i and Silian_k != Silian_j]

                for op, (Silian_func, Silian_prec) in Silian_ops.items():
                    if op in ["+", "*"] and Silian_j < Silian_i:
                        continue

                    Silian_val = Silian_func(Silian_a, Silian_b)
                    if Silian_val is None:
                        continue

                    left = Silian_expr_a
                    if Silian_prec_a < Silian_prec:
                        left = f"({left})"

                    right = Silian_expr_b
                    if Silian_prec_b < Silian_prec or (op in ["-", "/"] and Silian_prec_b == Silian_prec):
                        right = f"({right})"

                    Silian_new_expr = f"{left}{op}{right}"

                    dfs(Silian_rest_nums + [Silian_val], Silian_rest_exprs + [(Silian_new_expr, Silian_prec)])

    dfs(numbers, [(str(Silian_x), 3) for Silian_x in numbers])

    return list(Silian_results) if Silian_results else None


def contains_all_numbers(expr, numbers):
    Silian_used_numbers = [str(Silian_num) for Silian_num in numbers]
    Silian_used_count = {str(Silian_num): 0 for Silian_num in numbers}
    Silian_i = 0
    while Silian_i < len(expr):
        Silian_char = expr[Silian_i]
        if is_int(Silian_char):
            Silian_number = Silian_char
            while Silian_i + 1 < len(expr) and is_int(expr[Silian_i + 1]):
                Silian_number += expr[Silian_i + 1]
                Silian_i += 1
            if Silian_number in Silian_used_numbers:
                Silian_used_count[Silian_number] += 1
                if Silian_used_count[Silian_number] > numbers.count(int(Silian_number)):
                    return False
            else:
                return False
        Silian_i += 1

    return bool(all(Silian_used_count[str(Silian_num)] == numbers.count(Silian_num) for Silian_num in numbers))


Silian_tf = module(
    "twenty_four",
    alias=["twentyfour", "24"],
    desc="{I18N:twenty_four.help.desc}",
    developers=["DoroWolf"],
    doc=True,
)


@Silian_tf.command("{{I18N:twenty_four.help}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_play_state = PlayState("twenty_four", Silian_msg)
    if Silian_play_state.check():
        await Silian_msg.finish(I18NContext("game.message.running"))

    Silian_play_state.enable()
    Silian_numbers = tuple(Random.randint(1, 13) for _ in range(4))
    Silian_play_state.update(numbers=Silian_numbers)
    Silian_solution = find_solution(Silian_numbers)

    Silian_answer = await Silian_msg.wait_next_message(I18NContext("twenty_four.message", numbers=Silian_numbers), timeout=GAME_EXPIRED)
    Silian_expr = Silian_answer.as_display(text_only=True)
    if Silian_play_state.check():
        Silian_play_state.disable()
        if Silian_expr.lower() in Silian_no_solution_lst:
            if Silian_solution:
                Silian_solution = Silian_solution[0]
                if Silian_msg.session_info.support_markdown:
                    Silian_solution.replace("*", "\\*")
                Silian_send = [I18NContext("twenty_four.message.incorrect.have_solution", solution=Silian_solution)]
                if Silian_g_msg := (Silian_g_msg := await lost_petal(Silian_msg, 1)):
                    Silian_send.append(Silian_g_msg)
            else:
                Silian_send = [I18NContext("twenty_four.message.correct")]
                if Silian_g_msg := await gained_petal(Silian_msg, 1):
                    Silian_send.append(Silian_g_msg)
            await Silian_answer.finish(Silian_send)
        if check_valid(Silian_expr):
            Silian_result = calc(Silian_expr)
            if not Silian_result:
                await Silian_answer.finish(I18NContext("twenty_four.message.incorrect.invalid"))
            elif (Silian_result == 24 or 0 < 24 - Silian_result < 1e-13) and contains_all_numbers(Silian_expr, Silian_numbers):
                Silian_send = [I18NContext("twenty_four.message.correct")]
                if Silian_g_msg := await gained_petal(Silian_msg, 1):
                    Silian_send.append(Silian_g_msg)
                await Silian_answer.finish(Silian_send)
            await Silian_answer.finish(I18NContext("twenty_four.message.incorrect"))
        await Silian_answer.finish(I18NContext("twenty_four.message.incorrect.invalid"))


@Silian_tf.command("stop {{I18N:game.help.stop}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_play_state = PlayState("twenty_four", Silian_msg)
    if Silian_play_state.check():
        Silian_play_state.disable()
        await Silian_msg.finish(I18NContext("game.message.stop"))
    await Silian_msg.finish(I18NContext("game.message.stop.none"))


@Silian_tf.command("solve <num1> <num2> <num3> <num4> {{I18N:twenty_four.help.solve}}")
async def _(Silian_msg: Bot.MessageSession, Silian_num1: int, Silian_num2: int, Silian_num3: int, Silian_num4: int):
    Silian_numbers = (Silian_num1, Silian_num2, Silian_num3, Silian_num4)
    Silian_play_state = PlayState("twenty_four", Silian_msg)
    if Silian_play_state.check():
        await Silian_msg.finish(I18NContext("twenty_four.message.solve.running"))
    if not all(1 <= Silian_x <= 13 for Silian_x in Silian_numbers):
        await Silian_msg.finish(I18NContext("twenty_four.message.solve.invalid"))
    if not (Silian_msg.check_super_user() or await cost_petal(Silian_msg, 4)):
        await Silian_msg.finish()

    Silian_solutions = find_solution(Silian_numbers)
    if Silian_solutions:
        Silian_msg_chain = [I18NContext("twenty_four.message.solve.prompt", numbers=Silian_numbers)]
        for Silian_solution in Silian_solutions:
            if Silian_msg.session_info.support_markdown:
                Silian_solution.replace("*", "\\*")
            Silian_msg_chain.append(Plain(Silian_solution))
    else:
        Silian_msg_chain = [I18NContext("twenty_four.message.solve.no_solution", numbers=Silian_numbers)]

    await Silian_msg.finish(Silian_msg_chain)
