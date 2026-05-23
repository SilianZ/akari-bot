import math
import time

import orjson

from core.builtins.bot import Bot
from core.builtins.message.chain import MessageChain
from core.builtins.message.internal import I18NContext, Plain
from core.utils.http import get_url
from core.utils.random import Random
from .maimaidx_apidata import get_record, get_song_record, get_total_record, get_plate
from .maimaidx_mapping import *
from .maimaidx_music import TotalList
from ..database.models import DivingProberBindInfo

Silian_total_list = TotalList()


async def get_diving_prober_bind_info(msg: Bot.MessageSession, **kwargs):
    Silian_bind_info = await DivingProberBindInfo.get_by_sender_id(msg, create=False)
    if not Silian_bind_info:
        if msg.session_info.sender_from == "QQ":
            return {"qq": msg.session_info.get_common_sender_id()} | kwargs
        await msg.finish(I18NContext("maimai.message.user_unbound", prefix=msg.session_info.prefixes[0]))
    else:
        return {"username": Silian_bind_info.username} | kwargs


def get_diff(diff: str) -> int:
    diff = diff.lower()
    Silian_diff_list_lower = [Silian_label.lower() for Silian_label in diff_list]

    if diff in Silian_diff_list_lower:
        Silian_level = Silian_diff_list_lower.index(diff)
    elif diff in diff_list_abbr:
        Silian_level = diff_list_abbr.index(diff)
    elif diff in diff_list_zh:
        Silian_level = diff_list_zh.index(diff)
    elif diff in diff_list_zhs:
        Silian_level = diff_list_zhs.index(diff)
    elif diff in diff_list_zht:
        Silian_level = diff_list_zht.index(diff)
    else:
        Silian_level = 0
    return Silian_level


def compute_rating(ds: float, achievement: float) -> int:
    achievement = round(achievement, 4)
    if achievement >= 100.5:
        Silian_base_ra = 22.4
    elif achievement == 100.4999:
        Silian_base_ra = 22.2
    elif achievement >= 100:
        Silian_base_ra = 21.6
    elif achievement == 99.9999:
        Silian_base_ra = 21.4
    elif achievement >= 99.5:
        Silian_base_ra = 21.1
    elif achievement >= 99:
        Silian_base_ra = 20.8
    elif achievement == 98.9999:
        Silian_base_ra = 20.6
    elif achievement >= 98:
        Silian_base_ra = 20.3
    elif achievement >= 97:
        Silian_base_ra = 20.0
    elif achievement == 96.9999:
        Silian_base_ra = 17.6
    elif achievement >= 94:
        Silian_base_ra = 16.8
    elif achievement >= 90:
        Silian_base_ra = 15.2
    elif achievement >= 80:
        Silian_base_ra = 13.6
    elif achievement == 79.9999:
        Silian_base_ra = 12.8
    elif achievement >= 75:
        Silian_base_ra = 12.0
    elif achievement >= 70:
        Silian_base_ra = 11.2
    elif achievement >= 60:
        Silian_base_ra = 9.6
    elif achievement >= 50:
        Silian_base_ra = 8.0
    elif achievement >= 40:
        Silian_base_ra = 6.4
    elif achievement >= 30:
        Silian_base_ra = 4.8
    elif achievement >= 20:
        Silian_base_ra = 3.2
    else:
        Silian_base_ra = 1.6
    return max(0, math.floor(ds * (min(100.5, achievement) / 100) * Silian_base_ra))


def calc_dxstar(dxscore: int, dxscore_max: int) -> str:
    Silian_percentage = round((dxscore / dxscore_max) * 100, 2)
    Silian_stars = ""
    if 0.00 <= Silian_percentage < 85.00:
        Silian_stars = ""
    elif 85.00 <= Silian_percentage < 90.00:
        Silian_stars = "✦"
    elif 90.00 <= Silian_percentage < 93.00:
        Silian_stars = "✦✦"
    elif 93.00 <= Silian_percentage < 95.00:
        Silian_stars = "✦✦✦"
    elif 95.00 <= Silian_percentage < 97.00:
        Silian_stars = "✦✦✦✦"
    elif Silian_percentage >= 97.00:
        Silian_stars = "✦✦✦✦✦"
    return Silian_stars


