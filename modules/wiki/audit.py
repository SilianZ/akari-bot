from datetime import datetime

from config import Config
from core.builtins import Bot, Plain, Image
from core.component import module
from core.utils.image_table import image_table_render, ImageTable
from modules.wiki.utils.dbutils import Audit
from modules.wiki.utils.wikilib import WikiLib


if Config('enable_urlmanager'):
    aud = module('wiki_audit', developers=['Dianliang233', 'OasisAkari'], required_superuser=True,
                 alias='wau')

    @aud.command(['trust <apiLink>', 'block <apiLink>'])
    async def _(msg: Bot.MessageSession):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        api = msg.parsed_msg['<apiLink>']
        check = await WikiLib(api).check_wiki_available()
        if check.available:
            api = check.value.api
            if msg.parsed_msg.get('trust', False):
                res = Audit(api).add_to_AllowList(date)
                list_name = msg.locale.t('wiki.message.wiki_audit.list_name.allowlist')
            else:
                res = Audit(api).add_to_BlockList(date)
                list_name = msg.locale.t('wiki.message.wiki_audit.list_name.blocklist')
            if not res:
                await msg.finish(msg.locale.t('wiki.message.wiki_audit.add.failed', list_name=list_name) + api)
            else:
                await msg.finish(msg.locale.t('wiki.message.wiki_audit.add.success', list_name=list_name) + api)
        else:
            result = msg.locale.t('wiki.message.error.add') + \
                ('\n' + msg.locale.t('wiki.message.error.info') + check.message if check.message != '' else '')
            await msg.finish(result)

    @aud.command(['distrust <apiLink>', 'unblock <apiLink>'])
    async def _(msg: Bot.MessageSession):
        api = msg.parsed_msg['<apiLink>']  # 已关闭的站点无法验证有效性
        if msg.parsed_msg.get('distrust', False):
            res = Audit(api).remove_from_AllowList()
            if res is None:
                await msg.finish(msg.locale.t('wiki.message.wiki_audit.remove.failed.other') + api)
            list_name = msg.locale.t('wiki.message.wiki_audit.list_name.allowlist')
        else:
            res = Audit(api).remove_from_BlockList()
            list_name = msg.locale.t('wiki.message.wiki_audit.list_name.blocklist')
        if not res:
            await msg.finish(msg.locale.t('wiki.message.wiki_audit.remove.failed', list_name=list_name) + api)
        else:
            await msg.finish(msg.locale.t('wiki.message.wiki_audit.remove.success', list_name=list_name) + api)

    @aud.command('query <apiLink>')
    async def _(msg: Bot.MessageSession):
        api = msg.parsed_msg['<apiLink>']
        check = await WikiLib(api).check_wiki_available()
        if check.available:
            api = check.value.api
            audit = Audit(api)
            allow = audit.inAllowList
            block = audit.inBlockList
            msg_list = []
            if allow:
                msg_list.append(api + msg.locale.t('wiki.message.wiki_audit.query.allowlist'))
            if block:
                msg_list.append(api + msg.locale.t('wiki.message.wiki_audit.query.blocklist'))
            if msg_list:
                msg_list.append(msg.locale.t('wiki.message.wiki_audit.query.conflict'))
                await msg.finish('\n'.join(msg_list))
            else:
                await msg.finish(api + msg.locale.t('wiki.message.wiki_audit.query.none'))
        else:
            result = msg.locale.t('wiki.message.error.query') + \
                ('\n' + msg.locale.t('wiki.message.error.info') + check.message if check.message != '' else '')
            await msg.finish(result)

    @aud.command(['list', 'list legacy'])
    async def _(msg: Bot.MessageSession):
        allow_list = Audit.get_allow_list()
        block_list = Audit.get_block_list()
        legacy = True
        if not msg.parsed_msg.get('legacy', False) and msg.Feature.image:
            send_msgs = []
            allow_columns = [[x[0], x[1]] for x in allow_list]
            if allow_columns:
                allow_table = ImageTable(data=allow_columns, headers=[
                    msg.locale.t('wiki.message.wiki_audit.list.table.header.apilink'),
                    msg.locale.t('wiki.message.wiki_audit.list.table.header.date')
                ])
                if allow_table:
                    allow_image = await image_table_render(allow_table)
                    if allow_image:
                        send_msgs.append(Plain(msg.locale.t('wiki.message.wiki_audit.list.allowlist')))
                        send_msgs.append(Image(allow_image))
            block_columns = [[x[0], x[1]] for x in block_list]
            if block_columns:
                block_table = ImageTable(data=block_columns, headers=[
                    msg.locale.t('wiki.message.wiki_audit.list.table.header.apilink'),
                    msg.locale.t('wiki.message.wiki_audit.list.table.header.date')
                ])
                if block_table:
                    block_image = await image_table_render(block_table)
                    if block_image:
                        send_msgs.append(Plain(msg.locale.t('wiki.message.wiki_audit.list.blocklist')))
                        send_msgs.append(Image(block_image))
            if send_msgs:
                await msg.finish(send_msgs)
                legacy = False
        if legacy:
            wikis = [msg.locale.t('wiki.message.wiki_audit.list.allowlist')]
            for al in allow_list:
                wikis.append(f'{al[0]} ({al[1]})')
            wikis.append(msg.locale.t('wiki.message.wiki_audit.list.blocklist'))
            for bl in block_list:
                wikis.append(f'{bl[0]} ({bl[1]})')
            await msg.finish('\n'.join(wikis))
