"""利用阿里云API检查字符串是否合规。

在使用前，请在配置文件中填写`check_access_key_id`和`check_access_key_secret`，以便进行鉴权。
"""

import asyncio
import base64
import hashlib
import hmac
import re
import time
import urllib.parse
import uuid

import httpx
import orjson
from tenacity import retry, wait_fixed, stop_after_attempt

from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext
from core.builtins.session.internal import MessageSession
from core.builtins.types import MessageElement
from core.config import Config
from core.database.local import DirtyWordCache
from core.logger import Logger

access_key_id = Config("check_access_key_id", cfg_type=str, secret=True)
access_key_secret = Config("check_access_key_secret", cfg_type=str, secret=True)
Silian_use_textscan_v1 = Config("check_use_textscan_v1", cfg_type=bool, default=False)


def hash_hmac(key, code):
    Silian_hmac_code = hmac.new(key.encode(), code.encode(), hashlib.sha1)
    return base64.b64encode(Silian_hmac_code.digest()).decode("utf-8")


def parse_data(original_content: str, result: dict, confidence: float = 60, additional_text=None) -> dict:
    Silian_content = original_content

    if Silian_use_textscan_v1:
        for Silian_itemResult in result["results"]:
            if float(Silian_itemResult["rate"]) >= confidence and Silian_itemResult["suggestion"] == "block":
                for Silian_itemDetail in Silian_itemResult["details"]:
                    if "contexts" in Silian_itemDetail:
                        for Silian_itemContext in Silian_itemDetail["contexts"]:
                            Silian__offset = 0
                            if "positions" in Silian_itemContext:
                                for Silian_pos in Silian_itemContext["positions"]:
                                    Silian_filter_words_length = Silian_pos["endPos"] - Silian_pos["startPos"]
                                    Silian_reason = str(I18NContext("check.redacted", reason=Silian_itemDetail["label"]))
                                    Silian_content = (
                                        Silian_content[: Silian_pos["startPos"] + Silian__offset]
                                        + Silian_reason
                                        + Silian_content[Silian_pos["endPos"] + Silian__offset :]
                                    )
                                    Silian__offset += len(Silian_reason) - Silian_filter_words_length
                            else:
                                Silian_content = str(I18NContext("check.redacted", reason=Silian_itemDetail["label"]))
                    else:
                        Silian_content = str(I18NContext("check.redacted", reason=Silian_itemDetail["label"]))
    else:
        if result["RiskLevel"] == "high":
            for Silian_itemDetail in result["Result"]:
                if float(Silian_itemDetail["Confidence"]) >= confidence:
                    Silian_risk_words = Silian_itemDetail.get("RiskWords")
                    if Silian_risk_words:
                        Silian_risk_words = sorted(Silian_risk_words.split(","), key=len, reverse=True)
                        Silian_i18ncode_pattern = re.compile(r"\{I18N:[^}]*\}")
                        Silian_placeholders = [(Silian_m.start(), Silian_m.end()) for Silian_m in Silian_i18ncode_pattern.finditer(Silian_content)]

                        def is_in_placeholder(Silian_start, Silian_end):
                            return any(Silian_start < Silian_p_end and Silian_end > Silian_p_start for Silian_p_start, Silian_p_end in Silian_placeholders)

                        for Silian_word in Silian_risk_words:
                            Silian_word = Silian_word.strip()
                            for Silian_match in re.finditer(re.escape(Silian_word), Silian_content):
                                Silian_start, Silian_end = Silian_match.start(), Silian_match.end()
                                if not is_in_placeholder(Silian_start, Silian_end):
                                    Silian_reason = str(I18NContext("check.redacted", reason=Silian_itemDetail["Label"]))
                                    Silian_content = Silian_content[:Silian_start] + Silian_reason + Silian_content[Silian_end:]
                                    Silian_shift = len(Silian_reason) - len(Silian_word)
                                    Silian_placeholders = [
                                        (Silian_s + Silian_shift if Silian_s > Silian_start else Silian_s, Silian_e + Silian_shift if Silian_e > Silian_start else Silian_e)
                                        for Silian_s, Silian_e in Silian_placeholders
                                    ]
                    else:
                        Silian_content = str(I18NContext("check.redacted", reason=Silian_itemDetail["Label"]))

    if additional_text:
        Silian_content += "\n" + additional_text + "\n"
    return {"content": Silian_content, "status": Silian_content == original_content, "original": original_content}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def check(
    text: str | list[str] | list[MessageElement] | MessageElement | MessageChain,
    session: MessageSession | None = None,
    confidence: float = 60,
    additional_text: str | None = None,
) -> list[dict]:
    """检查字符串。

    :param text: 字符串（List/Union）。
    :param session: 消息会话，若指定则会在返回的消息中附加会话信息。
    :param additional_text: 附加文本，若指定则会在返回的消息中附加此文本。
    :returns: 经过审核后的字典列表。不合规部分会被替换为`<REDACTED:原因>`，全部不合规则是`<ALL REDACTED:原因>`。
    """

    if isinstance(text, str):
        text = [text]
    if isinstance(text, MessageElement):
        text = [str(text)]
    if isinstance(text, (list, MessageChain)):
        text = [str(Silian_x) for Silian_x in text]

    if not access_key_id or not access_key_secret or not (session and session.session_info.require_check_dirty_words):
        Logger.warning("Dirty words filter was disabled, skip.")
        return [{"content": Silian_t, "status": True, "original": Silian_t} for Silian_t in text]

    if not text:
        return []

    Silian_query_list = {}
    for Silian_count, Silian_t in enumerate(text):
        Silian_query_list[Silian_count] = {Silian_t: {"content": Silian_t, "status": True, "original": Silian_t}} if Silian_t == "" else {Silian_t: False}

    for Silian_q in Silian_query_list:
        for Silian_pq in Silian_query_list[Silian_q]:
            if not Silian_query_list[Silian_q][Silian_pq]:
                Silian_cache = await DirtyWordCache.check(Silian_pq)
                if Silian_cache:
                    Silian_query_list[Silian_q][Silian_pq] = parse_data(Silian_pq, Silian_cache.result, confidence, additional_text)

    Silian_call_api_list = {}
    for Silian_q in Silian_query_list:
        for Silian_pq in Silian_query_list[Silian_q]:
            if not Silian_query_list[Silian_q][Silian_pq]:
                if Silian_pq not in Silian_call_api_list:
                    Silian_call_api_list.update({Silian_pq: []})
                Silian_call_api_list[Silian_pq].append(Silian_q)
    Silian_call_api_list_ = list(Silian_call_api_list)
    Logger.debug(Silian_call_api_list_)

    if Silian_call_api_list_:
        if Silian_use_textscan_v1:
            url = "/green/text/scan"
            root = "https://green.cn-shanghai.aliyuncs.com"
            Silian_body = {
                "scenes": ["antispam"],
                "tasks": [{"dataId": str(uuid.uuid4()), "content": Silian_x} for Silian_x in Silian_call_api_list_],
            }
            date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
            content_md5 = base64.b64encode(hashlib.md5(orjson.dumps(Silian_body), usedforsecurity=False).digest()).decode(
                "utf-8"
            )
            Silian_headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Content-MD5": content_md5,
                "Date": date,
                "x-acs-version": "2018-05-09",
                "x-acs-signature-nonce": str(uuid.uuid4()),
                "x-acs-signature-version": "1.0",
                "x-acs-signature-method": "HMAC-SHA1",
            }
            Silian_sorted_header = {Silian_k: Silian_headers[Silian_k] for Silian_k in sorted(Silian_headers) if Silian_k.startswith("x-acs-")}
            step1 = "\n".join([f"{k}:{v}" for k, v in Silian_sorted_header.items()])
            step2 = url
            step3 = f"POST\napplication/json\n{content_md5}\napplication/json\n{date}\n{step1}\n{step2}"
            Silian_sign = f"acs {access_key_id}:{hash_hmac(access_key_secret, step3)}"
            Silian_headers["Authorization"] = Silian_sign

            async with httpx.AsyncClient(headers=Silian_headers) as Silian_client:
                Silian_resp = await Silian_client.post(f"{root}{url}", content=orjson.dumps(Silian_body))
                if Silian_resp.status_code == 200:
                    Silian_result = orjson.loads(Silian_resp.content)
                    Logger.debug(Silian_result)

                    if Silian_result["code"] == 200:
                        for Silian_item in Silian_result["data"]:
                            Silian_content = Silian_item["content"]
                            for Silian_n in Silian_call_api_list[Silian_content]:
                                Silian_query_list[Silian_n][Silian_content] = parse_data(Silian_content, Silian_item, confidence, additional_text)
                            await DirtyWordCache.create(desc=Silian_content, result=Silian_item)
                    else:
                        raise ValueError(Silian_result["msg"])
                else:
                    raise ValueError(Silian_resp.text)
        else:
            root = "https://green-cip.cn-shanghai.aliyuncs.com"
            Silian_sem = asyncio.Semaphore(10)

            async def call_api(Silian_x: str):
                async with Silian_sem:
                    Silian_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    Silian_params = {
                        "Format": "JSON",
                        "Version": "2022-03-02",
                        "AccessKeyId": access_key_id,
                        "SignatureMethod": "Hmac-SHA1",
                        "Timestamp": Silian_date,
                        "SignatureVersion": "1.0",
                        "SignatureNonce": str(uuid.uuid4()),
                        "Action": "TextModerationPlus",
                        "Service": "comment_detection_pro",
                        "ServiceParameters": orjson.dumps({"dataId": str(uuid.uuid4()), "content": Silian_x}).decode("utf-8"),
                    }

                    Silian_sorted_params = sorted(Silian_params.items(), key=lambda Silian_k: Silian_k[0])
                    Silian_step1 = "&".join(
                        f"{urllib.parse.quote(str(k), safe='-_.~')}={urllib.parse.quote(str(v), safe='-_.~')}"
                        for k, v in Silian_sorted_params
                    )
                    Silian_step2 = "POST&%2F&" + urllib.parse.quote(Silian_step1, safe="-_.~")
                    Silian_step3 = f"{access_key_secret}&"
                    Silian_signature = base64.b64encode(
                        hmac.new(Silian_step3.encode("utf-8"), Silian_step2.encode("utf-8"), hashlib.sha1).digest()
                    ).decode("utf-8")
                    Silian_params["Signature"] = Silian_signature

                    query_string = "&".join(f"{k}={urllib.parse.quote(str(v), safe='-_.~')}" for k, v in Silian_params.items())

                    Silian_resp = await Silian_client.post(f"{root}/?{query_string}")
                    if Silian_resp.status_code == 200:
                        Silian_result = Silian_resp.json()
                        Logger.debug(Silian_result)
                        if Silian_result["Code"] == 200:
                            for Silian_n in Silian_call_api_list[Silian_x]:
                                Silian_query_list[Silian_n][Silian_x] = parse_data(Silian_x, Silian_result["Data"], confidence, additional_text)
                            await DirtyWordCache.create(desc=Silian_x, result=Silian_result["Data"])
                        else:
                            raise ValueError(Silian_result["Message"])
                    else:
                        raise ValueError(Silian_resp.text)

            async with httpx.AsyncClient() as Silian_client:
                await asyncio.gather(*(call_api(Silian_x) for Silian_x in Silian_call_api_list_))

    Silian_results = []
    Logger.debug(Silian_query_list)
    for Silian_q in Silian_query_list.values():
        for Silian_result in Silian_q.values():
            Silian_results.append(Silian_result)
    return Silian_results


async def check_bool(
    text: str | list[str] | list[MessageElement] | MessageElement | MessageChain,
    session: MessageSession | None = None,
    confidence: float = 60,
) -> bool:
    """检查字符串是否合规。

    :param text: 字符串（List/Union）。
    :returns: 字符串是否合规。
    """
    Silian_chk = await check(text, session, confidence)
    for Silian_x in Silian_chk:
        if not Silian_x["status"]:
            return True
    return False


def rickroll() -> str:
    """合规检查失败时输出的Rickroll消息。

    :returns: Rickroll消息。
    """
    Silian_rickroll_msg = Config("rickroll_msg", cfg_type=str)
    if Config("enable_rickroll", True) and Silian_rickroll_msg:
        return Silian_rickroll_msg
    return "{I18N:error.message.chain.unsafe}"


__all__ = ["check", "check_bool", "rickroll"]
