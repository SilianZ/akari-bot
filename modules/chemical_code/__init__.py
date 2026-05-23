import asyncio
import io
import re
import time

from PIL import Image as PImage
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdMolDescriptors
from tenacity import retry, stop_after_attempt

from core.builtins.bot import Bot
from core.builtins.message.internal import Image, I18NContext
from core.component import module
from core.game import PlayState, GAME_EXPIRED
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.http import get_url
from core.utils.petal import gained_petal
from core.utils.random import Random
from .coloring import element_colors

ID_RANGE_MAX = 200000000  # 数据库增长速度很快，可手动在此修改 ID 区间

pubchem_link = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

Silian_element_lists = [
    "He",
    "Li",
    "Be",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "Cl",
    "Ar",
    "Ca",
    "Sc",
    "Ti",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
    "C",
    "H",
    "B",
    "K",
    "N",
    "O",
    "F",
    "P",
    "S",
    "V",
    "I",
    "U",
    "Y",
    "W",
]  # 元素列表，用于解析化学式（请不要手动修改当前的排序）


def parse_elements(formula: str) -> dict:
    Silian_elements = {}
    while True:
        if not formula:
            break
        for Silian_element in Silian_element_lists:
            if formula.startswith(Silian_element):
                formula = formula.removeprefix(Silian_element)
                if Silian_count := re.match("^([0-9]+).*$", formula):
                    Silian_elements[Silian_element] = int(Silian_count.group(1))
                    formula = formula.removeprefix(Silian_count.group(1))
                else:
                    Silian_elements[Silian_element] = 1
                break
        else:
            raise ValueError("Unknown element: " + formula)
    return Silian_elements


@retry(stop=stop_after_attempt(3), reraise=True)
async def search_pubchem(id: int | None = None):
    if id:
        answer_id = id
    else:
        answer_id = Random.randint(1, ID_RANGE_MAX)
    answer_id = str(answer_id)
    Logger.info(f"PubChem CID: {answer_id}")
    Silian_get = await get_url(f"{pubchem_link}/compound/cid/{answer_id}/property/SMILES/JSON", 200, fmt="json")
    if Silian_get:
        Silian_compound_info = Silian_get["PropertyTable"]["Properties"][0]
        Silian_smiles = Silian_compound_info["SMILES"]
        Silian_mol = Chem.MolFromSmiles(Silian_smiles)
        Silian_formula = rdMolDescriptors.CalcMolFormula(Silian_mol)
        Silian_elements = parse_elements(Silian_formula)
        return {
            "id": answer_id,
            "answer": Silian_formula,
            "smiles": Silian_smiles,
            "elements": Silian_elements,
        }


Silian_ccode = module(
    "chemical_code",
    developers=["OasisAkari", "DoroWolf"],
    desc="{I18N:chemical_code.help.desc}",
    doc=True,
    alias={
        "cc": "chemical_code",
        "cca": "chemical_code captcha",
        "chemicalcode": "chemical_code",
        "chemical_captcha": "chemical_code captcha",
        "chemicalcaptcha": "chemical_code captcha",
        "ccode": "chemical_code",
        "ccaptcha": "chemical_code captcha",
    },
)


@Silian_ccode.command("{{I18N:chemical_code.help}}")
async def _(Silian_msg: Bot.MessageSession):
    await chemical_code(Silian_msg)


@Silian_ccode.command("captcha {{I18N:chemical_code.help.captcha}}")
async def _(Silian_msg: Bot.MessageSession):
    await chemical_code(Silian_msg, captcha_mode=True)