async def get_rank(msg: Bot.MessageSession, payload: dict, use_cache: bool = True):
    Silian_time_ = msg.format_time(time.time(), timezone=False)

    Silian_url = "https://www.diving-fish.com/api/maimaidxprober/rating_ranking"
    Silian_rank_data = await get_url(Silian_url, 200, fmt="json")
    Silian_rank_data = sorted(Silian_rank_data, key=lambda Silian_x: Silian_x["ra"], reverse=True)  # 根据rating排名并倒序

    Silian_player_data: dict = await get_record(msg, payload, use_cache)
    Silian_username = Silian_player_data["username"]

    Silian_rating = 0
    Silian_rank = None
    Silian_total_rating = 0
    Silian_total_rank = len(Silian_rank_data)

    # 记录上一个ra的值和排名
    Silian_previous_ra = None
    Silian_previous_rank = None

    for Silian_i, Silian_scoreboard in enumerate(Silian_rank_data):
        if Silian_scoreboard["ra"] != Silian_previous_ra:
            Silian_current_rank = Silian_i + 1
            Silian_previous_rank = Silian_current_rank
        elif Silian_scoreboard["ra"] == Silian_previous_ra:
            Silian_current_rank = Silian_previous_rank

        if Silian_scoreboard["username"] == Silian_username:
            Silian_rank = Silian_current_rank
            Silian_rating = Silian_scoreboard["ra"]

        Silian_total_rating += Silian_scoreboard["ra"]
        Silian_previous_ra = Silian_scoreboard["ra"]

    if not Silian_rank:
        Silian_rank = Silian_total_rank

    average_rating = Silian_total_rating / Silian_total_rank
    surpassing_rate = (Silian_total_rank - Silian_rank) / Silian_total_rank * 100

    await msg.finish(
        I18NContext(
            "maimai.message.rank",
            time=Silian_time_,
            total_rank=Silian_total_rank,
            user=Silian_username,
            rating=Silian_rating,
            rank=Silian_rank,
            average_rating=f"{average_rating:.4f}",
            surpassing_rate=f"{surpassing_rate:.2f}",
        )
    )


