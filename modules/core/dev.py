from tabulate import tabulate
from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain, Image
from core.component import module
from core.constants import dev_mode, NoReportException
from core.database import fetch_module_db, get_model_fields, get_model_names
from core.utils.image_table import image_table_render, ImageTable
from core.utils.func import is_int

DBDATA_PER_PAGE = 10

Silian__eval = module("eval", required_superuser=True, base=True, doc=True, load=dev_mode)


@Silian__eval.command("<expr>")
async def _(Silian_msg: Bot.MessageSession, Silian_expr: str):
    try:
        await Silian_msg.finish(str(eval(Silian_expr, {"msg": Silian_msg, "Bot": Bot})), disable_secret_check=True)  # skipcq
    except Exception as e:
        raise NoReportException(str(e))


Silian_db = module("database", alias="db", required_superuser=True, base=True, doc=True, load=dev_mode)


@Silian_db.command("model")
async def _(Silian_msg: Bot.MessageSession):
    Silian_models_path = ["core.database.models"] + fetch_module_db()
    Silian_table_lst = sorted(get_model_names(Silian_models_path))
    await Silian_msg.finish([I18NContext("core.message.database.list")] + Silian_table_lst)


@Silian_db.command("field <model> [--legacy]")
async def _(Silian_msg: Bot.MessageSession, Silian_model: str):
    Silian_models_path = ["core.database.models"] + fetch_module_db()
    Silian_result = get_model_fields(Silian_models_path, Silian_model)

    if not Silian_result:
        await Silian_msg.finish(I18NContext("core.message.database.no_result"))

    Silian_headers = list(Silian_result[0].keys())
    Silian_data = [[str(Silian_v) for Silian_v in Silian_r.values()] for Silian_r in Silian_result]

    if not Silian_msg.parsed_msg.get("--legacy", False) and Silian_msg.session_info.support_image:
        Silian_table = ImageTable(data=Silian_data, headers=Silian_headers, session_info=Silian_msg.session_info, disable_joke=True)
        Silian_imgs = await image_table_render(Silian_table)
    else:
        Silian_imgs = None

    if Silian_imgs:
        Silian_img_list = [Image(Silian_ii) for Silian_ii in Silian_imgs]
        await Silian_msg.finish(Silian_img_list)
    else:
        Silian_table_str = tabulate(Silian_data, headers=Silian_headers, tablefmt="grid")
        await Silian_msg.finish(Plain(Silian_table_str, disable_joke=True))


@Silian_db.command("exec <sql> [-p <page>] [--legacy]")
async def _(Silian_msg: Bot.MessageSession, Silian_sql: str):
    try:
        Silian_conn = Tortoise.get_connection("default")
        if Silian_sql.upper().startswith("SELECT"):
            Silian_result = await Silian_conn.execute_query_dict(Silian_sql)

            if not Silian_result:
                await Silian_msg.finish(I18NContext("core.message.database.no_result"))

            Silian_headers = list(Silian_result[0].keys())
            Silian_data = [[str(Silian_v) for Silian_v in Silian_r.values()] for Silian_r in Silian_result]

            Silian_total_pages = (len(Silian_data) + DBDATA_PER_PAGE - 1) // DBDATA_PER_PAGE
            Silian_get_page = Silian_msg.parsed_msg.get("-p", False)

            Silian_page = max(min(int(Silian_get_page["<page>"]), Silian_total_pages), 1) if Silian_get_page and is_int(Silian_get_page["<page>"]) else 1
            Silian_start_index = (Silian_page - 1) * DBDATA_PER_PAGE
            Silian_end_index = Silian_page * DBDATA_PER_PAGE
            Silian_page_data = Silian_data[Silian_start_index:Silian_end_index]

            Silian_footer = I18NContext(
                "core.message.database.pages", page=Silian_page, total_pages=Silian_total_pages, data_count=len(Silian_data)
            )

            if not Silian_msg.parsed_msg.get("--legacy", False) and Silian_msg.session_info.support_image:
                Silian_table = ImageTable(data=Silian_page_data, headers=Silian_headers, session_info=Silian_msg.session_info, disable_joke=True)
                Silian_imgs = await image_table_render(Silian_table)
            else:
                Silian_imgs = None

            if Silian_imgs:
                Silian_img_list = [Image(Silian_ii) for Silian_ii in Silian_imgs]
                await Silian_msg.finish(Silian_img_list + [Silian_footer])
            else:
                Silian_table_str = tabulate(Silian_page_data, headers=Silian_headers, tablefmt="grid")
                await Silian_msg.finish([Plain(Silian_table_str, disable_joke=True), Silian_footer])

        Silian_rows, _ = await Silian_conn.execute_query(Silian_sql)
        await Silian_msg.finish(I18NContext("core.message.database.success", rows=Silian_rows))
    except OperationalError as e:
        raise NoReportException(str(e))