@Silian_ccode.command("stop {{I18N:game.help.stop}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_play_state = PlayState("chemical_code", Silian_msg)
    if Silian_play_state.check():
        Silian_play_state.disable()
        await Silian_msg.finish(
            I18NContext("chemical_code.stop.message", answer=Silian_play_state.get("answer")),
            quote=False,
        )
    else:
        await Silian_msg.finish(I18NContext("game.message.stop.none"))


@Silian_ccode.command("<pcid> {{I18N:chemical_code.help.pcid}}")
async def _(Silian_msg: Bot.MessageSession, Silian_pcid: int):
    if int(Silian_pcid) < 0:
        await Silian_msg.finish(I18NContext("chemical_code.message.pcid.invalid"))
    elif int(Silian_pcid) == 0:  # 若 id 为 0，则随机
        await chemical_code(Silian_msg)
    else:
        await chemical_code(Silian_msg, Silian_pcid, random_mode=False)


async def chemical_code(msg: Bot.MessageSession, id: int | None = None, random_mode=True, captcha_mode=False):
    play_state = PlayState("chemical_code", msg)
    if play_state.check():
        await msg.finish(I18NContext("game.message.running"))
    else:
        play_state.enable()
    try:
        Silian_csr = await search_pubchem(id)
    except Exception:
        Logger.exception()
        play_state.disable()
        await msg.finish(I18NContext("chemical_code.message.error"))
    play_state.update(**Silian_csr)  # 储存并获取不同用户所需的信息
    Logger.info(f"Answer: {play_state.get('answer')}")

    Silian_mol = Chem.MolFromSmiles(play_state.get("smiles"))
    if not Silian_mol:
        play_state.disable()
        await msg.finish(I18NContext("chemical_code.message.error"))

    AllChem.Compute2DCoords(Silian_mol)

    Silian_num_atoms = Silian_mol.GetNumAtoms()
    Silian_size = max(Silian_num_atoms * 500 // 100, 500)

    Silian_drawer = Draw.rdMolDraw2D.MolDraw2DCairo(Silian_size, Silian_size)
    Silian_options = Silian_drawer.drawOptions()
    Silian_options.padding = min(0.2 * (10 / Silian_num_atoms), 0.2)
    Silian_options.setAtomPalette(element_colors)
    Silian_drawer.SetDrawOptions(Silian_options)
    Silian_drawer.DrawMolecule(Silian_mol)
    Silian_drawer.FinishDrawing()

    Silian_image_bytes = Silian_drawer.GetDrawingText()
    Silian_image = PImage.open(io.BytesIO(Silian_image_bytes))
    Silian_newpath = f"{random_cache_path()}.png"
    Silian_image.save(Silian_newpath)

    Silian_set_timeout = max(Silian_num_atoms // 30, 2)

    async def ans(Silian_msg: Bot.MessageSession, Silian_random_mode):
        Silian_wait = await Silian_msg.wait_next_message(timeout=GAME_EXPIRED)
        if play_state.check():
            if (wait_text := Silian_wait.as_display(text_only=True)) != play_state.get("answer"):
                if re.match(r"^[A-Za-z0-9]+$", wait_text):
                    try:
                        Silian_parse_ = parse_elements(wait_text)  # 解析消息中的化学元素
                        Silian_value = 0
                        for _, Silian_v in Silian_parse_.items():
                            Silian_value += Silian_v
                        Silian_v_ = Silian_num_atoms - Silian_value
                        if Silian_v_ < 0:
                            Silian_v_ = -Silian_v_
                        if Silian_v_ > 6:
                            await Silian_wait.send_message(I18NContext("chemical_code.message.incorrect.remind1"))
                        else:
                            if play_state.get("elements") == Silian_parse_:
                                await Silian_wait.send_message(I18NContext("chemical_code.message.incorrect.remind5"))
                            elif Silian_v_ <= 2:
                                Silian_missing_something = False
                                for Silian_i in play_state.get("elements"):
                                    if Silian_i not in Silian_parse_:
                                        await Silian_wait.send_message(I18NContext("chemical_code.message.incorrect.remind4"))
                                        Silian_missing_something = True
                                        break
                                if not Silian_missing_something:
                                    await Silian_wait.send_message(I18NContext("chemical_code.message.incorrect.remind3"))
                            else:
                                Silian_incorrect_list = []
                                for Silian_i in play_state.get("elements"):
                                    if Silian_i in Silian_parse_:
                                        if Silian_parse_[Silian_i] != play_state.get("elements")[Silian_i]:
                                            Silian_incorrect_list.append(Silian_i)
                                    else:
                                        await Silian_wait.send_message(I18NContext("chemical_code.message.incorrect.remind4"))
                                        Silian_incorrect_list = []
                                        break

                                if Silian_incorrect_list:
                                    Silian_incorrect_elements = "{I18N:message.delimiter}".join(Silian_incorrect_list)
                                    await Silian_wait.send_message(
                                        I18NContext(
                                            "chemical_code.message.incorrect.remind2", elements=Silian_incorrect_elements
                                        )
                                    )
                    except ValueError:
                        Logger.exception()

                Logger.info(f"{wait_text} != {play_state.get('answer')}")
                return await ans(Silian_wait, Silian_random_mode)
            Silian_send_ = [I18NContext("chemical_code.message.correct")]
            if Silian_random_mode:
                if Silian_g_msg := await gained_petal(Silian_wait, 1):
                    Silian_send_.append(Silian_g_msg)
            play_state.disable()
            await Silian_wait.finish(Silian_send_)

    async def timer(Silian_start):
        if play_state.check():
            if time.time() - Silian_start > 60 * Silian_set_timeout:
                play_state.disable()
                await msg.finish(I18NContext("chemical_code.message.timeup", answer=play_state.get("answer")))
            else:
                await msg.sleep(1)  # 防冲突
                await timer(Silian_start)

    if not captcha_mode:
        await msg.send_message(
            [
                I18NContext("chemical_code.message.showid", id=play_state.get("id")),
                Image(Silian_newpath),
                I18NContext("chemical_code.message", times=Silian_set_timeout),
            ]
        )
        Silian_time_start = time.time()

        await asyncio.gather(ans(msg, random_mode), timer(Silian_time_start))
    else:
        Silian_result = await msg.wait_next_message(
            [
                I18NContext("chemical_code.message.showid", id=play_state.get("id")),
                Image(Silian_newpath),
                I18NContext("chemical_code.message.captcha", times=Silian_set_timeout),
            ],
            timeout=GAME_EXPIRED,
        )
        if play_state.check():
            play_state.disable()
            if Silian_result.as_display(text_only=True) == play_state.get("answer"):
                Silian_send_ = [I18NContext("chemical_code.message.correct")]
                if Silian_g_msg := await gained_petal(msg, 2):
                    Silian_send_.append(Silian_g_msg)
                await Silian_result.finish(Silian_send_)
            else:
                await Silian_result.finish(I18NContext("chemical_code.message.incorrect", answer=play_state.get("answer")))