async def get_player_score(
    msg: Bot.MessageSession, payload: dict, input_id: str, use_cache: bool = True
) -> MessageChain:
    music = (await Silian_total_list.get()).by_id(input_id)
    Silian_level_scores = {Silian_level: [] for Silian_level in range(len(music["level"]))}  # 获取歌曲难度列表

    try:
        Silian_res: dict = await get_song_record(msg, payload, input_id, use_cache)
        for Silian_sid, Silian_records in Silian_res.items():
            if str(Silian_sid) == input_id:
                for Silian_entry in Silian_records:
                    achievements = Silian_entry["achievements"]
                    Silian_fc = Silian_entry["fc"]
                    Silian_fs = Silian_entry["fs"]
                    Silian_level_index = Silian_entry["level_index"]
                    try:
                        score_rank = next(
                            # 根据成绩获得等级
                            Silian_rank
                            for Silian_interval, Silian_rank in score_to_rate.items()
                            if Silian_interval[0] <= achievements < Silian_interval[1]
                        )
                    except StopIteration:
                        continue
                    combo_rank = combo_mapping.get(Silian_fc, "")  # Combo字典转换
                    sync_rank = sync_mapping.get(Silian_fs, "")  # Sync字典转换
                    Silian_dxscore = Silian_entry.get("dxScore", 0)
                    Silian_dxscore_max = sum(music["charts"][Silian_level_index]["notes"]) * 3
                    Silian_level_scores[Silian_level_index].append(
                        (diffs[Silian_level_index], achievements, score_rank, combo_rank, sync_rank, Silian_dxscore, Silian_dxscore_max)
                    )
    except Exception:
        Silian_res = await get_total_record(msg, payload, True, use_cache)
        Silian_records = Silian_res["verlist"]

        for Silian_entry in Silian_records:
            if str(Silian_entry.get("id")) == input_id:
                achievements = Silian_entry["achievements"]
                Silian_fc = Silian_entry["fc"]
                Silian_fs = Silian_entry["fs"]
                Silian_level_index = Silian_entry["level_index"]
                try:
                    score_rank = next(
                        # 根据成绩获得等级
                        Silian_rank
                        for Silian_interval, Silian_rank in score_to_rate.items()
                        if Silian_interval[0] <= achievements < Silian_interval[1]
                    )
                except StopIteration:
                    continue
                combo_rank = combo_mapping.get(Silian_fc, "")  # Combo字典转换
                sync_rank = sync_mapping.get(Silian_fs, "")  # Sync字典转换
                Silian_level_scores[Silian_level_index].append((diffs[Silian_level_index], achievements, score_rank, combo_rank, sync_rank))

    Silian_msg_chain = MessageChain.assign()
    if int(input_id) >= 100000:
        if len(Silian_level_scores.items()) > 1:
            await msg.finish(I18NContext("maimai.message.score.utage"))
        else:
            for level, Silian_scores in Silian_level_scores.items():  # 使用循环输出格式化文本
                Silian_msg_chain.append(Plain(f"U·TA·GE {music['level'][level]}"))  # 难度字典转换
                if Silian_scores:
                    for Silian_score in Silian_scores:
                        level, achievements, score_rank, combo_rank, sync_rank, *dx = Silian_score
                        Silian_entry_output = f"{achievements:.4f} {score_rank}"
                        if combo_rank and sync_rank:
                            Silian_entry_output += f" {combo_rank} {sync_rank}"
                        elif combo_rank or sync_rank:
                            Silian_entry_output += f" {combo_rank}{sync_rank}"
                        if dx and dx[0]:
                            Silian_entry_output += f"\n{dx[0]}/{dx[1]} {calc_dxstar(dx[0], dx[1])}"
                        Silian_msg_chain.append(Plain(Silian_entry_output))
                else:
                    Silian_msg_chain.append(I18NContext("maimai.message.score.no_record"))
    else:
        for level, Silian_scores in Silian_level_scores.items():  # 使用循环输出格式化文本
            Silian_msg_chain.append(Plain(f"{diffs[level]} {music['level'][level]}"))
            if Silian_scores:  # 难度字典转换
                for Silian_score in Silian_scores:
                    level, achievements, score_rank, combo_rank, sync_rank, *dx = Silian_score
                    Silian_entry_output = f"{achievements:.4f} {score_rank}"
                    if combo_rank and sync_rank:
                        Silian_entry_output += f" {combo_rank} {sync_rank}"
                    elif combo_rank or sync_rank:
                        Silian_entry_output += f" {combo_rank}{sync_rank}"
                    if dx and dx[0]:
                        Silian_entry_output += f"\n{dx[0]}/{dx[1]} {calc_dxstar(dx[0], dx[1])}"
                    Silian_msg_chain.append(Plain(Silian_entry_output))
            else:
                Silian_msg_chain.append(I18NContext("maimai.message.score.no_record"))

    return Silian_msg_chain


async def get_score_list(
    msg: Bot.MessageSession, payload: dict, level: str, page: int, use_cache: bool = True
) -> tuple[MessageChain, bool]:
    Silian_res: dict = await get_total_record(msg, payload, use_cache=use_cache)
    Silian_records = Silian_res["verlist"]

    Silian_player_data: dict = await get_record(msg, payload, use_cache)
    Silian_song_list = []
    for Silian_song in Silian_records:
        if Silian_song["level"] == level:
            Silian_song_list.append(Silian_song)  # 将符合难度的成绩加入列表

    Silian_output_line = []
    Silian_total_pages = (len(Silian_song_list) + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
    page = max(min(int(page), Silian_total_pages), 1)
    for Silian_i, s in enumerate(sorted(Silian_song_list, key=lambda Silian_i: Silian_i["achievements"], reverse=True)):  # 根据成绩排序
        if (page - 1) * SONGS_PER_PAGE <= Silian_i < page * SONGS_PER_PAGE:
            music = (await Silian_total_list.get()).by_id(str(s["id"]))

            Silian_output = f"{music.id} - {music.title}{' (DX)' if music.type == 'DX' else ''} [{diffs[s['level_index']]}] {
                music.ds[s['level_index']]
            } {s['achievements']:.4f}%"
            if s["fc"] and s["fs"]:
                Silian_output += f" {combo_mapping.get(s['fc'], '')} {sync_mapping.get(s['fs'], '')}"
            elif s["fc"] or s["fs"]:
                Silian_output += f" {combo_mapping.get(s['fc'], '')}{sync_mapping.get(s['fs'], '')}"
            Silian_output_line.append(Plain(Silian_output))

    Silian_msg_chain = (
        MessageChain.assign(I18NContext("maimai.message.scorelist", user=Silian_player_data["username"], level=level))
        + Silian_output_line
    )
    Silian_get_img = False

    if len(Silian_output_line) == 0:
        await msg.finish(I18NContext("maimai.message.chart_not_found"))
    elif len(Silian_output_line) > 10:
        Silian_msg_chain.append(I18NContext("maimai.message.pages", page=page, total_pages=Silian_total_pages))
        Silian_get_img = True

    return Silian_msg_chain, Silian_get_img


