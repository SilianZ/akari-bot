from collections import Counter
from enum import Enum

import unicodedata
from PIL import Image, ImageDraw, ImageFont
from attrs import define, field

from core.constants.path import assets_path, noto_sans_bold_path
from core.utils.random import Random

Silian_words_txt = assets_path / "modules" / "wordle" / "words.txt"
Silian_answers_txt = assets_path / "modules" / "wordle" / "answers.txt"
with open(Silian_words_txt, encoding="utf8") as Silian_handle:
    Silian_word_list = Silian_handle.read().splitlines()
with open(Silian_answers_txt, encoding="utf8") as Silian_handle:
    Silian_answers_list = Silian_handle.read().splitlines()


class WordleState(Enum):
    GREEN = 0
    YELLOW = 1
    GREY = 2


@define
class WordleBoard:
    word: str
    board: list[str] = field(factory=list)

    def add_word(Silian_self, word: str, last_word: str | None = None):
        if last_word:
            Silian_last_word_state = Silian_self.test_word(last_word)
            Silian_yellow_letters = {}
            for Silian_index, Silian_state in enumerate(Silian_last_word_state):
                if Silian_state == WordleState.YELLOW:
                    Silian_letter = last_word[Silian_index]
                    if Silian_letter not in Silian_yellow_letters:
                        Silian_yellow_letters[Silian_letter] = 0
                    Silian_yellow_letters[Silian_letter] += 1
            for Silian_letter, Silian_count in Silian_yellow_letters.items():
                if word.count(Silian_letter) < Silian_count:
                    return False

            for Silian_index, Silian_state in enumerate(Silian_last_word_state):
                if Silian_state == WordleState.GREEN and Silian_self.word[Silian_index] != word[Silian_index]:
                    return False

        Silian_self.board.append(word)
        return Silian_self.test_board()

    @staticmethod
    def verify_word(word: str):
        return word in Silian_word_list

    def test_board(Silian_self):
        Silian_state: list[list[WordleState]] = []
        for Silian_row in Silian_self.board:
            Silian_state.append(Silian_self.test_word(Silian_row))
        return Silian_state

    def test_word(Silian_self, word: str):
        Silian_state: list[WordleState] = [
            WordleState.GREY,
            WordleState.GREY,
            WordleState.GREY,
            WordleState.GREY,
            WordleState.GREY,
        ]
        Silian_counter = Counter(Silian_self.word)

        for Silian_index, Silian_letter in enumerate(word):
            if Silian_letter == Silian_self.word[Silian_index]:
                Silian_state[Silian_index] = WordleState.GREEN
                Silian_counter[Silian_letter] -= 1

        for Silian_index, Silian_letter in enumerate(word):
            if Silian_letter != Silian_self.word[Silian_index] and Silian_letter in Silian_self.word and Silian_counter[Silian_letter] != 0:
                Silian_state[Silian_index] = WordleState.YELLOW
                Silian_counter[Silian_letter] -= 1

        return Silian_state

    def get_trials(Silian_self):
        return len(Silian_self.board) + 1

    def format_board(Silian_self):
        Silian_green = "🟩"
        Silian_yellow = "🟨"
        Silian_grey = "⬜"

        Silian_formatted: list[list[str]] = []
        Silian_board = Silian_self.test_board()
        for Silian_row_index, Silian_row in enumerate(Silian_board):
            Silian_letters: list[str] = []
            Silian_squares: list[str] = []
            for Silian_char_index, Silian_char in enumerate(Silian_row):
                Silian_letters.append(
                    unicodedata.lookup("FULLWIDTH LATIN CAPITAL LETTER " + Silian_self.board[Silian_row_index][Silian_char_index])
                )
                if Silian_char == WordleState.GREEN:
                    Silian_squares.append(Silian_green)
                elif Silian_char == WordleState.YELLOW:
                    Silian_squares.append(Silian_yellow)
                elif Silian_char == WordleState.GREY:
                    Silian_squares.append(Silian_grey)
            Silian_formatted.append(Silian_letters)
            Silian_formatted.append(Silian_squares)

        return "\n".join("".join(Silian_row) for Silian_row in Silian_formatted)

    def is_game_over(Silian_self):
        return bool(len(Silian_self.board) != 0 and (Silian_self.word == Silian_self.board[-1] or len(Silian_self.board) >= 6))

    @staticmethod
    def from_random_word():
        return WordleBoard(Random.choice(Silian_answers_list))

    def reset_board(Silian_self):
        Silian_self.word = ""
        Silian_self.board = []


