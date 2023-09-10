from core.logger import Logger
from core.builtins import Bot, Plain
from core.component import module
from core.utils.http import get_url
from config import Config
import hashlib
import random

trans = module(bind_prefix='translate', desc='{trans.desc}', alias=['trans'], developers=['bugungu'])
appid = Config('translate_appid')


@trans.handle('<from> <to> <query> {{trans.desc.trans}}')
async def send(msg: Bot.MessageSession):
    fm = msg.parsed_msg['<from>']
    to = msg.parsed_msg['<to>']
    q = msg.parsed_msg['<query>']

    salt = str(random.randint(32768, 65536))
    key = Config('translate_api_key')
    sign = hashlib.md5((appid + q + salt + key).encode('utf-8'))
    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate?q=' + q + '&from=' + fm + '&to=' + to + \
        '&appid=' + appid + '&salt=' + salt + '&sign=' + sign.hexdigest() + '&action=1'
    res = await get_url(url, fmt='json', timeout=200)

    if 'error_code' in res.keys():
        raise ValueError("{trans.err.prefix}{trans.err." + str(res['error_code']) + "}")
    send_msg = res['trans_result'][0]['dst']

    if res['trans_result'][0]['dst'] == '':
        send_msg += '\n' + '{trans.msg.none}'
    await msg.finish(send_msg)