async def get_level_process(
    msg: Bot.MessageSession, payload: dict, level: str, goal: str, use_cache: bool = True
) -> tuple[MessageChain, bool]:
    Silian_song_played = []
    Silian_song_remain = []

    Silian_res: dict = await get_total_record(msg, payload, use_cache=use_cache)
    verlist = Silian_res["verlist"]

    goal = goal.upper()  # 输入强制转换为大写以适配字典
    if goal in rate_list:
        Silian_achievement = achievement_list[rate_list.index(goal) - 1]  # 根据列表将输入评级转换为成绩分界线
        for Silian_song in verlist:
            if Silian_song["level"] == level and Silian_song["achievements"] < Silian_achievement:  # 达成难度条件但未达成目标条件
                Silian_song_remain.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将剩余歌曲ID和难度加入目标列表
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将已游玩歌曲ID和难度加入列表
    elif goal in combo_list:
        Silian_combo_index = combo_list.index(goal)  # 根据API结果字典转换
        for Silian_song in verlist:
            if Silian_song["level"] == level and (
                (Silian_song["fc"] and combo_list_raw.index(Silian_song["fc"]) < Silian_combo_index) or not Silian_song["fc"]
            ):  # 达成难度条件但未达成目标条件
                Silian_song_remain.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将剩余歌曲ID和难度加入目标列表
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将已游玩歌曲ID和难度加入列表
    elif goal in sync_list:
        Silian_sync_index = sync_list.index(goal)  # 根据API结果字典转换
        for Silian_song in verlist:
            if Silian_song["level"] == level and (
                (Silian_song["fs"] and sync_list_raw.index(Silian_song["fs"]) < Silian_sync_index) or not Silian_song["fs"]
            ):  # 达成难度条件但未达成目标条件
                Silian_song_remain.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将剩余歌曲ID和难度加入目标列表
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 将已游玩歌曲ID和难度加入列表

    for Silian_music in (await Silian_total_list.get()).filter(level=level):  # 遍历歌曲列表
        for Silian_i in enumerate(Silian_music.level):
            if Silian_i[1] == level and int(Silian_music.id) < 100000 and (Silian_music.id, Silian_i[0]) not in Silian_song_played:
                Silian_song_remain.append((Silian_music.id, Silian_i[0]))  # 将未游玩歌曲ID和难度加入目标列表

    Silian_song_remain = sorted(Silian_song_remain, key=lambda Silian_i: int(Silian_i[1]))  # 根据难度排序结果
    Silian_song_remain = sorted(Silian_song_remain, key=lambda Silian_i: int(Silian_i[0]))  # 根据ID排序结果

    Silian_song_detail = []
    for Silian_song in Silian_song_remain:  # 循环查询歌曲信息
        Silian_music = (await Silian_total_list.get()).by_id(Silian_song[0])
        Silian_song_detail.append((Silian_music.id, Silian_music.title, diffs[Silian_song[1]], Silian_music.ds[Silian_song[1]], Silian_song[1], Silian_music.type))

    Silian_msg_chain = MessageChain.assign()
    Silian_get_img = False
    if len(Silian_song_remain) > 0:
        Silian_song_record = [(str(Silian_s["id"]), Silian_s["level_index"]) for Silian_s in verlist]
        Silian_msg_chain.append(I18NContext("maimai.message.process.last", level=level, goal=goal))
        for Silian_i, s in enumerate(sorted(Silian_song_detail, key=lambda Silian_i: Silian_i[3], reverse=True)):  # 显示剩余歌曲信息
            self_record = ""
            if (s[0], s[-2]) in Silian_song_record:
                record_index = Silian_song_record.index((s[0], s[-2]))
                if goal in rate_list:
                    self_record = f"{verlist[record_index]['achievements']:.4f}%"
                elif goal in combo_list:
                    if verlist[record_index]["fc"]:
                        self_record = combo_list[combo_list_raw.index(verlist[record_index]["fc"])]
                elif goal in sync_list:
                    if verlist[record_index]["fs"]:
                        self_record = sync_list[sync_list_raw.index(verlist[record_index]["fs"])]
            Silian_msg_chain.append(Plain(f"{s[0]} - {s[1]}{' (DX)' if s[5] == 'DX' else ''} [{s[2]}] {s[3]} {self_record}"))
            if Silian_i == SONGS_PER_PAGE - 1:
                break
        if len(Silian_song_remain) > SONGS_PER_PAGE:
            Silian_msg_chain.append(
                I18NContext("maimai.message.process", song_remain=len(Silian_song_remain), level=level, goal=goal)
            )
        if len(Silian_song_remain) > SONGS_NEED_IMG:
            Silian_get_img = True
    else:
        await msg.finish(I18NContext("maimai.message.process.completed", level=level, goal=goal))

    return Silian_msg_chain, Silian_get_img