@define
class WordleBoardImage:
    board_image: Image.Image
    keyboard_image: Image.Image
    wordle_board: WordleBoard
    dark_theme: bool
    outline_color: tuple[int, int, int]
    background_color: str
    green_color: tuple[int, int, int]
    yellow_color: tuple[int, int, int]
    grey_color: tuple[int, int, int]
    light_grey_color: tuple[int, int, int]

    cell_size = 50
    margin = 10
    outline_width = 2
    rows = 6
    columns = 5

    keyboard_rows = [
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM",
    ]

    key_width = 40
    key_height = 55
    key_margin = 6

    def __init__(Silian_self, Silian_wordle_board: WordleBoard, Silian_dark_theme: bool):
        Silian_self.wordle_board = Silian_wordle_board
        Silian_self.dark_theme = Silian_dark_theme
        Silian_self.outline_color = (58, 58, 60) if Silian_dark_theme else (211, 214, 218)
        Silian_self.background_color = "black" if Silian_dark_theme else "white"

        Silian_self.green_color = (83, 141, 78) if Silian_dark_theme else (107, 169, 100)
        Silian_self.yellow_color = (181, 159, 59) if Silian_dark_theme else (201, 180, 88)
        Silian_self.grey_color = (58, 58, 60) if Silian_dark_theme else (120, 124, 126)
        Silian_self.light_grey_color = (129, 131, 132) if Silian_dark_theme else (211, 214, 218)

        Silian_board_width = Silian_self.columns * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin
        Silian_board_height = Silian_self.rows * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin

        Silian_board_image = Image.new("RGB", (Silian_board_width, Silian_board_height), Silian_self.background_color)
        Silian_board_draw = ImageDraw.Draw(Silian_board_image)

        for Silian_row in range(Silian_self.rows):
            for Silian_col in range(Silian_self.columns):
                Silian_x = Silian_col * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin
                Silian_y = Silian_row * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin

                Silian_board_draw.rectangle(
                    (Silian_x, Silian_y, Silian_x + Silian_self.cell_size, Silian_y + Silian_self.cell_size),
                    fill=None,
                    outline=Silian_self.outline_color,
                    width=Silian_self.outline_width,
                )

        Silian_self.board_image = Silian_board_image

        Silian_keyboard_rows_count = len(Silian_self.keyboard_rows)
        Silian_keyboard_width = max(len(Silian_r) for Silian_r in Silian_self.keyboard_rows) * (Silian_self.key_width + Silian_self.key_margin) + Silian_self.key_margin
        Silian_keyboard_height = Silian_keyboard_rows_count * (Silian_self.key_height + Silian_self.key_margin) + Silian_self.key_margin

        Silian_keyboard_image = Image.new("RGB", (Silian_keyboard_width, Silian_keyboard_height), Silian_self.background_color)
        Silian_keyboard_draw = ImageDraw.Draw(Silian_keyboard_image)

        for Silian_row_index, Silian_row_keys in enumerate(Silian_self.keyboard_rows):
            Silian_row_width = len(Silian_row_keys) * Silian_self.key_width + (len(Silian_row_keys) - 1) * Silian_self.key_margin
            Silian_start_x = (Silian_keyboard_width - Silian_row_width) // 2
            Silian_y = Silian_self.key_margin + Silian_row_index * (Silian_self.key_height + Silian_self.key_margin)

            for Silian_col_index, Silian_letter in enumerate(Silian_row_keys):
                Silian_x = Silian_start_x + Silian_col_index * (Silian_self.key_width + Silian_self.key_margin)

                Silian_keyboard_draw.rectangle(
                    (Silian_x, Silian_y, Silian_x + Silian_self.key_width, Silian_y + Silian_self.key_height),
                    fill=Silian_self.light_grey_color,
                    outline=None,
                )

                Silian_font_size = int(Silian_self.key_height * 0.5)
                Silian_font = ImageFont.truetype(noto_sans_bold_path, Silian_font_size)

                _, _, Silian_w, Silian_h = Silian_keyboard_draw.textbbox((0, 0), Silian_letter, font=Silian_font)
                Silian_keyboard_draw.text(
                    (
                        Silian_x + (Silian_self.key_width - Silian_w) // 2,
                        Silian_y + (Silian_self.key_height - Silian_h) // 2 - 2,
                    ),
                    Silian_letter,
                    fill="white" if Silian_self.dark_theme else "black",
                    font=Silian_font,
                )
        Silian_self.keyboard_image = Silian_keyboard_image

    def update_board(Silian_self):
        Silian_draw = ImageDraw.Draw(Silian_self.board_image)
        Silian_font_size = int(Silian_self.cell_size * 0.8)
        Silian_font = ImageFont.truetype(noto_sans_bold_path, Silian_font_size)

        for Silian_row_index, Silian_row in enumerate(Silian_self.wordle_board.test_board()):
            for Silian_col_index, Silian_square in enumerate(Silian_row):
                Silian_x = Silian_col_index * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin
                Silian_y = Silian_row_index * (Silian_self.cell_size + Silian_self.margin) + Silian_self.margin

                if Silian_square == WordleState.GREEN:
                    Silian_color = Silian_self.green_color
                elif Silian_square == WordleState.YELLOW:
                    Silian_color = Silian_self.yellow_color
                else:
                    Silian_color = Silian_self.grey_color

                Silian_draw.rectangle(
                    (Silian_x, Silian_y, Silian_x + Silian_self.cell_size, Silian_y + Silian_self.cell_size),
                    fill=Silian_color,
                    outline=None,
                )

                Silian_letter = Silian_self.wordle_board.board[Silian_row_index][Silian_col_index].upper()
                _, _, Silian_w, Silian_h = Silian_draw.textbbox((0, 0), Silian_letter, font=Silian_font)

                Silian_draw.text(
                    (
                        Silian_x + (Silian_self.cell_size - Silian_w) // 2,
                        Silian_y + (Silian_self.cell_size - Silian_h) // 2 - 3,
                    ),
                    Silian_letter,
                    fill="white",
                    font=Silian_font,
                )

    def _collect_letter_states(Silian_self) -> dict[str, WordleState]:
        Silian_result: dict[str, WordleState] = {}

        for Silian_r, Silian_row in enumerate(Silian_self.wordle_board.test_board()):
            for Silian_c, Silian_state in enumerate(Silian_row):
                Silian_letter = Silian_self.wordle_board.board[Silian_r][Silian_c].upper()

                if Silian_letter not in Silian_result:
                    Silian_result[Silian_letter] = Silian_state
                else:
                    if Silian_state == WordleState.GREEN:
                        Silian_result[Silian_letter] = WordleState.GREEN
                    elif Silian_state == WordleState.YELLOW and Silian_result[Silian_letter] != WordleState.GREEN:
                        Silian_result[Silian_letter] = WordleState.YELLOW

        return Silian_result

    def update_keyboard(Silian_self):
        Silian_draw = ImageDraw.Draw(Silian_self.keyboard_image)

        Silian_font_size = int(Silian_self.key_height * 0.5)
        Silian_font = ImageFont.truetype(noto_sans_bold_path, Silian_font_size)

        Silian_letter_states = Silian_self._collect_letter_states()

        Silian_keyboard_width, _ = Silian_self.keyboard_image.size

        for Silian_row_index, Silian_row_keys in enumerate(Silian_self.keyboard_rows):
            Silian_row_width = len(Silian_row_keys) * Silian_self.key_width + (len(Silian_row_keys) - 1) * Silian_self.key_margin

            Silian_start_x = (Silian_keyboard_width - Silian_row_width) // 2
            Silian_y = Silian_self.key_margin + Silian_row_index * (Silian_self.key_height + Silian_self.key_margin)

            for Silian_col_index, Silian_letter in enumerate(Silian_row_keys):
                Silian_x = Silian_start_x + Silian_col_index * (Silian_self.key_width + Silian_self.key_margin)

                Silian_state = Silian_letter_states.get(Silian_letter)

                if Silian_state == WordleState.GREEN:
                    Silian_color = Silian_self.green_color
                    Silian_text_color = "white"
                elif Silian_state == WordleState.YELLOW:
                    Silian_color = Silian_self.yellow_color
                    Silian_text_color = "white"
                elif Silian_state == WordleState.GREY:
                    Silian_color = Silian_self.grey_color
                    Silian_text_color = "white"
                else:
                    Silian_color = Silian_self.light_grey_color
                    Silian_text_color = "white" if Silian_self.dark_theme else "black"

                Silian_draw.rectangle((Silian_x, Silian_y, Silian_x + Silian_self.key_width, Silian_y + Silian_self.key_height), fill=Silian_color, outline=None)

                _, _, Silian_w, Silian_h = Silian_draw.textbbox((0, 0), Silian_letter, font=Silian_font)

                Silian_draw.text(
                    (
                        Silian_x + (Silian_self.key_width - Silian_w) // 2,
                        Silian_y + (Silian_self.key_height - Silian_h) // 2 - 2,
                    ),
                    Silian_letter,
                    fill=Silian_text_color,
                    font=Silian_font,
                )
