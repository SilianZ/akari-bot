import orjson

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain
from core.component import module
from core.constants.path import assets_path


Silian_data_path = assets_path / "modules" / "threedsdb"


Silian_threedsdb = module("3dsdb", desc="{I18N:threedsdb.help.desc}", developers=["OasisAkari"])


@Silian_threedsdb.command("<keywords> {{I18N:threedsdb.help.command}}")
async def _(Silian_msg: Bot.MessageSession, Silian_keywords: str):
    Silian_message_str = []
    Silian_i = 0
    if Silian_keywords.isdigit():
        for Silian_file in Silian_data_path.glob("*.json"):
            Silian_load_json = orjson.loads(Silian_file.read_text(encoding="utf-8"))
            for Silian_item in Silian_load_json:
                if Silian_keywords in Silian_item.get("TitleID", ""):
                    if Silian_i < 10:
                        Silian_message_str += [f"{k}: {v}" for k, v in Silian_item.items()]
                        Silian_message_str.append("\n")
                        Silian_i += 1

    else:
        for Silian_file in Silian_data_path.glob("*.json"):
            Silian_load_json = orjson.loads(Silian_file.read_text(encoding="utf-8"))
            for Silian_item in Silian_load_json:
                if Silian_keywords.lower() in Silian_item.get("Name", "").lower():
                    if Silian_i < 10:
                        Silian_message_str += [f"{k}: {v}" for k, v in Silian_item.items()]
                        Silian_message_str.append("\n")
                        Silian_i += 1
    if Silian_message_str:
        await Silian_msg.finish(
            [Plain("\n".join(Silian_message_str)), (I18NContext("threedsdb.message.limited_results") if Silian_i >= 10 else None)]
        )
    else:
        await Silian_msg.finish(I18NContext("threedsdb.message.no_results"))