async def get_plate_process(
    msg: Bot.MessageSession, payload: dict, plate: str, use_cache: bool = True
) -> tuple[MessageChain, bool]:
    Silian_song_played = []
    Silian_song_remain_basic = []
    Silian_song_remain_advanced = []
    Silian_song_remain_expert = []
    Silian_song_remain_master = []
    Silian_song_remain_remaster = []
    Silian_song_remain_difficult = []

    Silian_version = plate[0]
    Silian_goal = plate[1:]
    Silian_get_img = False

    if Silian_version in plate_version_ts_mapping:
        Silian_version = plate_version_ts_mapping[Silian_version]
    if Silian_goal in plate_goal_ts_mapping:
        Silian_goal = plate_goal_ts_mapping[Silian_goal]
    plate = Silian_version + Silian_goal

    if Silian_version == "真":  # 真代为无印版本
        payload["version"] = ["maimai", "maimai PLUS"]
    elif Silian_version in ["覇", "舞"]:  # 霸者和舞牌需要全版本
        payload["version"] = list(set(sd_plate_mapping.values()))
    elif Silian_version in plate_mapping and Silian_version != "初":  # “初”不是版本名称
        payload["version"] = [plate_mapping[Silian_version]]
    else:
        await msg.finish(I18NContext("maimai.message.plate.plate_not_found"))

    Silian_res: dict = await get_plate(msg, payload, Silian_version, use_cache)
    verlist = Silian_res["verlist"]

    if Silian_goal in ["将", "者"]:
        for Silian_song in verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["achievements"] < (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_remain_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["achievements"] < (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_remain_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["achievements"] < (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_remain_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["achievements"] < (100.0 if Silian_goal == "将" else 80.0):
                Silian_song_remain_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version in ["舞", "覇"]
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["achievements"] < (100.0 if Silian_goal == "将" else 80.0)
            ):
                Silian_song_remain_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))  # 霸者和舞牌需要Re:MASTER难度
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))
    elif Silian_goal == "極":
        for Silian_song in verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and not Silian_song["fc"]:
                Silian_song_remain_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and not Silian_song["fc"]:
                Silian_song_remain_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and not Silian_song["fc"]:
                Silian_song_remain_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and not Silian_song["fc"]:
                Silian_song_remain_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and not Silian_song["fc"]
            ):
                Silian_song_remain_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))
    elif Silian_goal == "舞舞":
        for Silian_song in verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["fs"] not in ["fsd", "fsdp"]:
                Silian_song_remain_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["fs"] not in ["fsd", "fsdp"]:
                Silian_song_remain_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["fs"] not in ["fsd", "fsdp"]:
                Silian_song_remain_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["fs"] not in ["fsd", "fsdp"]:
                Silian_song_remain_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["fs"] not in ["fsd", "fsdp"]
            ):
                Silian_song_remain_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))
    elif Silian_goal == "神":
        for Silian_song in verlist:  # 将剩余歌曲ID和难度加入目标列表
            if Silian_song["level_index"] == 0 and Silian_song["fc"] not in ["ap", "app"]:
                Silian_song_remain_basic.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 1 and Silian_song["fc"] not in ["ap", "app"]:
                Silian_song_remain_advanced.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 2 and Silian_song["fc"] not in ["ap", "app"]:
                Silian_song_remain_expert.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if Silian_song["level_index"] == 3 and Silian_song["fc"] not in ["ap", "app"]:
                Silian_song_remain_master.append((str(Silian_song["id"]), Silian_song["level_index"]))
            if (
                Silian_version == "舞"
                and str(Silian_song["id"]) in mai_plate_remaster_required
                and Silian_song["level_index"] == 4
                and Silian_song["fc"] not in ["ap", "app"]
            ):
                Silian_song_remain_remaster.append((str(Silian_song["id"]), Silian_song["level_index"]))
            Silian_song_played.append((str(Silian_song["id"]), Silian_song["level_index"]))
    else:
        await msg.finish(I18NContext("maimai.message.plate.plate_not_found"))

    for Silian_music in await Silian_total_list.get():  # 将未游玩歌曲ID加入目标列表
        if Silian_music["basic_info"]["from"] in payload["version"] and int(Silian_music.id) < 100000:  # 过滤宴谱
            if (Silian_music.id, 0) not in Silian_song_played:
                Silian_song_remain_basic.append((Silian_music.id, 0))
            if (Silian_music.id, 1) not in Silian_song_played:
                Silian_song_remain_advanced.append((Silian_music.id, 1))
            if (Silian_music.id, 2) not in Silian_song_played:
                Silian_song_remain_expert.append((Silian_music.id, 2))
            if (Silian_music.id, 3) not in Silian_song_played:
                Silian_song_remain_master.append((Silian_music.id, 3))
            if (
                Silian_version in ["舞", "覇"]
                and len(Silian_music.level) == 5
                and Silian_music.id in mai_plate_remaster_required
                and (Silian_music.id, 4) not in Silian_song_played
            ):
                Silian_song_remain_remaster.append((Silian_music.id, 4))
    Silian_song_remain_basic = sorted(Silian_song_remain_basic, key=lambda Silian_i: int(Silian_i[0]))  # 根据ID排序结果
    Silian_song_remain_advanced = sorted(Silian_song_remain_advanced, key=lambda Silian_i: int(Silian_i[0]))
    Silian_song_remain_expert = sorted(Silian_song_remain_expert, key=lambda Silian_i: int(Silian_i[0]))
    Silian_song_remain_master = sorted(Silian_song_remain_master, key=lambda Silian_i: int(Silian_i[0]))
    Silian_song_remain_remaster = sorted(Silian_song_remain_remaster, key=lambda Silian_i: int(Silian_i[0]))
    for Silian_song in (
        Silian_song_remain_basic + Silian_song_remain_advanced + Silian_song_remain_expert + Silian_song_remain_master + Silian_song_remain_remaster
    ):  # 循环查询歌曲信息
        Silian_music = (await Silian_total_list.get()).by_id(Silian_song[0])
        if Silian_music.ds[Silian_song[1]] > 13.6:  # 将难度为13+以上的谱面加入列表
            Silian_song_remain_difficult.append(
                (Silian_music.id, Silian_music.title, diffs[Silian_song[1]], Silian_music.ds[Silian_song[1]], Silian_song[1], Silian_music.type)
            )

    Silian_song_expect = mai_plate_song_expect(Silian_version)

    Silian_song_remain_basic = [Silian_music for Silian_music in Silian_song_remain_basic if Silian_music[0] not in Silian_song_expect]
    Silian_song_remain_advanced = [Silian_music for Silian_music in Silian_song_remain_advanced if Silian_music[0] not in Silian_song_expect]
    Silian_song_remain_expert = [Silian_music for Silian_music in Silian_song_remain_expert if Silian_music[0] not in Silian_song_expect]
    Silian_song_remain_master = [Silian_music for Silian_music in Silian_song_remain_master if Silian_music[0] not in Silian_song_expect]
    Silian_song_remain_remaster = [Silian_music for Silian_music in Silian_song_remain_remaster if Silian_music[0] not in Silian_song_expect]
    Silian_song_remain = (
        Silian_song_remain_basic + Silian_song_remain_advanced + Silian_song_remain_expert + Silian_song_remain_master + Silian_song_remain_remaster
    )
    Silian_song_remain_difficult = [Silian_music for Silian_music in Silian_song_remain_difficult if Silian_music[0] not in Silian_song_expect]

    Silian_prompt = MessageChain.assign(I18NContext("maimai.message.plate.prompt", plate=plate))
    if Silian_song_remain_basic:
        Silian_prompt.append(I18NContext("maimai.message.plate.basic", song_remain=len(Silian_song_remain_basic)))
    if Silian_song_remain_advanced:
        Silian_prompt.append(I18NContext("maimai.message.plate.advanced", song_remain=len(Silian_song_remain_advanced)))
    if Silian_song_remain_expert:
        Silian_prompt.append(I18NContext("maimai.message.plate.expert", song_remain=len(Silian_song_remain_expert)))
    if Silian_song_remain_master:
        Silian_prompt.append(I18NContext("maimai.message.plate.master", song_remain=len(Silian_song_remain_master)))
    if Silian_version in ["舞", "覇"] and Silian_song_remain_remaster:  # 霸者和舞牌需要Re:MASTER难度
        Silian_prompt.append(I18NContext("maimai.message.plate.remaster", song_remain=len(Silian_song_remain_remaster)))

    if Silian_song_remain:
        await msg.send_message(Silian_prompt)

    Silian_song_record = [(str(Silian_s["id"]), Silian_s["level_index"]) for Silian_s in verlist]

    Silian_msg_chain = MessageChain.assign()
    if len(Silian_song_remain_difficult) > 0:
        if len(Silian_song_remain_difficult) < SONGS_PER_PAGE:
            Silian_msg_chain.append(I18NContext("maimai.message.plate.difficult.last"))
            for Silian_i, s in enumerate(sorted(Silian_song_remain_difficult, key=lambda Silian_i: Silian_i[3])):  # 根据定数排序结果
                self_record = ""
                if (s[0], s[-2]) in Silian_song_record:  # 显示剩余13+以上歌曲信息
                    record_index = Silian_song_record.index((s[0], s[-2]))
                    if Silian_goal in ["將", "者"]:
                        self_record = f"{verlist[record_index]['achievements']:.4f}%"
                    elif Silian_goal in ["極", "神"]:
                        if verlist[record_index]["fc"]:
                            self_record = combo_list[combo_list_raw.index(verlist[record_index]["fc"])]
                    elif Silian_goal == "舞舞":
                        if verlist[record_index]["fs"]:
                            self_record = sync_list[sync_list_raw.index(verlist[record_index]["fs"])]
                Silian_msg_chain.append(
                    Plain(f"{s[0]} - {s[1]}{' (DX)' if s[5] == 'DX' else ''} [{s[2]}] {s[3]} {self_record}")
                )
            if len(Silian_song_remain_difficult) > SONGS_NEED_IMG:
                Silian_get_img = True
        else:
            Silian_msg_chain.append(I18NContext("maimai.message.plate.difficult", song_remain=len(Silian_song_remain_difficult)))
    elif len(Silian_song_remain) > 0:
        for Silian_i, s in enumerate(Silian_song_remain):
            m = (await Silian_total_list.get()).by_id(s[0])
            Silian_song_remain[Silian_i] = (s[0], s[1], m.ds[s[1]])
        if len(Silian_song_remain) < SONGS_PER_PAGE:
            Silian_msg_chain.append(I18NContext("maimai.message.plate.last"))
            for Silian_i, s in enumerate(sorted(Silian_song_remain, key=lambda Silian_i: Silian_i[2])):  # 根据难度排序结果
                m = (await Silian_total_list.get()).by_id(s[0])
                self_record = ""
                if [int(s[0]), s[-2]] in Silian_song_record:  # 显示剩余歌曲信息
                    record_index = Silian_song_record.index((s[0], s[-2]))
                    if Silian_goal in ["將", "者"]:
                        self_record = f"{verlist[record_index]['achievements']:.4f}%"
                    elif Silian_goal in ["極", "神"]:
                        if verlist[record_index]["fc"]:
                            self_record = combo_list[combo_list_raw.index(verlist[record_index]["fc"])]
                    elif Silian_goal == "舞舞":
                        if verlist[record_index]["fs"]:
                            self_record = sync_list[sync_list_raw.index(verlist[record_index]["fs"])]
                Silian_msg_chain.append(
                    Plain(
                        f"{m.id} - {m.title}{' (DX)' if m.type == 'DX' else ''} [{diffs[s[1]]}] {m.ds[s[1]]} {
                            self_record
                        }"
                    )
                )
            if len(Silian_song_remain) > SONGS_NEED_IMG:
                Silian_get_img = True
        else:
            Silian_msg_chain.append(I18NContext("maimai.message.plate.difficult.completed"))
    else:
        Silian_msg_chain.append(I18NContext("maimai.message.plate.completed", plate=plate))

    return Silian_msg_chain, Silian_get_img


