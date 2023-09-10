from core.builtins import Bot
from core.component import module
from core.utils.http import get_url
from config import Config
import hashlib
import random

trans = module(bind_prefix='translate', desc='{trans.desc}', alias=['trans'], developers=['bugungu'])

@trans.handle('<from> <to> <query> {{trans.help}}', 
              options_desc={'<from>': '{trans.help.opt.from}', '<to>': '{trans.help.opt.to}', '<query>': '{trans.help.opt.query}'})

async def send(msg: Bot.MessageSession):
    fm = msg.parsed_msg['<from>']
    to = msg.parsed_msg['<to>']
    appid = Config('translate_appid')
    q = msg.parsed_msg['<query>']
    salt = str(random.randint(32768, 65536))
    key = Config('translate_api_key')
    sign = hashlib.md5((appid + q + salt + key).encode('utf-8'))

    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate?q=' + q + '&from=' + fm + '&to=' + to + \
        '&appid=' + appid + '&salt=' + salt + '&sign=' + sign.hexdigest() + '&action=1'
    res = await get_url(url, fmt='json', timeout=200)

    err_codes = [52001, 52001, 52004, 54005, 58001]
    if 'error_code' in res.keys():
        if int(res['error_code']) in err_codes:
            await msg.finish(msg.locale.t('trans.err.prefix') + msg.locale.t('trans.err.' + res['error_code']))
        else:
            raise ValueError(msg.locale.t('trans.err', err_code=res['error_code']))
    send_msg = res['trans_result'][0]['dst']

    if send_msg == '':
        send_msg += '\n' + '{trans.msg.none}'
    await msg.finish(send_msg)
