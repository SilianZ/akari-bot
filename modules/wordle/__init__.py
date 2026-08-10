from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as BImage, Plain
from core.component import module
from core.cooldown import CoolDown
from core.config import Config
from core.logger import Logger
from core.game import PlayState, GAME_EXPIRED
from core.utils.petal import gained_petal
from .board import WordleBoard, WordleBoardImage

Silian_text_mode = Config("wordle_disable_image", False, table_name="module_wordle")

Silian_wordle = module(
    "wordle",
    desc="{I18N:wordle.help.desc}",
    doc=True,
    developers=["Dianliang233", "DoroWolf"],
)


@Silian_wordle.command()
@Silian_wordle.command(
    "[--hard] [--trial] {{I18N:wordle.help}}",
    options_desc={"--hard": "{I18N:wordle.help.option.hard}", "--trial": "{I18N:wordle.help.option.trial}"},
)
async def _(Silian_msg: Bot.MessageSession):
    Silian_hard_mode = bool(Silian_msg.parsed_msg and Silian_msg.parsed_msg.get("--hard", False))
    Silian_trial = bool(Silian_msg.parsed_msg and Silian_msg.parsed_msg.get("--trial", False))

    Silian_play_state = PlayState("wordle", Silian_msg)
    if Silian_play_state.check():
        await Silian_msg.finish(I18NContext("game.message.running"))
    if PlayState("wordle", Silian_msg).check():
        await Silian_msg.finish(I18NContext("wordle.message.occupied"))

    Silian_qc = CoolDown("wordle", Silian_msg, 180)
    if not Silian_msg.check_super_user():
        Silian_c = Silian_qc.check()
        if Silian_c != 0:
            await Silian_msg.finish(I18NContext("message.cooldown", time=int(Silian_c)))

    board = WordleBoard.from_random_word()
    Silian_last_word = None
    Silian_board_image = WordleBoardImage(
        wordle_board=board, dark_theme=Silian_msg.session_info.target_info.target_data.get("wordle_dark_theme")
    )

    Silian_play_state.enable()
    Silian_play_state.update(answer=board.word)
    Logger.info(f"Answer: {board.word}")
    Silian_start_msg = []
    if not Silian_text_mode:
        Silian_start_msg.append(BImage(Silian_board_image.board_image))
        Silian_start_msg.append(BImage(Silian_board_image.keyboard_image))
    Silian_start_msg.append(I18NContext("wordle.message.start"))
    if Silian_hard_mode:
        Silian_start_msg.append(I18NContext("wordle.message.start.hard"))
    if Silian_trial:
        Silian_start_msg.append(I18NContext("wordle.message.start.trial"))
    await Silian_msg.send_message(Silian_start_msg)

    while board.get_trials() <= 6 and Silian_play_state.check() and not board.is_game_over():
        if Silian_trial:
            Silian_wait = await Silian_msg.wait_next_message(timeout=GAME_EXPIRED)
        else:
            Silian_wait = await Silian_msg.wait_anyone(timeout=GAME_EXPIRED)
        word = Silian_wait.as_display(text_only=True).strip().lower()
        if len(word) != 5 or not (word.isalpha() and word.isascii()):
            continue
        if not board.verify_word(word):
            await Silian_wait.send_message(I18NContext("wordle.message.not_a_word"))
            continue
        if not board.add_word(word, Silian_last_word):
            await Silian_wait.send_message(I18NContext("wordle.message.hard.not_matched"))
            continue
        if Silian_hard_mode:
            Silian_last_word = word
        Silian_board_image.update_board()
        Silian_board_image.update_keyboard()

        if not board.is_game_over() and board.get_trials() <= 6:
            Logger.info(f"{word} != {board.word}, attempt {board.get_trials() - 1}")
            if Silian_text_mode:
                await Silian_wait.send_message(board.format_board())
            else:
                await Silian_wait.send_message([BImage(Silian_board_image.board_image), BImage(Silian_board_image.keyboard_image)])

    if board.is_game_over():
        Silian_play_state.disable()
        Silian_attempt = board.get_trials() - 1
        Silian_g_msg = [I18NContext("wordle.message.finish", answer=board.word)]
        if board.board[-1] == board.word:
            Silian_g_msg = [I18NContext("wordle.message.finish.success", attempt=Silian_attempt)]
            if Silian_trial:
                Silian_petal = 2 if Silian_attempt <= 3 else 1
                Silian_petal += 1 if Silian_hard_mode else 0
                if Silian_reward := await gained_petal(Silian_msg, Silian_petal):
                    Silian_g_msg.append(Silian_reward)
        Silian_qc.reset()
        if Silian_text_mode:
            await Silian_msg.finish([Plain(board.format_board())] + Silian_g_msg, quote=False)
        await Silian_msg.finish([BImage(Silian_board_image.board_image), BImage(Silian_board_image.keyboard_image)] + Silian_g_msg, quote=False)


@Silian_wordle.command("stop {{I18N:game.help.stop}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_play_state = PlayState("wordle", Silian_msg)
    if Silian_play_state.check():
        Silian_play_state.disable()
        CoolDown("wordle", Silian_msg, 180).reset()
        await Silian_msg.finish(I18NContext("wordle.message.stop", answer=Silian_play_state.get("answer")))
    await Silian_msg.finish(I18NContext("game.message.stop.none"))


@Silian_wordle.command("theme {{I18N:wordle.help.theme}}", load=not Silian_text_mode)
async def _(Silian_msg: Bot.MessageSession):
    Silian_dark_theme = Silian_msg.session_info.target_info.target_data.get("wordle_dark_theme")

    if Silian_dark_theme:
        await Silian_msg.session_info.target_info.edit_target_data("wordle_dark_theme", False)
        await Silian_msg.finish(I18NContext("wordle.message.theme.disable"))
    await Silian_msg.session_info.target_info.edit_target_data("wordle_dark_theme", True)
    await Silian_msg.finish(I18NContext("wordle.message.theme.enable"))
