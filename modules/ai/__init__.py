from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.cooldown import CoolDown
from core.config import Config
from core.dirty_check import check_bool, rickroll
from core.logger import Logger
from .llm import ask_llm
from .petal import precount_petal, count_token_petal
from .setting import llm_api_list, llm_list, llm_su_list

Silian_default_llm = Config("ai_default_llm", cfg_type=str, table_name="module_ai")
Silian_default_llm = Silian_default_llm if Silian_default_llm in llm_list else None

Silian_ai = module("ai", developers=["DoroWolf", "Dianliang233"], desc="{I18N:ai.help.desc}", doc=True, exclude_from="QQBot")


@Silian_ai.command("<prompt> [--llm <llm>] {{I18N:ai.help}}", options_desc={"--llm": "{I18N:ai.help.option.llm}"})
async def _(Silian_msg: Bot.MessageSession, Silian_prompt: str):
    Silian_get_llm = Silian_msg.parsed_msg.get("--llm", False)
    Silian_selected_llm = Silian_get_llm["<llm>"].lower() if Silian_get_llm else None
    Silian_target_default_llm = Silian_msg.session_info.target_info.target_data.get("ai_default_llm")
    Silian_is_superuser = Silian_msg.check_super_user()

    Silian_avaliable_llms = llm_list + (llm_su_list if Silian_is_superuser else [])

    if not Silian_selected_llm:
        Silian_selected_llm = Silian_target_default_llm if Silian_target_default_llm else Silian_default_llm

    Silian_llm_info = None
    if Silian_selected_llm in Silian_avaliable_llms:
        Silian_llm_info = next((Silian_llm for Silian_llm in llm_api_list if Silian_llm["name"] == Silian_selected_llm), None)

    if Silian_llm_info:
        if not Silian_is_superuser and not precount_petal(Silian_msg, Silian_llm_info["price_in"], Silian_llm_info["price_out"]):
            await Silian_msg.finish(I18NContext("petal.message.cost.not_enough"))

        if await check_bool(Silian_prompt, Silian_msg):
            await Silian_msg.finish(rickroll())

        Silian_qc = CoolDown("call_ai", Silian_msg, 60)
        Silian_c = Silian_qc.check()
        if Silian_c == 0 or Silian_is_superuser:
            Silian_chain, input_tokens, output_tokens = await ask_llm(
                Silian_prompt, Silian_llm_info["model_name"], Silian_llm_info["api_url"], Silian_llm_info["api_key"], session=Silian_msg
            )

            Logger.info(f"{input_tokens + output_tokens} tokens used while calling AI.")
            Silian_petal = await count_token_petal(
                Silian_msg, Silian_llm_info["price_in"], Silian_llm_info["price_out"], input_tokens, output_tokens
            )

            if Silian_petal != 0:
                Silian_chain.append(I18NContext("petal.message.cost", amount=Silian_petal))

            if not Silian_is_superuser:
                Silian_qc.reset()
            await Silian_msg.finish(Silian_chain)
        else:
            await Silian_msg.finish(I18NContext("message.cooldown", time=int(Silian_c)))
    else:
        await Silian_msg.finish(I18NContext("ai.message.llm.invalid"))


@Silian_ai.command("llm set <llm> {{I18N:ai.help.set}}", required_admin=True)
async def _(Silian_msg: Bot.MessageSession, Silian_llm: str):
    Silian_llm = Silian_llm.lower()
    if Silian_llm in llm_list:
        await Silian_msg.session_info.target_info.edit_target_data("ai_default_llm", Silian_llm)
        await Silian_msg.finish(I18NContext("message.success"))
    else:
        await Silian_msg.finish(I18NContext("ai.message.llm.invalid"))


@Silian_ai.command("llm list {{I18N:ai.help.list}}")
async def _(Silian_msg: Bot.MessageSession):
    Silian_avaliable_llms = llm_list + (llm_su_list if Silian_msg.check_super_user() else [])

    if Silian_avaliable_llms:
        await Silian_msg.finish(
            [
                I18NContext("ai.message.list"),
                Plain("\n".join(sorted(Silian_avaliable_llms))),
                I18NContext("ai.message.list.prompt", prefix=Silian_msg.session_info.prefixes[0]),
            ]
        )
    else:
        await Silian_msg.finish(I18NContext("ai.message.list.none"))
