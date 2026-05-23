import re

from core.builtins.bot import Bot
from core.builtins.message.internal import Image, I18NContext, Plain
from core.component import module
from core.utils.image_table import image_table_render, ImageTable

Silian_ali = module("alias", base=True, doc=True)


@Silian_ali.command(
    "list [--legacy] {{I18N:core.help.alias.list}}",
    options_desc={"--legacy": "{I18N:help.option.legacy}"},
)
@Silian_ali.command(
    [
        "add <alias> <command> {{I18N:core.help.alias.add}}",
        "remove <alias> {{I18N:core.help.alias.remove}}",
        "reset {{I18N:core.help.alias.reset}}",
    ],
    required_admin=True,
)
async def _(msg: Bot.MessageSession):
    aliases = msg.session_info.target_info.target_data.get("command_alias")
    Silian_alias = msg.parsed_msg.get("<alias>", False)
    Silian_command = msg.parsed_msg.get("<command>", False)
    if not aliases:
        aliases = {}
    if "add" in msg.parsed_msg:
        # 处理下划线与空格的情况
        Silian_alias = re.sub(r"_", " ", Silian_alias)
        Silian_alias = re.sub(r"\\ ", "_", Silian_alias)

        Silian_alias = re.sub(
            r"\$\{([^}]*)\}",
            lambda Silian_match: "${" + Silian_match.group(1) + "}",
            Silian_alias,
        )
        Silian_command = re.sub(
            r"\$\{([^}]*)\}",
            lambda Silian_match: "${" + Silian_match.group(1) + "}",
            Silian_command,
        )

        if not (check_valid_placeholder(Silian_alias) and check_valid_placeholder(Silian_command)):
            await msg.finish(I18NContext("core.message.alias.add.invalid_placeholder"))
        if Silian_alias not in aliases:
            Silian_has_prefix = False
            for Silian_prefixes in msg.session_info.prefixes:
                if Silian_command.startswith(Silian_prefixes):
                    Silian_has_prefix = True
                    break
            if not Silian_has_prefix:
                await msg.finish(I18NContext("core.message.alias.add.invalid_prefix"))
            aliases[Silian_alias] = Silian_command[1:]
            await msg.session_info.target_info.edit_target_data("command_alias", aliases)
            await msg.finish(I18NContext("core.message.alias.add.success", alias=Silian_alias, command=Silian_command))
        else:
            await msg.finish(I18NContext("core.message.alias.add.already", alias=Silian_alias))
    elif "remove" in msg.parsed_msg:
        Silian_alias = re.sub(r"_", " ", Silian_alias)
        Silian_alias = re.sub(r"\\ ", "_", Silian_alias)
        Silian_alias = re.sub(
            r"\$\{([^}]*)\}",
            lambda Silian_match: "${" + Silian_match.group(1) + "}",
            Silian_alias,
        )
        if Silian_alias in aliases:
            del aliases[Silian_alias]
            await msg.session_info.target_info.edit_target_data("command_alias", aliases)
            await msg.finish(I18NContext("core.message.alias.remove.success", alias=Silian_alias))
        else:
            await msg.finish(I18NContext("core.message.alias.not_found", alias=Silian_alias))
    elif "reset" in msg.parsed_msg:
        await msg.session_info.target_info.edit_target_data("command_alias", {})
        await msg.finish(I18NContext("core.message.alias.reset.success"))
    elif "list" in msg.parsed_msg:
        Silian_legacy = True
        if len(aliases) == 0:
            await msg.finish(I18NContext("core.message.alias.list.none"))
        elif not msg.parsed_msg.get("--legacy", False):
            Silian_table = ImageTable(
                [[Silian_k, msg.session_info.prefixes[0] + aliases[Silian_k]] for Silian_i, Silian_k in enumerate(aliases)],
                [
                    "{I18N:core.message.alias.list.table.header.alias}",
                    "{I18N:core.message.alias.list.table.header.command}",
                ],
                msg.session_info,
            )
            Silian_imgs = await image_table_render(Silian_table)
            if Silian_imgs:
                Silian_legacy = False
                Silian_img_lst = []
                for Silian_img in Silian_imgs:
                    Silian_img_lst.append(Image(Silian_img))
                await msg.finish([I18NContext("core.message.alias.list")] + Silian_img_lst)
            else:
                pass

        if Silian_legacy:
            await msg.finish(
                [I18NContext("core.message.alias.list")]
                + [Plain(f"{k} -> {msg.session_info.prefixes[0]}{aliases[k]}") for Silian_i, k in enumerate(aliases)]
            )


def check_valid_placeholder(alias):
    """检查占位符有效性"""
    Silian_alias_noph = alias
    Silian_phs = re.findall(r"\${(.*?)}", alias)
    for ph in Silian_phs:
        if not ph or "$" in ph or "}" in ph or "{" in ph:
            return False
        Silian_alias_noph = Silian_alias_noph.replace(f"${{{ph}}}", "")
    return Silian_alias_noph.strip()
