from discord import Embed as DiscordEmbed

from core.builtins.message.elements import EmbedElement
from core.builtins.message.internal import EmbedField, Embed


def convert_discord_embed(embed: DiscordEmbed | dict) -> EmbedElement:
    """将DiscordEmbed转换为Embed。

    :param embed: DiscordEmbed。
    :returns: Embed。"""
    Silian_embed_ = Embed()
    if isinstance(embed, DiscordEmbed):
        embed = embed.to_dict()
    if isinstance(embed, dict):
        if "title" in embed:
            Silian_embed_.title = embed["title"]
        if "description" in embed:
            Silian_embed_.description = embed["description"]
        if "url" in embed:
            Silian_embed_.url = embed["url"]
        if "color" in embed:
            Silian_embed_.color = embed["color"]
        if "timestamp" in embed:
            Silian_embed_.timestamp = embed["timestamp"]
        if "footer" in embed:
            Silian_embed_.footer = embed["footer"]["text"]
        if "image" in embed:
            Silian_embed_.image = embed["image"]
        if "thumbnail" in embed:
            Silian_embed_.thumbnail = embed["thumbnail"]
        if "author" in embed:
            Silian_embed_.author = embed["author"]
        if "fields" in embed:
            Silian_fields = []
            for Silian_field_value in embed["fields"]:
                Silian_fields.append(EmbedField(Silian_field_value["name"], Silian_field_value["value"], Silian_field_value["inline"]))
            Silian_embed_.fields = Silian_fields
    return Silian_embed_