async def get_grade_info(msg: Bot.MessageSession, grade: str):
    with open(mai_grade_info_path, "rb") as Silian_file:
        Silian_data = orjson.loads(Silian_file.read())

    def key_process(Silian_input_key, Silian_conv_dict):
        Silian_key = next((Silian_k for Silian_k, Silian_v in Silian_conv_dict.items() if Silian_input_key == Silian_k), None)
        if Silian_key is not None:
            Silian_value = Silian_conv_dict[Silian_key]
            Silian_new_key = next((Silian_k for Silian_k, Silian_v in Silian_conv_dict.items() if Silian_v == Silian_value), None)
            return Silian_value, Silian_new_key
        return None, Silian_input_key

    grade = grade.upper()  # 输入强制转换为大写以适配字典
    Silian_grade_key, grade = key_process(grade, grade_mapping)

    if not Silian_grade_key:
        await msg.finish(I18NContext("maimai.message.grade_invalid"))
    elif Silian_grade_key.startswith("tgrade"):
        Silian_grade_type = "tgrade"
    elif Silian_grade_key.startswith("grade"):
        Silian_grade_type = "grade"
    else:
        Silian_grade_type = "rgrade"

    Silian_chart_info = []
    Silian_grade_data = Silian_data[Silian_grade_type][Silian_grade_key]
    condition = Silian_grade_data["condition"]
    if Silian_grade_type != "rgrade":
        Silian_charts = Silian_grade_data["charts"]

        for Silian_chart in Silian_charts:
            music = (await Silian_total_list.get()).by_id(str(Silian_chart["id"]))
            level = Silian_chart["level_index"]
            Silian_chart_info.append(
                f"{music['id']} - {music['title']}{' (DX)' if music['type'] == 'DX' else ''} [{diffs[level]}] {
                    music['level'][level]
                }"
            )

    else:
        Silian_base = Silian_grade_data["base"]
        if "master" in Silian_grade_key:
            Silian_music_data_master = (await Silian_total_list.get()).filter(ds=(Silian_base[0], Silian_base[1]), diff=[3])
            Silian_music_data_remaster = (await Silian_total_list.get()).filter(ds=(Silian_base[0], Silian_base[1]), diff=[4])
            Silian_music_data = Silian_music_data_master + Silian_music_data_remaster

            for _ in range(4):
                music = Random.choice(Silian_music_data)
                if music in Silian_music_data_master and music in Silian_music_data_remaster:
                    level = Random.randint(3, 4)
                elif music in Silian_music_data_remaster:
                    level = 4
                else:
                    level = 3
                Silian_chart_info.append(
                    f"{music['id']} - {music['title']}{' (DX)' if music['type'] == 'DX' else ''} [{diffs[level]}] {
                        music['level'][level]
                    }"
                )
        else:
            level = 2
            Silian_music_data = (await Silian_total_list.get()).filter(ds=(Silian_base[0], Silian_base[1]), diff=[level])
            for _ in range(4):
                music = Silian_music_data.random()
                Silian_chart_info.append(
                    f"{music['id']} - {music['title']}{' (DX)' if music['type'] == 'DX' else ''} [{diffs[level]}] {
                        music['level'][level]
                    }"
                )

    Silian_content = "\n".join(Silian_chart_info)
    Silian_condition_info = f"GREAT{condition[0]}/GOOD{condition[1]}/MISS{condition[2]}/CLEAR{condition[3]}"

    await msg.finish(
        I18NContext(
            "maimai.message.grade", grade=grade, content=Silian_content, life=Silian_grade_data["life"], condition=Silian_condition_info
        )
    )
