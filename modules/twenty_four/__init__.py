import itertools
import random

from simpleeval import simple_eval

from core.builtins import Bot
from core.component import module

no_solution = ['无解', '無解', 'none', 'n/a']


def calc(expression):
    try:
        return simple_eval(expression)
    except BaseException:
        return None


def is_valid(expression):
    operators = ['+', '-', '*', '/', '(', ')']
    numbers = [str(i) for i in range(1, 14)]
    valid_chars = numbers + operators
    valid_chars_set = set(valid_chars)

    i = 0
    num_numbers = 0
    while i < len(expression):
        char = expression[i]

        if char.isdigit():
            while i < len(expression) and expression[i].isdigit():
                i += 1
            num_numbers += 1

        elif char in valid_chars_set:
            i += 1
            if i < len(expression) and expression[i] == ' ':
                i += 1
                if i < len(expression) and expression[i] == ' ':
                    return False
            continue

        elif char == ' ':
            i += 1
            if i < len(expression) and expression[i] == ' ':
                return False

        else:
            return False

    if num_numbers > 9:
        return False

    return True


async def has_solution(numbers):
    permutations = list(itertools.permutations(numbers))
    operators = ['+', '-', '*', '/']
    expressions = list(itertools.product(operators, repeat=3))

    for perm in permutations:
        for expr in expressions:  # 穷举就完事了
            exp = '((( {} {} {} ) {} {} ) {} {} )'.format(perm[0], expr[0], perm[1], expr[1], perm[2], expr[2], perm[3])
            if calc(exp) == 24:
                return True
            exp = '(( {} {} {} ) {} ( {} {} {} ))'.format(perm[0], expr[0], perm[1], expr[1], perm[2], expr[2], perm[3])
            if calc(exp) == 24:
                return True
            exp = '( {} {} ( {} {} ( {} {} {} )))'.format(perm[0], expr[0], perm[1], expr[1], perm[2], expr[2], perm[3])
            if calc(exp) == 24:
                return True
            exp = '( {} {} ( {} {} {} ) {} {} )'.format(perm[0], expr[0], perm[1], expr[1], perm[2], expr[2], perm[3])
            if calc(exp) == 24:
                return True
    return False


def contains_all_numbers(expression, numbers):
    used_numbers = [str(num) for num in numbers]
    i = 0
    while i < len(expression):
        char = expression[i]
        if char.isdigit():
            number = char
            while i + 1 < len(expression) and expression[i + 1].isdigit():
                number += expression[i + 1]
                i += 1
            if number in used_numbers:
                used_numbers.remove(number)
        i += 1

    return len(used_numbers) == 0


tf = module('twenty_four', alias=['twentyfour', '24'],
            desc='{twenty_four.help.desc}', developers=['DoroWolf'])
play_state = {}


@tf.command('{{twenty_four.help}}')
async def _(msg: Bot.MessageSession):
    if msg.target.target_id in play_state and play_state[msg.target.target_id]['active']:
        await msg.finish(msg.locale.t('twenty_four.message.running'))
    play_state.update({msg.target.target_id: {'active': True}})

    numbers = [random.randint(1, 13) for _ in range(4)]
    has_solution_flag = await has_solution(numbers)

    answer = await msg.wait_next_message(msg.locale.t('twenty_four.message', numbers=numbers))
    expression = answer.as_display(text_only=True)
    if play_state[msg.target.target_id]['active']:
        if expression.lower() in no_solution:
            if has_solution_flag:
                await answer.send_message(msg.locale.t('twenty_four.message.incorrect.have_solution'))
            else:
                await answer.send_message(msg.locale.t('twenty_four.message.correct'))
        elif is_valid(expression):
            result = calc(expression)
            if result == 24 and contains_all_numbers(expression, numbers):
                await answer.send_message(msg.locale.t('twenty_four.message.correct'))
            else:
                await answer.send_message(msg.locale.t('twenty_four.message.incorrect'))
        else:
            await answer.send_message(msg.locale.t('twenty_four.message.incorrect.error'))
        play_state[msg.target.target_id]['active'] = False


@tf.command('stop {{twenty_four.stop.help}}')
async def s(msg: Bot.MessageSession):
    state = play_state.get(msg.target.target_id, False)
    if state:
        if state['active']:
            play_state[msg.target.target_id]['active'] = False
            await msg.send_message(msg.locale.t('twenty_four.stop.message'))
        else:
            await msg.send_message(msg.locale.t('twenty_four.stop.message.none'))
    else:
        await msg.send_message(msg.locale.t('twenty_four.stop.message.none'))
