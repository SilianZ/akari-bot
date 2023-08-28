import asyncio
import datetime
import html
import random
import re
import traceback
from pathlib import Path
from typing import List, Union

import aiocqhttp.exceptions
import ujson as json
from aiocqhttp import MessageSegment

from bots.aiocqhttp.client import bot, client_name
from config import Config
from core.builtins import Bot, ErrorMessage, base_superuser_list
from core.builtins import Plain, Image, Voice, Temp, command_prefix
from core.builtins.message import MessageSession as MS
from core.builtins.message.chain import MessageChain
from core.logger import Logger
from core.types import MsgInfo, Session, FetchTarget as FT, FinishedSession as FinS
from core.utils.image import msgchain2image
from database import BotDBUtil
from core.utils.storedata import get_stored_list
from core.exceptions import SendMessageFailed

enable_analytics = Config('enable_analytics')


class FinishedSession(FinS):
    async def delete(self):
        """
        用于删除这条消息。
        """
        if self.session.target.targetFrom in ['QQ|Group', 'QQ']:
            try:
                for x in self.messageId:
                    if x != 0:
                        await bot.call_action('delete_msg', message_id=x)
            except Exception:
                Logger.error(traceback.format_exc())


last_send_typing_time = {}
Temp.data['is_group_message_blocked'] = False
Temp.data['waiting_for_send_group_message'] = []


async def resending_group_message():
    falied_list = []
    try:
        if targets := Temp.data['waiting_for_send_group_message']:
            for x in targets:
                try:
                    if x['i18n']:
                        await x['fetch'].sendDirectMessage(x['fetch'].parent.locale.t(x['message'], **x['kwargs']))
                    else:
                        await x['fetch'].sendDirectMessage(x['message'])
                    Temp.data['waiting_for_send_group_message'].remove(x)
                    await asyncio.sleep(30)
                except SendMessageFailed:
                    Logger.error(traceback.format_exc())
                    falied_list.append(x)
                    if len(falied_list) > 3:
                        raise SendMessageFailed
        Temp.data['is_group_message_blocked'] = False
    except SendMessageFailed:
        Logger.error(traceback.format_exc())
        Temp.data['is_group_message_blocked'] = True
        for bu in base_superuser_list:
            fetch_base_superuser = await FetchTarget.fetch_target(bu)
            if fetch_base_superuser:
                await fetch_base_superuser. \
                    sendDirectMessage(fetch_base_superuser.parent.locale.t("error.message.paused",
                                                                           prefix=command_prefix[0]))


