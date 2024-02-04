from core.builtins import Bot, Plain, Image
from core.component import module
from core.utils.image_table import ImageTable
from .image_render import image_table_render
from core.utils.http import get_url
from core.logger import logger
import ujson as json

bgm = module(
    'bgm',
    developers=['bugungu'],
    alias=['bangumi', 'anime'],
    desc='基于 Bangumi API 的查番器。',
    support_languages=['zh_cn'],
)

@bgm.handle(['search <keyword>', 'search legacy <keyword>'])
async def search(msg: Bot.MessageSession, keyword: str):
    logger.info(keyword)
    url = f"https://api.bgm.tv/search/subject/{keyword}?type=2&resourceGroup=medium"
    logger.info(url)
    result = await get_url(url)
    logger.info(result)
    result = json.loads(result)
    count = result['results']
    if count == 0:
        await msg.finish('找不到该番剧！')

    result = result['list'][:10]

    if not msg.parsed_msg.get('legacy', False) and msg.Feature.image:
        send_msg = [Plain('搜索结果' + '\n')]
        data = [[
            str(i),
            f'<img src="{anime["images"]["large"] if "large" in anime["images"] else anime["images"]["common"]}" width="500">' + f'<h4>{anime["name"]}' + (f' ({anime["name_cn"]})' if 'name_cn' in anime else '') + '</h4>',
            str(anime['id'])
        ] for i, anime in enumerate(result, start=1)]

        tables = ImageTable(data, 
                            ['序号',
                            '番剧',
                            'ID']
                            )
        img = await image_table_render(tables)
        if img:
            send_msg.append(Image(img))
    elif not img:
        for i, anime in enumerate(result, start=1):
            send_msg.append(f"{i}. {anime['name']}" + (f' ({anime["name_cn"]})' if 'name_cn' in anime else '') + '\n')
    if count > 10:
        count = 10
        send_msg.append(Plain(msg.locale.t('message.collapse', amount='10')))
    
    if count == 1:
        send_msg.append('是否查看番剧详情？')
        query = await msg.wait_confirm(send_msg, delete=False)
        if query:
            sid = result[0]['id']
        else:
            await msg.finish()
    
    else:
        send_msg.append('回复对应的序号以查看番剧详情。')
        query = await msg.wait_reply(send_msg)
        query = query.as_display(text_only=True)
        if query.isdigit():
            query = int(query)
            if query > count:
                await msg.finish('编号超出范围。')
            else:
                sid = result[query - 1]['id']
        else:
            await msg.finish(msg.locale.t('无效的编号，必须为数字。'))

    await msg.finish(f'测试已完成，搜索内容为 {sid}')

        

