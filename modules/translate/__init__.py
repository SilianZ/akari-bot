from core.logger import Logger
from core.builtins import Bot, Plain
from core.component import module
from core.utils.http import get_url
from config import Config
import time
import hashlib, random

trans = module(bind_prefix='translate', desc='{trans.desc}', alias=['trans'], developers=['bugungu'])

@trans.handle('<from> <to> <query> {{trans.desc.trans}}')

async def send(msg: Bot.MessageSession):
    fm = msg.parsed_msg['<from>']
    to = msg.parsed_msg['<to>']
    q = msg.parsed_msg['<query>']
    appid = Config('translate_appid')
    salt = str(random.randint(32768, 65536))
    key = Config('translate_api_key')
    sign = hashlib.md5((appid + q + salt + key).encode('utf-8'))
    Logger.info(sign.hexdigest() + ' ' + appid + q + salt + key)
    start = time.perf_counter_ns()
    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate?q=' + q + '&from=' + fm + '&to=' + to + \
            '&appid=' + appid + '&salt=' + salt + '&sign=' + sign.hexdigest() + '&action=1'
    res = await get_url(url, fmt='json', timeout=200)
    Logger.info('Got result: ' + str(res))
    if 'error_code' in res.keys():
        await msg.finish(msg.locale.t('trans.err.prefix') + msg.locale.t('trans.err.'+str(res['error_code'])))
    send_msg = []
    send_msg.append(Plain(res['trans_result']['dst'][0]))
    if res['trans_result']['dst'][0] == '':
        send_msg.append(Plain(msg.locale.t('trans.msg.none')))
    stop = time.perf_counter_ns()
    delta = (stop - start) / 1000000
    if msg.checkSuperUser():
        send_msg.append(Plain(msg.locale.t('trans.msg.time', time=delta)))
    await msg.finish(send_msg)