class MessageSession(MS):
    class Feature:
        image = True
        voice = True
        embed = False
        forward = True
        delete = True
        wait = True
        quote = True

    async def sendMessage(self, msgchain, quote=True, disable_secret_check=False,
                          allow_split_image=True) -> FinishedSession:
        msg = MessageSegment.text('')
        if quote and self.target.targetFrom == 'QQ|Group' and self.session.message:
            msg = MessageSegment.reply(self.session.message.message_id)
        msgchain = MessageChain(msgchain)
        if not msgchain.is_safe and not disable_secret_check:
            return await self.sendMessage(Plain(ErrorMessage(self.locale.t("error.message.chain.unsafe"))))
        self.sent.append(msgchain)
        count = 0
        for x in msgchain.asSendable(locale=self.locale.locale, embed=False):
            if isinstance(x, Plain):
                msg = msg + MessageSegment.text(('\n' if count != 0 else '') + x.text)
            elif isinstance(x, Image):
                msg = msg + MessageSegment.image(Path(await x.get()).as_uri())
            elif isinstance(x, Voice):
                if self.target.targetFrom != 'QQ|Guild':
                    msg = msg + MessageSegment.record(file=Path(x.path).as_uri())
            count += 1
        Logger.info(f'[Bot] -> [{self.target.targetId}]: {msg}')
        if self.target.targetFrom == 'QQ|Group':
            try:
                send = await bot.send_group_msg(group_id=self.session.target, message=msg)
            except aiocqhttp.exceptions.ActionFailed:
                msgchain.insert(0, Plain('消息被风控，尝试使用图片发送。'))
                msg2img = MessageSegment.image(Path(await msgchain2image(msgchain)).as_uri())
                try:
                    send = await bot.send_group_msg(group_id=self.session.target, message=msg2img)
                except aiocqhttp.exceptions.ActionFailed as e:
                    raise SendMessageFailed(e.result['wording'])

            if Temp.data['is_group_message_blocked']:
                asyncio.create_task(resending_group_message())

        elif self.target.targetFrom == 'QQ|Guild':
            match_guild = re.match(r'(.*)\|(.*)', self.session.target)
            send = await bot.call_action('send_guild_channel_msg', guild_id=int(match_guild.group(1)),
                                         channel_id=int(match_guild.group(2)), message=msg)
        else:
            try:
                send = await bot.send_private_msg(user_id=self.session.target, message=msg)
            except aiocqhttp.exceptions.ActionFailed as e:
                if self.session.message.detail_type == 'private' and self.session.message.sub_type == 'group':
                    return FinishedSession(self, 0, [{}])
                else:
                    raise e
        return FinishedSession(self, send['message_id'], [send])

    async def checkNativePermission(self):
        if self.target.targetFrom == 'QQ':
            return True
        elif self.target.targetFrom == 'QQ|Group':
            get_member_info = await bot.call_action('get_group_member_info', group_id=self.session.target,
                                                    user_id=self.session.sender)
            if get_member_info['role'] in ['owner', 'admin']:
                return True
        elif self.target.targetFrom == 'QQ|Guild':
            match_guild = re.match(r'(.*)\|(.*)', self.session.target)
            get_member_info = await bot.call_action('get_guild_member_profile', guild_id=match_guild.group(1),
                                                    user_id=self.session.sender)
            for m in get_member_info['roles']:
                if m['role_id'] == "2":
                    return True
            get_guild_info = await bot.call_action('get_guild_meta_by_guest', guild_id=match_guild.group(1))
            if get_guild_info['owner_id'] == self.session.sender:
                return True
            return False
        return False

    def asDisplay(self, text_only=False):
        m = html.unescape(self.session.message.message)
        if text_only:
            return ''.join(
                re.split(r'\[CQ:.*?]', m)).strip()
        m = re.sub(r'\[CQ:at,qq=(.*?)]', r'QQ|\1', m)
        m = re.sub(r'\[CQ:forward,id=(.*?)]', r'\[Ke:forward,id=\1]', m)

        return ''.join(
            re.split(r'\[CQ:.*?]', m)).strip()

    async def fake_forward_msg(self, nodelist):
        if self.target.targetFrom == 'QQ|Group':
            get_ = get_stored_list(Bot.FetchTarget, 'forward_msg')
            if not get_['status']:
                await self.sendMessage('转发消息已禁用。')
                raise
            await bot.call_action('send_group_forward_msg', group_id=int(self.session.target), messages=nodelist)

    async def delete(self):
        if self.target.targetFrom in ['QQ', 'QQ|Group']:
            try:
                if isinstance(self.session.message, list):
                    for x in self.session.message:
                        await bot.call_action('delete_msg', message_id=x['message_id'])
                else:
                    await bot.call_action('delete_msg', message_id=self.session.message['message_id'])
            except Exception:
                Logger.error(traceback.format_exc())

    async def get_text_channel_list(self):
        match_guild = re.match(r'(.*)\|(.*)', self.session.target)
        get_channels_info = await bot.call_action('get_guild_channel_list', guild_id=match_guild.group(1),
                                                  no_cache=True)
        lst = []
        for m in get_channels_info:
            if m['channel_type'] == 1:
                lst.append(f'{m["owner_guild_id"]}|{m["channel_id"]}')
        return lst

    async def toMessageChain(self):
        m = html.unescape(self.session.message.message)
        m = re.sub(r'\[CQ:at,qq=(.*?)]', r'QQ|\1', m)
        m = re.sub(r'\[CQ:forward,id=(.*?)]', r'\[Ke:forward,id=\1]', m)
        spl = re.split(r'(\[CQ:.*?])', m)
        lst = []
        for s in spl:
            if s == '':
                continue
            if s.startswith('[CQ:'):
                if s.startswith('[CQ:image'):
                    sspl = s.split(',')
                    for ss in sspl:
                        if ss.startswith('url='):
                            lst.append(Image(ss[4:-1]))
            else:
                lst.append(Plain(s))

        return MessageChain(lst)

    async def call_api(self, action, **params):
        return await bot.call_action(action, **params)

    class Typing:
        def __init__(self, msg: MS):
            self.msg = msg

        async def __aenter__(self):
            if self.msg.target.targetFrom == 'QQ|Group':
                if self.msg.session.sender in last_send_typing_time:
                    if datetime.datetime.now().timestamp() - last_send_typing_time[self.msg.session.sender] <= 3600:
                        return
                last_send_typing_time[self.msg.session.sender] = datetime.datetime.now().timestamp()
                await bot.send_group_msg(group_id=self.msg.session.target,
                                         message=f'[CQ:poke,qq={self.msg.session.sender}]')

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass


class FetchTarget(FT):
    name = client_name

    @staticmethod
    async def fetch_target(targetId, senderId=None) -> Union[Bot.FetchedSession]:
        matchTarget = re.match(r'^(QQ\|Group|QQ\|Guild|QQ)\|(.*)', targetId)
        if matchTarget:
            targetFrom = senderFrom = matchTarget.group(1)
            targetId = matchTarget.group(2)
            if senderId:
                matchSender = re.match(r'^(QQ\|Tiny|QQ)\|(.*)', senderId)
                if matchSender:
                    senderFrom = matchSender.group(1)
                    senderId = matchSender.group(2)
            else:
                senderId = targetId

            return Bot.FetchedSession(targetFrom, targetId, senderFrom, senderId)

    @staticmethod
    async def fetch_target_list(targetList: list) -> List[Bot.FetchedSession]:
        lst = []
        group_list_raw = await bot.call_action('get_group_list')
        group_list = []
        for g in group_list_raw:
            group_list.append(g['group_id'])
        friend_list_raw = await bot.call_action('get_friend_list')
        friend_list = []
        guild_list_raw = await bot.call_action('get_guild_list')
        guild_list = []
        for g in guild_list_raw:
            get_channel_list = await bot.call_action('get_guild_channel_list', guild_id=g['guild_id'])
            for channel in get_channel_list:
                if channel['channel_type'] == 1:
                    guild_list.append(f"{str(g['guild_id'])}|{str(channel['channel_id'])}")
        for f in friend_list_raw:
            friend_list.append(f)
        for x in targetList:
            fet = await FetchTarget.fetch_target(x)
            if fet:
                if fet.target.targetFrom == 'QQ|Group':
                    if fet.session.target not in group_list:
                        continue
                if fet.target.targetFrom == 'QQ':
                    if fet.session.target not in friend_list:
                        continue
                if fet.target.targetFrom == 'QQ|Guild':
                    if fet.session.target not in guild_list:
                        continue
                lst.append(fet)
        return lst

    @staticmethod
    async def post_message(module_name, message, user_list: List[Bot.FetchedSession] = None, i18n=False, **kwargs):
        _tsk = []
        blocked = False

        async def post_(fetch_: Bot.FetchedSession):
            nonlocal _tsk
            nonlocal blocked
            try:
                if Temp.data['is_group_message_blocked'] and fetch_.target.targetFrom == 'QQ|Group':
                    Temp.data['waiting_for_send_group_message'].append({'fetch': fetch_, 'message': message,
                                                                        'i18n': i18n, 'kwargs': kwargs})
                else:
                    if i18n:
                        await fetch_.sendDirectMessage(fetch_.parent.locale.t(message, **kwargs))

                    else:
                        await fetch_.sendDirectMessage(message)
                    if _tsk:
                        _tsk = []
                if enable_analytics:
                    BotDBUtil.Analytics(fetch_).add('', module_name, 'schedule')
                await asyncio.sleep(0.5)
            except SendMessageFailed as e:
                if e.args[0] == 'send group message failed: blocked by server':
                    if len(_tsk) >= 3:
                        blocked = True
                    if not blocked:
                        _tsk.append({'fetch': fetch_, 'message': message, 'i18n': i18n, 'kwargs': kwargs})
                    else:
                        Temp.data['is_group_message_blocked'] = True
                        Temp.data['waiting_for_send_group_message'].append({'fetch': fetch_, 'message': message,
                                                                            'i18n': i18n, 'kwargs': kwargs})
                        if _tsk:
                            for t in _tsk:
                                Temp.data['waiting_for_send_group_message'].append(t)
                            _tsk = []
                        for bu in base_superuser_list:
                            fetch_base_superuser = await FetchTarget.fetch_target(bu)
                            if fetch_base_superuser:
                                await fetch_base_superuser. \
                                    sendDirectMessage(fetch_base_superuser.parent.locale.t("error.message.paused",
                                                                                           prefix=command_prefix[0]))
            except Exception:
                Logger.error(traceback.format_exc())

        if user_list is not None:
            for x in user_list:
                await post_(x)
        else:
            get_target_id = BotDBUtil.TargetInfo.get_enabled_this(module_name, "QQ")
            group_list_raw = await bot.call_action('get_group_list')
            group_list = [g['group_id'] for g in group_list_raw]
            friend_list_raw = await bot.call_action('get_friend_list')
            friend_list = [f['user_id'] for f in friend_list_raw]
            guild_list_raw = await bot.call_action('get_guild_list')
            guild_list = []
            for g in guild_list_raw:
                try:
                    get_channel_list = await bot.call_action('get_guild_channel_list', guild_id=g['guild_id'],
                                                             no_cache=True)
                    for channel in get_channel_list:
                        if channel['channel_type'] == 1:
                            guild_list.append(f"{str(g['guild_id'])}|{str(channel['channel_id'])}")
                except Exception:
                    traceback.print_exc()
                    continue

            in_whitelist = []
            else_ = []
            for x in get_target_id:
                fetch = await FetchTarget.fetch_target(x.targetId)
                Logger.debug(fetch)
                if fetch:
                    if fetch.target.targetFrom == 'QQ|Group':
                        if int(fetch.session.target) not in group_list:
                            continue
                    if fetch.target.targetFrom == 'QQ':
                        if int(fetch.session.target) not in friend_list:
                            continue
                    if fetch.target.targetFrom == 'QQ|Guild':
                        if fetch.session.target not in guild_list:
                            continue

                    if fetch.target.targetFrom in ['QQ', 'QQ|Guild']:
                        in_whitelist.append(post_(fetch))
                    else:
                        load_options: dict = json.loads(x.options)
                        if load_options.get('in_post_whitelist', False):
                            in_whitelist.append(post_(fetch))
                        else:
                            else_.append(post_(fetch))

            if in_whitelist:
                for x in in_whitelist:
                    await x
                    await asyncio.sleep(random.randint(1, 5))

            async def post_not_in_whitelist(lst):
                for f in lst:
                    await f
                    await asyncio.sleep(random.randint(15, 30))

            if else_:
                asyncio.create_task(post_not_in_whitelist(else_))
                Logger.info(f"The task of posting messages to whitelisted groups is complete. "
                            f"Posting message to {len(else_)} groups not in whitelist.")


Bot.MessageSession = MessageSession
Bot.FetchTarget = FetchTarget
Bot.client_name = client_name
